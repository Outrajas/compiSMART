def _video_summary(v: dict) -> str:
    title = v.get("title") or "Untitled"
    creator = v.get("creator")
    views = v.get("views")
    likes = v.get("likes")
    comments = v.get("comments")
    eng = v.get("engagement_rate")
    followers = v.get("follower_count")
    duration = v.get("duration")
    upload = v.get("upload_date")
    vpf = v.get("views_per_follower")
    hashtags = v.get("hashtags", [])

    lines = [f'"{title}"']
    if creator:
        lines.append(f"by {creator}")
    if followers:
        lines.append(f"Followers: {followers:,}")
    if views:
        lines.append(f"Views: {views:,}")
    if likes:
        lines.append(f"Likes: {likes:,}")
    if comments:
        lines.append(f"Comments: {comments:,}")
    if eng is not None:
        lines.append(f"Engagement: {eng:.2f}%")
    if vpf is not None:
        lines.append(f"Views/Follower: {vpf:.1f}x")
    if duration:
        lines.append(f"Duration: {duration}s")
    if upload:
        lines.append(f"Upload: {upload}")
    if hashtags:
        lines.append(f"Tags: {', '.join(hashtags[:5])}")
    return " | ".join(lines)

def _data_completeness(videos: list[dict]) -> str:
    lines = []
    for v in videos:
        title = v.get("title") or v.get("video_id")
        missing = []
        if not v.get("creator"): missing.append("creator")
        if not v.get("views"): missing.append("views")
        if not v.get("engagement_rate"): missing.append("engagement metrics")
        if not v.get("hashtags"): missing.append("hashtags")
        if not v.get("follower_count"): missing.append("follower count")
        if missing:
            lines.append(f'⚠️ "{title}": missing {", ".join(missing)}.')
        else:
            lines.append(f'✅ "{title}": complete.')
    return "\n".join(lines)

def _chunk_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    lines = ["## Transcript Segments (with features)"]
    for c in chunks:
        title = c.get("title", c.get("video_id", "?"))
        start = c.get("start_time")
        end = c.get("end_time")
        text = c.get("text", "")
        features = c.get("semantic_features", {})
        hook = features.get("hook_score", "?")
        question = "Q" if features.get("question") else ""
        conflict = "C" if features.get("conflict") else ""
        emotion = features.get("emotion", "")
        time_str = f"[{start:.1f}s - {end:.1f}s]" if start is not None and end is not None else ""
        tags = " ".join(filter(None, [question, conflict, f"emotion:{emotion}" if emotion else ""])).strip()
        extra = f" (hook={hook}{', ' + tags if tags else ''})"
        lines.append(f"- {title} {time_str}{extra}: {text}")
    return "\n".join(lines)

def _coverage_text(semantic_profiles: list[dict]) -> str:
    if not semantic_profiles:
        return ""
    lines = ["## Transcript Coverage"]
    for p in semantic_profiles:
        cov = p.get("transcript_coverage", 0)
        segs = p.get("total_segments", 0)
        lines.append(f"- **{p.get('title', p['video_id'])}**: {cov}% ({segs} segments)")
    return "\n".join(lines)

def _winners_block(analytics_summary: dict, semantic_profiles: list[dict]) -> str:
    winners = []
    if analytics_summary.get("best_engagement_value"):
        winners.append(f"Engagement Winner: **{analytics_summary['best_engagement']}** ({analytics_summary['best_engagement_value']}%)")
    if analytics_summary.get("most_views_value"):
        winners.append(f"Views Winner: **{analytics_summary['most_views_title']}** ({analytics_summary['most_views_value']:,})")
    if semantic_profiles:
        sorted_hooks = sorted(semantic_profiles, key=lambda x: x["hook_score"], reverse=True)
        winners.append(f"Hook Score Winner: **{sorted_hooks[0]['title']}** ({sorted_hooks[0]['hook_score']}/10)")
    if analytics_summary.get("outlier_videos"):
        winners.append(f"⚠️ Viral Outliers (high Views/Follower): {', '.join(analytics_summary['outlier_videos'])}")
    if analytics_summary.get("best_views_per_follower_title"):
        winners.append(f"Efficiency Winner (Views/Follower): **{analytics_summary['best_views_per_follower_title']}** ({analytics_summary['best_views_per_follower_value']}x)")
    return "\n".join(winners)

def build_prompt(question: str, context: dict, history: str = "", platform: str = "youtube") -> str:
    all_metadata = context.get("all_metadata", [])
    chunks = context.get("chunks", [])
    analytics_summary = context.get("analytics_summary", {})
    hook_summary = context.get("hook_summary", "")
    semantic_profiles = context.get("semantic_profiles", [])

    completeness = _data_completeness(all_metadata)
    summaries = "\n".join([_video_summary(v) for v in all_metadata]) if all_metadata else "No videos."
    chunks_block = _chunk_context(chunks) if chunks else ""
    coverage_block = _coverage_text(semantic_profiles)
    winners = _winners_block(analytics_summary, semantic_profiles)

    history_block = f"## Conversation History\n{history}\n" if history else ""

    system = f"""You are a rigorous creator‑growth analyst for {platform.capitalize()}. **Every claim must be supported by the provided data. Never speculate or invent structure.**

**Data Available:**
- **Pre‑computed Winners:** {winners or 'None'}
- **Semantic Scores (0‑10):** {hook_summary or 'None'}
- **Transcript Coverage:** {coverage_block or 'None'}
- **Metadata summaries:** below.
- **Transcript segments:** attached if relevant.

**Strict Rules:**
1. **No fake timeline.** Do NOT describe “beginning”, “middle”, or “end” unless transcript coverage exceeds 80% AND you have segments spanning the full duration. If coverage < 30%, explicitly say “Insufficient data for timeline analysis (coverage X%)”. Even if coverage is high, only describe what is directly visible in the provided segments.
2. **Evidence‑only reasoning.** When comparing, cite exact metrics: engagement rate, views/follower, hook scores, semantic features. Do not use vague phrases like “high‑quality content” – explain which specific numbers support the conclusion.
3. **Hook analysis.** Compare hook scores and, if coverage allows, point to the semantic features (question, conflict, emotion). If transcript coverage < 10%, state that hook confidence is Low.
4. **Outlier detection.** Videos with extremely high Views/Follower are potential viral breakouts. Highlight them and discuss possible reasons (algorithm pickup, shareability) – but stay grounded in the numbers.
5. **Confidence.** End each section with a confidence level (High/Medium/Low) and a brief justification based on data completeness and coverage.
6. **Views/Follower** is one of the most important metrics. Always mention it when comparing videos, especially if there’s a large disparity.

**Data Quality:**
{completeness}
"""

    prompt = f"""{system}

{history_block}## User Question
{question}

{summaries}

{chunks_block}
{coverage_block}

Answer:"""
    return prompt