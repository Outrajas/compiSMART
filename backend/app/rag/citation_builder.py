def build_citations(context: dict) -> list[str]:
    """
    Build a list of human‑friendly source strings.
    Each source string looks like: "BB Ki Vines — Opening Hook (0s–5s)"
    """
    sources = []
    all_metadata = context.get("all_metadata", [])
    chunks = context.get("chunks", [])

    # Helper: get title for a video_id
    title_map = {m["video_id"]: m.get("title", m["video_id"]) for m in all_metadata}

    for c in chunks:
        vid = c.get("video_id", "?")
        title = title_map.get(vid, vid)
        start = c.get("start_time")
        end = c.get("end_time")
        if start is not None and start <= 5:
            desc = f"Opening Hook ({start:.1f}s–{end:.1f}s)"
        elif start is not None:
            desc = f"Transcript Segment ({start:.1f}s–{end:.1f}s)"
        else:
            desc = "Transcript Segment"
        sources.append(f"{title} — {desc}")

    # Add metadata sources
    for m in all_metadata:
        title = m.get("title", m["video_id"])
        if m.get("platform") == "youtube":
            sources.append(f"{title} — YouTube metadata")
        else:
            sources.append(f"{title} — Instagram metadata")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in sources:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique