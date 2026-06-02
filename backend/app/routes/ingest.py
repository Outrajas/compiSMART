import json
import uuid
from fastapi import APIRouter, HTTPException
from app.models.video import VideoInput
from app.models.chat import ChatRequest
from app.services.metadata_service import MetadataService
from app.services.transcript_service import TranscriptService
from app.services.embedding_service import generate_embedding
from app.services.vector_store_service import VectorStoreService
from app.services.video_id_service import generate_video_id
from app.db.sqlite import get_connection, add_video_to_dataset
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

    async def process_urls(urls, requested_platform):
        for url in urls:
            try:
                url_str = str(url)
                
                if "instagram.com" in url_str.lower():
                    actual_platform = "instagram"
                elif "youtube.com" in url_str.lower() or "youtu.be" in url_str.lower():
                    actual_platform = "youtube"
                else:
                    actual_platform = requested_platform

                conn = get_connection()
                if actual_platform == "youtube":
                    clean_url = url_str.split('&')[0] if 'watch?v=' in url_str else url_str
                    cached_row = conn.execute("SELECT * FROM videos WHERE youtube_id = ? OR title = ?", (clean_url, url_str)).fetchone()
                else:
                    cached_row = conn.execute("SELECT * FROM videos WHERE title = ? OR bio = ?", (url_str, url_str)).fetchone()
                
                if cached_row:
                    logger.info(f"CACHE HIT: Reusing stored assets for {url_str}. Bypassing processing chains.")
                    video_id = cached_row["video_id"]
                    conn.close()
                    
                    add_video_to_dataset(dataset_id, video_id)
                    
                    ingested.append({
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
                    })
                    continue
                conn.close()
                
                if actual_platform == "youtube":
                    meta = metadata_service.youtube.get_metadata(url_str)
                else:
                    meta = metadata_service.instagram.get_metadata(url_str)

                views = meta.get("views") or 0
                likes = meta.get("likes") or 0
                comments = meta.get("comments") or 0
                
                if views > 0:
                    meta["engagement_rate"] = round((likes + comments) / views * 100, 4)
                else:
                    meta["engagement_rate"] = 0.0

                video_id = generate_video_id(actual_platform)

                hook_text = ""
                segments = []
                transcript_text = ""
                
                if actual_platform == "youtube":
                    result = transcript_service.extract_transcript(url_str, video_id=video_id)
                    segments = result.get("segments", [])
                    transcript_text = result.get("transcript", "")
                    
                    # FIX: Tighten the hook text strictly to the first 15 chronological seconds
                    hook_texts_list = [seg["text"] for seg in segments if seg.get("start", 0) <= 15.0]
                    hook_text = " ".join(hook_texts_list).strip()
                else:
                    base_text = meta.get("native_transcript") or meta.get("caption") or meta.get("title") or ""
                    transcript_text = base_text
                    
                    # Instagram short-form uses first 300 characters as the strict intro hook boundary
                    hook_text = base_text[:300].strip()
                    features = transcript_service._compute_semantic_features(base_text, segment_index=0, total_segments=1)
                    segments = [{
                        "start": 0.0,
                        "end": float(meta.get("duration") or 15.0),
                        "text": base_text if base_text else "[No description text available]",
                        "semantic_features": features
                    }]

                global_stats = transcript_service.compute_global_transcript_stats(transcript_text)

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

                chunk_count = 0
                if segments:
                    points = []
                    for i, seg in enumerate(segments):
                        emb = generate_embedding(seg["text"])
                        payload_data = {
                            "dataset_id": dataset_id,
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
                        vector_store.client.upsert(
                            collection_name=vector_store.COLLECTION_NAME,
                            points=points
                        )
                        chunk_count = len(points)
                        logger.info(f"Stored {chunk_count} semantic segments into vector DB for {video_id}")

                ingested.append({
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
                })

            except Exception as e:
                logger.error(f"Ingestion worker step error on URL {url}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed on {url}: {str(e)}")

    if payload.youtube_urls:
        await process_urls(payload.youtube_urls, "youtube")
    if payload.instagram_urls:
        await process_urls(payload.instagram_urls, "instagram")

    return {
        "dataset_id": dataset_id,
        "ingested": ingested,
        "status": "completed"
    }