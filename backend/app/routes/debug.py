from fastapi import APIRouter, Query
from app.services.vector_store_service import VectorStoreService

router = APIRouter(tags=["debug"])

@router.get("/debug/check-chunks")
async def check_chunks(dataset_id: str, video_id: str = None):
    """Return first 5 chunks from Qdrant for a dataset, optionally filtered by video_id."""
    vs = VectorStoreService()
    if video_id:
        chunks = vs.search_with_filter(
            query="",
            limit=5,
            dataset_id=dataset_id,
            video_ids=[video_id]
        )
    else:
        chunks = vs.search_with_filter(query="", limit=5, dataset_id=dataset_id)
    # Return only essential fields for readability
    result = []
    for c in chunks:
        result.append({
            "video_id": c.get("video_id"),
            "start_time": c.get("start_time"),
            "end_time": c.get("end_time"),
            "text_preview": c.get("text", "")[:200],
            "has_semantic": bool(c.get("semantic_features"))
        })
    return {"chunk_count": len(chunks), "chunks": result}