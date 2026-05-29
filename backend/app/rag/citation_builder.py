def build_citations(context: dict) -> list[dict]:
    """
    Build a structured list of sources.
    Returns a list of objects: { "video_id": ..., "chunk_id": ... or null }
    """
    sources = []

    # Metadata sources (no chunk_id)
    if context.get("metadata_a"):
        sources.append({"video_id": "A", "chunk_id": None})
    if context.get("metadata_b"):
        sources.append({"video_id": "B", "chunk_id": None})

    # Transcript chunk sources
    for chunk in context.get("chunks", []):
        sources.append({
            "video_id": chunk.get("video_id"),
            "chunk_id": chunk.get("chunk_id")
        })

    return sources