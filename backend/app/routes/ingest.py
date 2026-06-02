import json
import uuid
import time
import asyncio
from fastapi import APIRouter, HTTPException
from app.models.video import VideoInput
from app.services.metadata_service import MetadataService
from app.services.transcript_service import TranscriptService
from app.services.embedding_service import generate_embeddings_batch
from app.services.vector_store_service import VectorStoreService
from app.services.video_id_service import generate_video_id
from app.db.sqlite import get_connection, add_video_to_dataset, set_video_semantic_cache
from app.core.logger import logger
from qdrant_client.models import PointStruct

router = APIRouter(tags=["ingest"])
metadata_service = MetadataService()
transcript_service = TranscriptService()
vector_store = VectorStoreService()

@router.post("/ingest")
async def ingest_videos(payload: VideoInput):
    if not payload.youtube_urls and not payload.instagram_urls:
        raise HTTPException(status_code=422, detail="At least one URL required")

    dataset_id = str(uuid.uuid4())
    
    conn = get_connection()
    conn.execute("INSERT INTO datasets (dataset_id) VALUES (?)", (dataset_id,))
    conn.commit()
    conn.close()
    
    ingested = []

    async def process_single_url(raw_url, requested_platform: str):
        url_str = str(raw_url) # FIX: Cast HttpUrl to str to prevent attribute errors
        t_start = time.time()
        
        if "instagram.com" in url_str.lower():
            actual_platform = "instagram"
        elif "youtube.com" in url_str.lower() or "youtu.be" in url_str.lower():
            actual_platform = "youtube"
        else:
            actual_platform = requested_platform

        # --- INSTANT CACHE BYPASS ---
        conn = get_connection()
        if actual_platform == "youtube":
            clean_url = url_str.split('&')[0] if 'watch?v=' in url_str else url_str
            cached_row = conn.execute("SELECT * FROM videos WHERE youtube_id = ? OR title = ?", (clean_url, url_str)).fetchone()
        else:
            cached_row = conn.execute("SELECT * FROM videos WHERE title = ? OR bio = ?", (url_str, url_str)).fetchone()
        
        if cached_row:
            t_cache = time.time()
            logger.info(f"CACHE HIT: Bypassing chains for {url_str}.")
            video_id = cached_row["video_id"]
            conn.close()
            
            add_video_to_dataset(dataset_id, video_id)
            
            res = {
                "video_id": video_id,
                "platform": actual_platform,
                "url": url_str,
                "title": cached_row["title"],
                "creator": cached_row["creator"],
                "views": cached_row["views"],
                "likes": cached_row["likes"],
                "comments": cached_row["comments"],
                "duration": cached_row["duration"],
                "follower_count": cached_row["follower_count"],
                "engagement_rate": cached_row["engagement_rate"],
                "hashtags": json.loads(cached_row["hashtags"]) if cached_row["hashtags"] else [],
                "chunk_count": 0
            }
            logger.info(f"PERFORMANCE: URL {url_str} | Cache Loaded: {t_cache-t_start:.2f}s")
            return res

        conn.close()

        # --- COLD EXTRACTION TRACK ---
        t_ext_start = time.time()
        
        def get_meta():
            if actual_platform == "youtube":
                return metadata_service.youtube.get_metadata(url_str)
            return metadata_service.instagram.get_metadata(url_str)
            
        def get_trans():
            video_id_tmp = generate_video_id(actual_platform)
            if actual_platform == "youtube":
                res = transcript_service.extract_transcript(url_str, video_id=video_id_tmp)
                segments = res.get("segments", [])
                transcript_text = res.get("transcript", "")
                hook_texts_list = [seg["text"] for seg in segments if seg.get("start", 0) <= 15.0]
                hook_text = " ".join(hook_texts_list).strip()
            else:
                base_text = ""
                transcript_text = ""
                hook_text = ""
                segments = []
            return video_id_tmp, segments, transcript_text, hook_text

        meta_task = asyncio.to_thread(get_meta)
        trans_task = asyncio.to_thread(get_trans)

        meta, (video_id, segments, transcript_text, hook_text) = await asyncio.gather(meta_task, trans_task)
        
        if actual_platform == "instagram":
            base_text = meta.get("native_transcript") or meta.get("caption") or meta.get("title") or ""
            transcript_text = base_text
            hook_text = base_text[:300].strip()
            features = transcript_service._compute_semantic_features(base_text, segment_index=0, total_segments=1)
            segments = [{
                "start": 0.0,
                "end": float(meta.get("duration") or 15.0),
                "text": base_text if base_text else "[No description text available]",
                "semantic_features": features
            }]

        views = meta.get("views") or 0
        likes = meta.get("likes") or 0
        comments = meta.get("comments") or 0
        
        if views > 0:
            meta["engagement_rate"] = round((likes + comments) / views * 100, 4)
        else:
            meta["engagement_rate"] = 0.0

        global_stats = transcript_service.compute_global_transcript_stats(transcript_text)
        
        # PRE-COMPUTE AND SAVE SEMANTIC PROFILE
        total_segs = len(segments)
        avg = lambda key: round(sum(s.get("semantic_features", {}).get(key, 0) for s in segments) / total_segs, 1) if total_segs else 0.0
        avg_bool = lambda key: round(sum(1 for s in segments if s.get("semantic_features", {}).get(key)) / total_segs * 100, 1) if total_segs else 0.0
        
        opening = [s for s in segments if s.get("start", 0) <= 15]
        hook_score = max((s.get("semantic_features", {}).get("hook_score", 0) for s in opening), default=0)
        if not opening and segments:
            hook_score = max((s.get("semantic_features", {}).get("hook_score", 0) for s in segments))

        duration = meta.get("duration") or 0
        last_end = max(s.get("end", 0) for s in segments) if segments else 0
        coverage = round((last_end / duration) * 100, 1) if duration else 0

        semantic_profile = {
            "hook_score": round(hook_score, 1),
            "avg_humor": avg("humor_score"),
            "avg_curiosity": avg("curiosity_score"),
            "avg_emotion": avg("emotion"),
            "avg_conflict": avg_bool("conflict"),
            "avg_question": avg_bool("question"),
            "avg_cta": avg("cta_score"),
            "transcript_coverage": coverage,
            "total_segments": total_segs,
            "hook_breakdown": {
                "question": avg_bool("question"),
                "conflict": avg_bool("conflict"),
                "emotion": avg("emotion"),
                "humor": avg("humor_score"),
                "curiosity": avg("curiosity_score"),
                "cta": avg("cta_score")
            }
        }
        set_video_semantic_cache(video_id, json.dumps(semantic_profile))
        t_ext_end = time.time()

        # --- DB INSERTION ---
        t_db_start = time.time()
        conn = get_connection()
        conn.execute("""
            INSERT INTO videos 
            (video_id, youtube_id, platform, title, creator, views, likes, comments, 
             duration, upload_date, hashtags, follower_count, dataset_id, hook_text, engagement_rate, transcript,
             question_count, emotion_words, conflict_score, humor_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id, url_str if actual_platform == "youtube" else None, actual_platform,
            meta.get("title"), meta.get("creator"),
            meta.get("views"), meta.get("likes"), meta.get("comments"),
            meta.get("duration"), meta.get("upload_date"),
            json.dumps(meta.get("hashtags", [])),
            meta.get("follower_count", 0),
            dataset_id,
            hook_text,
            meta["engagement_rate"],
            transcript_text,
            global_stats["question_count"],
            global_stats["emotion_words"],
            global_stats["conflict_score"],
            global_stats["humor_score"]
        ))
        conn.commit()
        conn.close()

        add_video_to_dataset(dataset_id, video_id)
        t_db_end = time.time()

        # --- PARALLEL BATCH EMBEDDING ---
        t_emb_start = time.time()
        chunk_count = 0
        if segments:
            texts = [seg["text"] for seg in segments]
            embeddings = await asyncio.to_thread(generate_embeddings_batch, texts)
            
            points = []
            for i, (seg, emb) in enumerate(zip(segments, embeddings)):
                payload_data = {
                    "video_id": video_id,
                    "platform": actual_platform,
                    "chunk_id": i,
                    "text": seg["text"],
                    "start_time": seg["start"],
                    "end_time": seg["end"],
                    "semantic_features": seg.get("semantic_features", {})
                }
                if meta.get("title"):
                    payload_data["title"] = meta["title"]
                    
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb,
                    payload=payload_data
                ))
            
            if points:
                await asyncio.to_thread(vector_store.client.upsert, collection_name=vector_store.COLLECTION_NAME, points=points)
                chunk_count = len(points)
        t_emb_end = time.time()

        t_end = time.time()
        logger.info(f"PERFORMANCE: URL {url_str} | Meta+Trans: {t_ext_end-t_ext_start:.2f}s | DB: {t_db_end-t_db_start:.2f}s | Embedding+Qdrant: {t_emb_end-t_emb_start:.2f}s | Total: {t_end-t_start:.2f}s")

        return {
            "video_id": video_id,
            "platform": actual_platform,
            "url": url_str,
            "title": meta.get("title"),
            "creator": meta.get("creator"),
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration": meta.get("duration"),
            "follower_count": meta.get("follower_count", 0),
            "engagement_rate": meta["engagement_rate"],
            "hashtags": meta.get("hashtags", []),
            "chunk_count": chunk_count
        }

    tasks = []
    if payload.youtube_urls:
        tasks.extend([process_single_url(u, "youtube") for u in payload.youtube_urls])
    if payload.instagram_urls:
        tasks.extend([process_single_url(u, "instagram") for u in payload.instagram_urls])
        
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for res in results:
        if isinstance(res, Exception):
            logger.error(f"Ingest parallel error: {res}")
        else:
            ingested.append(res)

    return {
        "dataset_id": dataset_id,
        "ingested": ingested,
        "status": "completed"
    }