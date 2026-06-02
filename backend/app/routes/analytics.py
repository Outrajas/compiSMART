from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List
from app.db.sqlite import add_video_to_dataset, remove_video_from_dataset, get_dataset_video_ids
from app.services.analytics_service import (
    get_top_performing_video,
    get_average_engagement,
    rank_videos_by_engagement,
    get_platform_summary_for_dataset,
    get_detailed_rankings_for_dataset,
    compare_videos_in_dataset,
    get_semantic_profiles_for_dataset
)

router = APIRouter(tags=["analytics"])

class DatasetMutation(BaseModel):
    dataset_id: str
    video_id: str

def parse_video_ids(video_ids_str: str | None) -> list[str] | None:
    if video_ids_str:
        return [vid.strip() for vid in video_ids_str.split(",") if vid.strip()]
    return None

@router.post("/analytics/dataset/add")
async def add_video_link(payload: DatasetMutation):
    try:
        add_video_to_dataset(payload.dataset_id, payload.video_id)
        return {"status": "success", "message": "Video attached to active session mapping successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/dataset/remove")
async def remove_video_link(payload: DatasetMutation):
    try:
        remove_video_from_dataset(payload.dataset_id, payload.video_id)
        return {"status": "success", "message": "Video isolated from active session parameters successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/top")
async def top_video(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    video = get_top_performing_video(dataset_id, vids)
    return video or {"message": "No videos found"}

@router.get("/analytics/average-engagement")
async def average_engagement(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    avg = get_average_engagement(dataset_id, vids)
    return {"dataset_id": dataset_id, "average_engagement": avg}

@router.get("/analytics/ranked")
async def ranked_videos(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    return rank_videos_by_engagement(dataset_id, vids)

@router.get("/analytics/summary")
async def summary(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    return get_platform_summary_for_dataset(dataset_id, vids)

@router.get("/analytics/rankings")
async def rankings(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    return get_detailed_rankings_for_dataset(dataset_id, vids)

@router.get("/analytics/semantic-profiles")
async def semantic_profiles(dataset_id: str = Query(...), video_ids: str = Query(None)):
    vids = parse_video_ids(video_ids)
    return get_semantic_profiles_for_dataset(dataset_id, vids)

@router.get("/analytics/comparison")
async def comparison(
    dataset_id: str = Query(...),
    video_id_a: str = Query(...),
    video_id_b: str = Query(...)
):
    result = compare_videos_in_dataset(dataset_id, video_id_a, video_id_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result