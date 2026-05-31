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
        followers = data.get("follower_count", 0) or 0
        data["views_per_follower"] = round(views / followers, 2) if followers else None
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
    chunks = vector_store.search_with_filter(
        query, limit,
        dataset_id=dataset_id,
        platform=platform,
        time_max=time_max,
        video_ids=video_ids
    )
    if not chunks and time_max is not None:
        chunks = vector_store.search_with_filter(
            query, limit * 2,
            dataset_id=dataset_id,
            platform=platform,
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
    count = conn.execute("SELECT COUNT(*) FROM videos WHERE dataset_id = ?", (dataset_id,)).fetchone()[0]
    conn.close()
    return count > 0

# ---------- INTENT PLANNER (LLM‑based, retrieval‑first) ----------
def plan_intent(question: str, has_dataset: bool, groq_client) -> dict:
    """
    Returns a dict with keys:
        - needs_retrieval (bool): whether to fetch transcript chunks
        - needs_metadata (bool): whether to fetch metadata (always true if has_dataset)
        - style (str): "concise", "analytical", "verbatim"
        - intent (str): descriptive, for logging
    """
    # If no dataset, we can't retrieve anything meaningful
    if not has_dataset:
        return {
            "needs_retrieval": False,
            "needs_metadata": False,
            "style": "normal",
            "intent": "no_dataset"
        }

    system = """You are a decision engine for a creator assistant. Your task is to decide whether a user query requires access to the loaded dataset (transcripts and metadata).

Rules:
- If the question asks about **any of the loaded videos** (e.g., "engagement rate", "which video", "compare", "hook", "transcript", "dialogue", "why did X outperform Y"), then needs_retrieval = true.
- If the question is **completely unrelated** to the loaded dataset (e.g., "what is the population of France", "tell me a joke", "write python code", "how to cook pasta"), then needs_retrieval = false.
- Even if the question is a greeting like "sup" or "hello", if a dataset is loaded, assume the user might want a quick summary → needs_retrieval = true (but style="concise").

Output JSON with:
{
    "needs_retrieval": bool,
    "style": "concise" | "analytical" | "verbatim",
    "reasoning": "short explanation"
}

Style:
- "concise": for simple factual questions (e.g., "engagement rate of each video")
- "analytical": for comparisons, why questions, deep analysis
- "verbatim": when user asks for exact dialogues, quotes, timestamps

Now, answer for this query:"""

    prompt = f"""Dataset loaded: Yes, {dataset_has_videos} videos.
User question: {question}
JSON:"""
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
        # Ensure defaults
        return {
            "needs_retrieval": parsed.get("needs_retrieval", True),
            "style": parsed.get("style", "analytical"),
            "intent": parsed.get("reasoning", "dataset_query")[:50]
        }
    except Exception as e:
        print(f"Intent planner error: {e}, falling back to retrieval=true")
        # Fallback: always retrieve when dataset exists
        return {
            "needs_retrieval": True,
            "style": "analytical",
            "intent": "fallback_retrieve"
        }

# ---------- SESSION MEMORY (unchanged) ----------
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
            if k in ["active_videos", "last_comparison"]:
                current[k] = v
            else:
                current[k] = v
    conn.execute("""
        INSERT OR REPLACE INTO session_state (session_id, last_intent, last_topic, active_videos, last_comparison, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        session_id,
        current.get("last_intent"),
        current.get("last_topic"),
        json.dumps(current.get("active_videos", [])),
        json.dumps(current.get("last_comparison")) if current.get("last_comparison") else None,
    ))
    conn.commit()
    conn.close()

# ---------- CONTEXT COMPRESSION ----------
def compress_context(chunks: list[dict], max_chunks: int = 10) -> list[dict]:
    return chunks[:max_chunks]

# ---------- retrieve_context ----------
def retrieve_context(question: str, dataset_id: str, platform: str = "youtube", needs_retrieval: bool = True) -> dict:
    from app.services.analytics_service import get_platform_summary_for_dataset, get_semantic_profiles_for_dataset

    all_metadata = retrieve_metadata_by_dataset(dataset_id)
    analytics_summary = get_platform_summary_for_dataset(dataset_id) if all_metadata else {}
    semantic_profiles = get_semantic_profiles_for_dataset(dataset_id) if dataset_id else []

    hook_lines = []
    for p in semantic_profiles:
        title = p.get("title", p["video_id"])
        hook = p.get("hook_score", 0)
        hook_lines.append(f"- **{title}**: Hook={hook}/10 (coverage: {p.get('transcript_coverage', 0)}%)")
    hook_summary = "\n".join(hook_lines) if hook_lines else "No hook data."

    chunks = []
    if needs_retrieval:
        # Determine if user wants specific video
        video_ids = None
        for v in all_metadata:
            title = v.get("title", "")
            if title and title.lower() in question.lower():
                video_ids = [v["video_id"]]
                break
        chunks = retrieve_chunks(
            question,
            dataset_id=dataset_id,
            limit=10,
            platform=platform,
            time_max=None,
            video_ids=video_ids
        )
        # Debug log
        print(f"DEBUG: Retrieved {len(chunks)} chunks for query: {question[:50]}")
        if chunks:
            print(f"DEBUG: First chunk text: {chunks[0].get('text', '')[:100]}")
        else:
            print("DEBUG: No chunks retrieved from Qdrant")

    return {
        "all_metadata": all_metadata,
        "analytics_summary": analytics_summary,
        "chunks": chunks,
        "hook_summary": hook_summary,
        "semantic_profiles": semantic_profiles,
    }