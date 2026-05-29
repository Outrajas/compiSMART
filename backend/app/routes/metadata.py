import json
from fastapi import APIRouter, HTTPException
from app.db.sqlite import get_connection

router = APIRouter(tags=["metadata"])

def compute_engagement(views, likes, comments):
    if views and views > 0:
        return round((likes + comments) / views * 100, 4)
    return None

@router.get("/video/{video_id}")
async def get_video_metadata(video_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    data = dict(row)
    # Parse hashtags JSON string back to list
    if data.get("hashtags"):
        data["hashtags"] = json.loads(data["hashtags"])
    else:
        data["hashtags"] = []

    # Add engagement rate
    data["engagement_rate"] = compute_engagement(
        data.get("views"), data.get("likes"), data.get("comments")
    )
    return data