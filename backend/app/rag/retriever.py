from app.services.vector_store_service import VectorStoreService
from app.db.sqlite import get_connection
import json

vector_store = VectorStoreService()

def retrieve_metadata(video_id: str) -> dict:
    """Fetch structured metadata from SQLite for a given video."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,)).fetchone()
    conn.close()
    if not row:
        return {}
    data = dict(row)
    if data.get("hashtags"):
        data["hashtags"] = json.loads(data["hashtags"])
    # Compute engagement rate
    views = data.get("views", 0) or 0
    likes = data.get("likes", 0) or 0
    comments = data.get("comments", 0) or 0
    data["engagement_rate"] = round((likes + comments) / views * 100, 4) if views else None
    return data

def retrieve_chunks(query: str, limit: int = 3) -> list[dict]:
    """Retrieve transcript chunks from Qdrant."""
    return vector_store.search(query, limit=limit)

def classify_question(question: str) -> str:
    """
    Simple keyword router.
    Returns: "metadata", "content", or "both"
    """
    q = question.lower()
    meta_keywords = ["creator", "engagement rate", "views", "likes", "comments",
                     "followers", "upload date", "follower count", "who is the creator",
                     "engagement", "video a", "video b"]
    content_keywords = ["hook", "transcript", "song", "lyric", "content", "compare the hook",
                        "first 5 seconds", "why did", "outperform", "improve", "suggestion"]

    meta_hit = any(k in q for k in meta_keywords)
    content_hit = any(k in q for k in content_keywords)

    if meta_hit and content_hit:
        return "both"
    elif meta_hit:
        return "metadata"
    elif content_hit:
        return "content"
    else:
        return "both"  # default to both if unsure

def retrieve_context(question: str) -> dict:
    """
    Main retrieval logic:
    - Always fetch metadata for both videos (A and B).
    - If question is about content, also fetch transcript chunks.
    """
    intent = classify_question(question)

    # Always get metadata for both videos
    metadata_a = retrieve_metadata("A")
    metadata_b = retrieve_metadata("B")

    chunks = []
    if intent in ("content", "both"):
        chunks = retrieve_chunks(question, limit=3)

    return {
        "metadata_a": metadata_a,
        "metadata_b": metadata_b,
        "chunks": chunks,
        "intent": intent
    }