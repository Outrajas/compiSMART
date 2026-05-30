from fastapi import APIRouter, Query, HTTPException
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

@router.get("/analytics/top")
async def top_video(dataset_id: str = Query(...)):
    video = get_top_performing_video(dataset_id)
    return video or {"message": "No videos found"}

@router.get("/analytics/average-engagement")
async def average_engagement(dataset_id: str = Query(...)):
    avg = get_average_engagement(dataset_id)
    return {"dataset_id": dataset_id, "average_engagement": avg}

@router.get("/analytics/ranked")
async def ranked_videos(dataset_id: str = Query(...)):
    return rank_videos_by_engagement(dataset_id)

@router.get("/analytics/summary")
async def summary(dataset_id: str = Query(...)):
    return get_platform_summary_for_dataset(dataset_id)

@router.get("/analytics/rankings")
async def rankings(dataset_id: str = Query(...)):
    return get_detailed_rankings_for_dataset(dataset_id)
@router.get("/analytics/semantic-profiles")
async def semantic_profiles(dataset_id: str = Query(...)):
    return get_semantic_profiles_for_dataset(dataset_id)

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