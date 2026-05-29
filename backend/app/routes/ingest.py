import json
from fastapi import APIRouter, HTTPException
from app.models.video import VideoInput
from app.services.metadata_service import MetadataService
from app.services.transcript_service import TranscriptService
from app.services.embedding_service import chunk_transcript
from app.services.vector_store_service import VectorStoreService
from app.db.sqlite import get_connection
from app.core.logger import logger

router = APIRouter(tags=["ingest"])
metadata_service = MetadataService()
transcript_service = TranscriptService()
vector_store = VectorStoreService()

@router.post("/ingest")
async def ingest_videos(payload: VideoInput):
    logger.info(f"Ingest request: {payload}")
    try:
        # 1. Metadata
        metadata = metadata_service.collect_all(
            youtube_url=str(payload.youtube_url),
            instagram_url=str(payload.instagram_url)
        )

        # 2. Save metadata to SQLite
        conn = get_connection()
        # YouTube (video_id = "A")
        yt = metadata["youtube"]
        if yt.get("title"):   # ensure we have something
            conn.execute("""
                INSERT OR REPLACE INTO videos 
                (video_id, platform, title, creator, views, likes, comments, duration, upload_date, hashtags, follower_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "A",
                "youtube",
                yt.get("title"),
                yt.get("creator"),
                yt.get("views"),
                yt.get("likes"),
                yt.get("comments"),
                yt.get("duration"),
                yt.get("upload_date"),
                json.dumps(yt.get("hashtags", [])),
                yt.get("follower_count"),
            ))

        # Instagram (stub – video_id = "B")
        insta = metadata["instagram"]
        if insta.get("platform"):   # stub always has platform
            conn.execute("""
                INSERT OR REPLACE INTO videos 
                (video_id, platform, title, creator, views, likes, comments, duration, upload_date, hashtags, follower_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "B",
                "instagram",
                insta.get("title"),
                insta.get("creator"),
                insta.get("views"),
                insta.get("likes"),
                insta.get("comments"),
                insta.get("duration"),
                insta.get("upload_date"),
                json.dumps(insta.get("hashtags", [])),
                insta.get("follower_count"),
            ))
        conn.commit()
        conn.close()

        # 3. Transcript for YouTube (ID "A")
        youtube_url = str(payload.youtube_url)
        result = transcript_service.extract_transcript(youtube_url, video_id="A")
        transcript_text = result["transcript"]

        # 4. Chunk transcript
        chunks = chunk_transcript(transcript_text)
        chunk_count = len(chunks)
        preview = transcript_text[:500]

        # 5. Store chunks in Qdrant
        vector_store.store_chunks(chunks, video_id="A", platform="youtube")

        return {
            "youtube": metadata["youtube"],
            "instagram": metadata["instagram"],
            "transcript_preview": preview,
            "chunk_count": chunk_count,
            "status": "stored"
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))