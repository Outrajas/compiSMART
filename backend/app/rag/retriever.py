from app.services.vector_store_service import VectorStoreService
from app.db.sqlite import get_connection, get_dataset_video_ids
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import json

vector_store = VectorStoreService()

def retrieve_metadata_by_dataset(dataset_id: str, active_video_ids: list[str] = None) -> list[dict]:
    conn = get_connection()
    
    # Isolate extraction scope cleanly to current active context list parameters
    if active_video_ids is not None:
        if not active_video_ids:
            conn.close()
            return []
        placeholders = ",".join(["?"] * len(active_video_ids))
        query = f"SELECT * FROM videos WHERE video_id IN ({placeholders})"
        rows = conn.execute(query, active_video_ids).fetchall()
    else:
        query = """
            SELECT v.* FROM videos v
            JOIN dataset_videos dv ON v.video_id = dv.video_id
            WHERE dv.dataset_id = ?
        """
        rows = conn.execute(query, (dataset_id,)).fetchall()
        
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
        followers = data.get("follower_count", 0) or 0
        data["views_per_follower"] = round(views / followers, 2) if followers else None
        
        # --- CHRONOLOGICAL TRANSCRIPT RECONSTRUCTION (Fallback for old cache) ---
        transcript = data.get("transcript")
        if not transcript:
            try:
                client = QdrantClient(host="localhost", port=6333)
                results = client.scroll(
                    collection_name="video_chunks",
                    scroll_filter=Filter(must=[
                        FieldCondition(key="video_id", match=MatchValue(value=data["video_id"]))
                    ]),
                    limit=2000
                )
                chunks = results[0]
                if chunks:
                    # Sort completely chronologically to guarantee correct order
                    chunks.sort(key=lambda c: c.payload.get("start_time", 0))
                    data["transcript"] = " ".join(c.payload.get("text", "") for c in chunks)
                else:
                    data["transcript"] = ""
            except Exception as e:
                print(f"Error reconstructing transcript for {data['video_id']}: {e}")
                data["transcript"] = ""
                
        videos.append(data)
    return videos

def retrieve_chunks(
    query: str,
    dataset_id: str,
    limit: int = 5,
    platform: str | None = None,
    time_max: float | None = None,
    video_ids: list[str] | None = None
) -> list[dict]:
    # Clean cross-platform parameter mapping to prevent Qdrant filter suppressions
    if platform == "cross-platform":
        platform = None

    chunks = vector_store.search_with_filter(
        query, limit,
        dataset_id=dataset_id,
        platform=platform,
        time_max=time_max,
        video_ids=video_ids
    )
    if not chunks:
        chunks = vector_store.search_with_filter(
            query, limit * 2,
            dataset_id=None,
            platform=platform,
            time_max=time_max,
            video_ids=video_ids
        )
        if time_max == 5.0:
            chunks.sort(key=lambda c: c.get("start_time", 0))
            chunks = chunks[:limit]
        else:
            chunks = chunks[:limit]
    return chunks

def dataset_has_videos(dataset_id: str) -> bool:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM dataset_videos WHERE dataset_id = ?", (dataset_id,)).fetchone()[0]
    conn.close()
    return count > 0

# ---------- INTENT PLANNER ----------
def plan_intent(question: str, has_dataset: bool, groq_client) -> dict:
    if not has_dataset:
        return {
            "needs_retrieval": False,
            "needs_metadata": False,
            "style": "normal",
            "intent": "no_dataset"
        }

    system = """You are a decision engine for a creator assistant. Your task is to decide whether a user query requires access to the loaded dataset (transcripts and metadata).

Rules:
- If the question asks about **any of the loaded videos** (e.g., "engagement rate", "which video", "hook", "dialogue", "why did X outperform Y"), then needs_retrieval = true.
- If the user explicitly asks for the **full, complete, or entire transcript** of a video, set style="full_transcript" and needs_retrieval=false.
- If the user asks to **compare transcripts** (e.g., "compare transcripts of each video", "compare storytelling"), set style="transcript_comparison" and needs_retrieval=false.
- If the user asks for exact quotes or specific verbatim dialogues (but NOT the full transcript), set style="verbatim" and needs_retrieval=true.
- If the question is **completely unrelated** to the loaded dataset (e.g., "what is the population of France", "write python code"), then needs_retrieval = false.

Output JSON with:
{
    "needs_retrieval": bool,
    "style": "concise" | "analytical" | "verbatim" | "full_transcript" | "transcript_comparison",
    "reasoning": "short explanation"
}
"""

    prompt = f"User question: {question}\nJSON:"
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        return {
            "needs_retrieval": parsed.get("needs_retrieval", True),
            "style": parsed.get("style", "analytical"),
            "intent": parsed.get("reasoning", "dataset_query")[:50]
        }
    except Exception as e:
        print(f"Intent planner error: {e}, falling back to retrieval=true")
        return {
            "needs_retrieval": True,
            "style": "analytical",
            "intent": "fallback_retrieve"
        }

