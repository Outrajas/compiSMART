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

    # Create a new dataset for this ingestion batch
    dataset_id = str(uuid.uuid4())

    ingested = []

    async def process_urls(urls, platform):
        for url in urls:
            try:
                url_str = str(url)
                # 1. Metadata
                if platform == "youtube":
                    meta = metadata_service.youtube.get_metadata(url_str)
                else:
                    meta = metadata_service.instagram.get_metadata(url_str)

                # 2. Video ID
                video_id = generate_video_id(platform)

                # 3. Store metadata in SQLite (now with dataset_id)
                conn = get_connection()
                conn.execute("""
                    INSERT INTO videos 
                    (video_id, platform, title, creator, views, likes, comments, 
                     duration, upload_date, hashtags, follower_count, dataset_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_id, platform,
                    meta.get("title"), meta.get("creator"),
                    meta.get("views"), meta.get("likes"), meta.get("comments"),
                    meta.get("duration"), meta.get("upload_date"),
                    json.dumps(meta.get("hashtags", [])),
                    meta.get("follower_count"),
                    dataset_id
                ))
                conn.commit()
                conn.close()

                # 4. Transcript (only YouTube)
                chunk_count = 0
                if platform == "youtube":
                    result = transcript_service.extract_transcript(url_str, video_id=video_id)
                    segments = result.get("segments", [])
                    points = []
                    for i, seg in enumerate(segments):
                        emb = generate_embedding(seg["text"])
                        points.append(PointStruct(
                            id=str(uuid.uuid4()),
                            vector=emb,
                            payload={
                                "dataset_id": dataset_id,    # dataset isolation
                                "video_id": video_id,
                                "platform": platform,
                                "chunk_id": i,
                                "text": seg["text"],
                                "start_time": seg["start"],
                                "end_time": seg["end"],
                                "semantic_features": seg.get("semantic_features", {}),
                            }
                        
                        ))
                    if points:
                        vector_store.client.upsert(
                            collection_name=vector_store.COLLECTION_NAME,
                            points=points
                        )
                        chunk_count = len(points)

                ingested.append({
                    "video_id": video_id,
                    "platform": platform,
                    "url": url_str,
                    "metadata": meta,
                    "chunk_count": chunk_count
                })
                logger.info(f"Ingested {platform} video {video_id} into dataset {dataset_id}")

            except Exception as e:
                logger.error(f"Failed to ingest {url}: {e}")
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