import json
import uuid
from fastapi import APIRouter, HTTPException
from app.models.video import VideoInput
from app.services.metadata_service import MetadataService
from app.services.transcript_service import TranscriptService
from app.services.embedding_service import generate_embedding
from app.services.vector_store_service import VectorStoreService
from app.services.video_id_service import generate_video_id
from app.db.sqlite import get_connection
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
    ingested = []

    async def process_urls(urls, platform):
        for url in urls:
            try:
                url_str = str(url)
                
                # 1. Collect Metadata Unified Engine (100% Real Stats)
                if platform == "youtube":
                    meta = metadata_service.youtube.get_metadata(url_str)
                else:
                    meta = metadata_service.instagram.get_metadata(url_str)

                views = meta.get("views") or 0
                likes = meta.get("likes") or 0
                comments = meta.get("comments") or 0
                
                # 2. Strict Cross-Platform Metrics Normalization Formula
                if views > 0:
                    meta["engagement_rate"] = round((likes + comments) / views * 100, 4)
                else:
                    meta["engagement_rate"] = 0.0

                video_id = generate_video_id(platform)

                # 3. Extract Hook Block (No Whisper)
                base_text = meta.get("native_transcript") or meta.get("caption") or meta.get("title") or ""
                hook_text = base_text[:300].strip()
                
                if platform == "youtube":
                    result = transcript_service.extract_transcript(url_str, video_id=video_id)
                    segments = result.get("segments", [])
                    hook_texts_list = [seg["text"] for seg in segments if seg.get("start", 0) <= 60.0]
                    hook_text = " ".join(hook_texts_list).strip()
                else:
                    features = transcript_service._compute_semantic_features(base_text, segment_index=0, total_segments=1)
                    segments = [{
                        "start": 0.0,
                        "end": float(meta.get("duration") or 15.0),
                        "text": base_text if base_text else "[No description text available]",
                        "semantic_features": features
                    }]

                # 4. Save clean data directly to SQLite Engine
                conn = get_connection()
                conn.execute("""
                    INSERT INTO videos 
                    (video_id, platform, title, creator, views, likes, comments, 
                     duration, upload_date, hashtags, follower_count, following_count, 
                     posts_count, bio, dataset_id, hook_text, engagement_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_id, platform,
                    meta.get("title"), meta.get("creator"),
                    meta.get("views"), meta.get("likes"), meta.get("comments"),
                    meta.get("duration"), meta.get("upload_date"),
                    json.dumps(meta.get("hashtags", [])),
                    meta.get("follower_count", 0),
                    meta.get("following_count", 0),
                    meta.get("posts_count", 0),
                    meta.get("bio", ""),
                    dataset_id,
                    hook_text,
                    meta["engagement_rate"]
                ))
                conn.commit()
                conn.close()

                # 5. Build Qdrant Point Payload Data
                chunk_count = 0
                if segments:
                    points = []
                    for i, seg in enumerate(segments):
                        emb = generate_embedding(seg["text"])
                        payload_data = {
                            "dataset_id": dataset_id,
                            "video_id": video_id,
                            "platform": platform,
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

                # Populate the response meta fields cleanly to prevent front-end zero values
                ingested.append({
                    "video_id": video_id,
                    "platform": platform,
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