# ---------- SESSION MEMORY ----------
def init_session_state_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            last_intent TEXT,
            last_topic TEXT,
            active_videos TEXT,
            last_comparison TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_session_state(session_id: str) -> dict:
    init_session_state_table()
    conn = get_connection()
    row = conn.execute("SELECT * FROM session_state WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return {"last_intent": None, "last_topic": None, "active_videos": [], "last_comparison": None}
    return {
        "last_intent": row["last_intent"],
        "last_topic": row["last_topic"],
        "active_videos": json.loads(row["active_videos"]) if row["active_videos"] else [],
        "last_comparison": json.loads(row["last_comparison"]) if row["last_comparison"] else None,
    }

def update_session_state(session_id: str, **kwargs):
    conn = get_connection()
    current = get_session_state(session_id)
    for k, v in kwargs.items():
        if v is not None:
            current[k] = v
    conn.execute("""
        INSERT OR REPLACE INTO session_state (session_id, last_intent, last_topic, active_videos, last_comparison, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        session_id,
        current.get("last_intent"),
        current.get("last_topic"),
        json.dumps(current.get("active_videos")),
        json.dumps(current.get("last_comparison")) if current.get("last_comparison") else None,
    ))
    conn.commit()
    conn.close()


def compress_context(chunks: list[dict], max_chunks: int = 10) -> list[dict]:
    return chunks[:max_chunks]


def retrieve_context(question: str, dataset_id: str, platform: str = "youtube", needs_retrieval: bool = True, active_video_ids: list[str] = None) -> dict:
    from app.services.analytics_service import get_platform_summary_for_dataset, get_semantic_profiles_for_dataset

    search_platform = None if platform == "cross-platform" else platform

    if active_video_ids is None:
        active_video_ids = get_dataset_video_ids(dataset_id)

    all_metadata = retrieve_metadata_by_dataset(dataset_id, active_video_ids)
    analytics_summary = get_platform_summary_for_dataset(dataset_id, active_video_ids) if all_metadata else {}
    semantic_profiles = get_semantic_profiles_for_dataset(dataset_id, active_video_ids) if dataset_id else []

    hook_lines = []
    for p in semantic_profiles:
        title = p.get("title", p["video_id"])
        hook = p.get("hook_score", 0)
        hook_lines.append(f"- **{title}**: Hook={hook}/10 (coverage: {p.get('transcript_coverage', 0)}%)")
    hook_summary = "\n".join(hook_lines) if hook_lines else "No hook data."

    chunks = []
    if needs_retrieval and active_video_ids:
        keywords = ["quote", "dialogue", "conversation", "emotion", "humor", "hook", "compare"]
        base_limit = 30 if any(k in question.lower() for k in keywords) else 10

        specific_video_ids = []
        for v in all_metadata:
            title = v.get("title", "")
            if title and title.lower() in question.lower():
                specific_video_ids.append(v["video_id"])
        
        target_videos = specific_video_ids if specific_video_ids else active_video_ids

        for vid in target_videos:
            vid_chunks = retrieve_chunks(
                question,
                dataset_id=dataset_id,
                limit=base_limit,
                platform=search_platform,
                time_max=None,
                video_ids=[vid]
            )
            chunks.extend(vid_chunks)

    return {
        "all_metadata": all_metadata,
        "analytics_summary": analytics_summary,
        "chunks": chunks,
        "hook_summary": hook_summary,
        "semantic_profiles": semantic_profiles,
    }