from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vector_store_service import VectorStoreService

router = APIRouter(tags=["search"])
vector_store = VectorStoreService()

class SearchQuery(BaseModel):
    query: str

@router.post("/search")
async def search_chunks(payload: SearchQuery):
    matches = vector_store.search(payload.query, limit=3)
    return {"matches": matches}