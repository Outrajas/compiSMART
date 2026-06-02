import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny, MatchValue, Range
from app.services.embedding_service import generate_embedding
from app.core.logger import logger

class VectorStoreService:
    COLLECTION_NAME = "video_chunks"
    VECTOR_SIZE = 384

    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION_NAME not in collections:
            logger.info(f"Creating Qdrant collection '{self.COLLECTION_NAME}'")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info(f"Collection '{self.COLLECTION_NAME}' already exists")

    def search_with_filter(
        self,
        query: str,
        limit: int = 3,
        video_ids: list[str] | None = None,
        platform: str | None = None,
        time_max: float | None = None
    ) -> list[dict]:
        query_vector = generate_embedding(query)

        must_conditions = []
        if video_ids:
            must_conditions.append(FieldCondition(
                key="video_id",
                match=MatchAny(any=video_ids)
            ))
        if platform:
            must_conditions.append(FieldCondition(
                key="platform",
                match=MatchAny(any=[platform])
            ))
        if time_max is not None:
            must_conditions.append(FieldCondition(
                key="start_time",
                range=Range(lte=time_max)
            ))

        if must_conditions:
            query_filter = Filter(must=must_conditions)
        else:
            query_filter = None

        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        matches = []
        for hit in results.points:
            matches.append(hit.payload)
        return matches

    def search(self, query: str, limit: int = 3) -> list[dict]:
        return self.search_with_filter(query, limit)