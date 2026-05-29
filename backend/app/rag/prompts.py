def build_prompt(question: str, context: dict, history: str = "") -> str:
    """
    Construct the prompt for the LLM.
    context contains metadata_a, metadata_b, chunks, intent.
    history is optional pre‑formatted chat history.
    """
    metadata_a = context.get("metadata_a", {})
    metadata_b = context.get("metadata_b", {})
    chunks = context.get("chunks", [])

    def format_meta(m, label):
        if not m:
            return f"{label}: No metadata available."
        return (
            f"{label}:\n"
            f"  Title: {m.get('title') or 'N/A'}\n"
            f"  Creator: {m.get('creator') or 'N/A'}\n"
            f"  Views: {m.get('views')}\n"
            f"  Likes: {m.get('likes')}\n"
            f"  Comments: {m.get('comments')}\n"
            f"  Engagement Rate: {m.get('engagement_rate')}%\n"
            f"  Duration (seconds): {m.get('duration')}\n"
            f"  Upload Date: {m.get('upload_date')}\n"
            f"  Follower Count: {m.get('follower_count')}\n"
            f"  Hashtags: {', '.join(m.get('hashtags', []))}"
        )

    meta_str_a = format_meta(metadata_a, "Video A")
    meta_str_b = format_meta(metadata_b, "Video B")

    chunks_str = ""
    if chunks:
        chunks_str = "\nRelevant Transcript Chunks:\n"
        for i, c in enumerate(chunks, 1):
            chunks_str += f"  Chunk {i} (Video {c.get('video_id')}, Chunk #{c.get('chunk_id')}): {c.get('text')}\n"

    history_block = ""
    if history:
        history_block = f"Chat History:\n{history}\n\n"

    prompt = f"""You are a social media analyst. Answer the user's question using the provided data and conversation history.
Always cite specific numbers when available. If comparing videos, use exact values.

{history_block}User Question: {question}

Available Data:
{meta_str_a}

{meta_str_b}
{chunks_str}
Instructions:
- If the question asks about metadata (creator, views, engagement, etc.), answer directly from the metadata above.
- If the question asks about content or hooks, base your answer on the transcript chunks.
- If comparing videos, use the exact numbers and explain differences clearly.
- When suggesting improvements, refer to what worked in Video A and apply to Video B.
- Always mention which video and which data source you are using.

Answer:"""

    return prompt