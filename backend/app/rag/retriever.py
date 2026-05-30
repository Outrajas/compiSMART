from app.services.vector_store_service import VectorStoreService
from app.db.sqlite import get_connection
import json

vector_store = VectorStoreService()

def retrieve_metadata_by_dataset(dataset_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM videos WHERE dataset_id = ?", (dataset_id,)
    ).fetchall()
    conn.close()
    videos = []
    for row in rows:
        data = dict(row)
        if data.get("hashtags"):
            data["hashtags"] = json.loads(data["hashtags"])
        views = data.get("views", 0) or 0
        likes = data.get("likes", 0) or 0
        comments = data.get("comments", 0) or 0
        data["engagement_rate"] = round((likes + comments) / views * 100, 4) if views else None
        videos.append(data)
    return videos

def retrieve_chunks(
    query: str,
    dataset_id: str,
    limit: int = 3,
    platform: str | None = None,
    time_max: float | None = None
) -> list[dict]:
    """Search for chunks. If time‑filtered and no results, fall back to unlimited time."""
    chunks = vector_store.search_with_filter(
        query, limit,
        dataset_id=dataset_id,
        platform=platform,
        time_max=time_max
    )
    if not chunks and time_max is not None:
        # Fallback: try without time restriction, then pick the earliest segments
        chunks = vector_store.search_with_filter(
            query, max(limit * 2, 10),   # retrieve more to find early ones
            dataset_id=dataset_id,
            platform=platform
        )
        # Sort by start_time and keep the earliest ones
        chunks.sort(key=lambda c: c.get("start_time", 0))
        chunks = chunks[:limit]
    return chunks

def classify_question(question: str) -> dict:
    q = question.lower()
    meta_keywords = ["creator", "engagement rate", "views", "likes", "comments",
                     "followers", "upload date", "follower count", "who is the creator",
                     "engagement", "top", "average"]
    content_keywords = ["hook", "transcript", "song", "lyric", "content", "compare the hook",
                        "first 5 seconds", "why did", "outperform", "improve", "suggestion"]
    time_keywords = ["first 5 seconds", "hook", "opening"]

    meta_hit = any(k in q for k in meta_keywords)
    content_hit = any(k in q for k in content_keywords)
    time_hit = any(k in q for k in time_keywords)

    if meta_hit and content_hit:
        intent = "both"
    elif meta_hit:
        intent = "metadata"
    elif content_hit:
        intent = "content"
    else:
        intent = "both"
    return {"intent": intent, "filter_first_5": time_hit}

def retrieve_context(question: str, dataset_id: str, platform: str = "youtube") -> dict:
    from app.services.analytics_service import get_platform_summary_for_dataset, get_semantic_profiles_for_dataset

    analysis = classify_question(question)
    intent = analysis["intent"]
    filter_time = analysis["filter_first_5"]

    all_metadata = retrieve_metadata_by_dataset(dataset_id)
    analytics_summary = get_platform_summary_for_dataset(dataset_id) if all_metadata else {}
    semantic_profiles = get_semantic_profiles_for_dataset(dataset_id) if dataset_id else []

    # Build hook summary
    hook_lines = []
    for p in semantic_profiles:
        title = p.get("title", p["video_id"])
        hook = p.get("hook_score", 0)
        hook_lines.append(f"- **{title}**: Hook={hook}/10 (coverage: {p.get('transcript_coverage', 0)}%)")
    hook_summary = "\n".join(hook_lines) if hook_lines else "No hook data."

    chunks = []
    if intent in ("content", "both"):
        chunks = retrieve_chunks(
            question,
            dataset_id=dataset_id,
            limit=5 if filter_time else 3,
            platform=platform,
            time_max=5.0 if filter_time else None
        )

    return {
        "all_metadata": all_metadata,
        "analytics_summary": analytics_summary,
        "chunks": chunks,
        "hook_summary": hook_summary,
        "semantic_profiles": semantic_profiles,
        "intent": intent,
        "filter_first_5": filter_time
    }