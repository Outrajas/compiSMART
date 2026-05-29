import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.services.embedding_service import generate_embedding
from app.core.logger import logger

COLLECTION_NAME = "video_chunks"
VECTOR_SIZE = 384

class VectorStoreService:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            logger.info(f"Creating Qdrant collection '{COLLECTION_NAME}'")
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists")

    def store_chunks(self, chunks: list[dict], video_id: str, platform: str = "youtube"):
        points = []
        for chunk in chunks:
            embedding = generate_embedding(chunk["text"])
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "video_id": video_id,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "platform": platform,
                },
            )
            points.append(point)

        if points:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
            )
            logger.info(f"Stored {len(points)} chunks for video {video_id}")

    def search(self, query: str, limit: int = 3) -> list[dict]:
        query_vector = generate_embedding(query)
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
        )
        matches = []
        for hit in results.points:
            matches.append(hit.payload)
        return matches