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
    hook_text = v.get("hook_text")
    platform = str(v.get("platform", "unknown")).upper()

    # Prepend explicit platform tags so the LLM identifies cross-platform scope instantly
    lines = [f'[{platform}] "{title}"']
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
    if hook_text:
        lines.append(f"Hook Segment Text: {hook_text[:300]}")
    return " | ".join(lines)

def _data_completeness(videos: list[dict]) -> str:
    lines = []
    for v in videos:
        title = v.get("title") or v.get("video_id")
        platform = str(v.get("platform", "unknown")).upper()
        missing = []
        if not v.get("creator"): missing.append("creator")
        if not v.get("views") and platform == "YOUTUBE": missing.append("views")
        if not v.get("engagement_rate"): missing.append("engagement metrics")
        if missing:
            lines.append(f'⚠️ [{platform}] "{title}": missing {", ".join(missing)}.')
        else:
            lines.append(f'✅ [{platform}] "{title}": complete records.')
    return "\n".join(lines)

def _chunk_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    for c in chunks:
        if "text" not in c:
            print(f"WARNING: Chunk missing 'text' field: {c.keys()}")
    lines = ["## Cross-Platform Transcript Segments (partitioned with metadata markers)"]
    for c in chunks:
        title = c.get("title", c.get("video_id", "?"))
        start = c.get("start_time")
        end = c.get("end_time")
        text = c.get("text", "")
        platform = str(c.get("platform", "unknown")).upper()
        if not text:
            text = "[MISSING TEXT]"
        features = c.get("semantic_features", {})
        hook = features.get("hook_score", "?")
        question = "Q" if features.get("question") else ""
        conflict = "C" if features.get("conflict") else ""
        emotion = features.get("emotion", "")
        time_str = f"[{start:.1f}s - {end:.1f}s]" if start is not None and end is not None else ""
        tags = " ".join(filter(None, [question, conflict, f"emotion:{emotion}" if emotion else ""])).strip()
        extra = f" (platform={platform}, hook={hook}{', ' + tags if tags else ''})"
        lines.append(f"- {title} {time_str}{extra}: {text}")
    return "\n".join(lines)

def _verbatim_chunk_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No transcript chunks available."
    lines = ["## Verbatim Transcript Lines (platform contextual anchors)"]
    for c in chunks:
        start = c.get("start_time")
        text = c.get("text", "")
        platform = str(c.get("platform", "unknown")).upper()
        if start is not None and text:
            lines.append(f"[{platform}][{start:.1f}s] {text}")
        elif text:
            lines.append(f"[{platform}] {text}")
    return "\n".join(lines)

def _coverage_text(semantic_profiles: list[dict]) -> str:
    if not semantic_profiles:
        return ""
    lines = ["## Transcript Coverage Mapping"]
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
        if sorted_hooks:
            winners.append(f"Hook Score Winner: **{sorted_hooks[0]['title']}** ({sorted_hooks[0]['hook_score']}/10)")
    return "\n".join(winners)

def _build_minimal_fact_prompt(question: str, context: dict, history: str = "") -> str:
    all_metadata = context.get("all_metadata", [])
    if not all_metadata:
        return f"Question: {question}\nNo videos loaded."

    best = max(all_metadata, key=lambda v: v.get("engagement_rate") or 0)
    title = best.get("title", "Unknown")
    engagement = best.get("engagement_rate")
    platform = str(best.get("platform", "unknown")).upper()
    
    snapshot = f"Top Performing Unified Asset: [{platform}] {title}"
    if engagement is not None:
        snapshot += f" (Engagement Metric Strength: {engagement:.2f}%)"

    history_block = f"History:\n{history}\n" if history else ""
    return f"""{history_block}Data snapshot: {snapshot}

Question: {question}
Short, factual cross-platform answer (1-2 sentences):"""

def _build_casual_prompt(question: str, history: str = "") -> str:
    return f"""Conversation history:
{history}
User: {question}
Assistant (friendly, concise, cross-platform aware):"""

def _build_general_qa_prompt(question: str, history: str = "") -> str:
    return f"""Answer this general knowledge question accurately and concisely. No dataset involved.

History:
{history}
User: {question}
Answer:"""

def _build_comparison_prompt(question: str, context: dict, history: str = "") -> str:
    all_metadata = context.get("all_metadata", [])
    if not all_metadata:
        return f"Question: {question}\nNo videos loaded."

    summaries = "\n".join([_video_summary(v) for v in all_metadata])
    return f"""Compare the cross-platform media matrix below. Answer briefly focusing directly on the platform discrepancies.

Data Elements:
{summaries}

History:
{history}

Question: {question}
Answer:"""

def _build_transcript_query_prompt(question: str, context: dict, history: str = "") -> str:
    chunks = context.get("chunks", [])
    all_metadata = context.get("all_metadata", [])
    if not chunks:
        video_titles = [f"[{str(v.get('platform')).upper()}] {v.get('title', v['video_id'])}" for v in all_metadata]
        return f"""User requested raw textual elements from multiple assets. However, no valid platform segment structures were found: {', '.join(video_titles)}.
Please respond: "No valid transcript segments available for the cross-platform request. I can only audit metadata variables."
History: {history}
"""
    verbatim = _verbatim_chunk_context(chunks)
    return f"""You are a cross-platform transcript query engine. Answer using ONLY the verbatim lines provided below.

{verbatim}

User question: {question}

Group quotes by platform identity explicitly ([YOUTUBE] vs [INSTAGRAM]). Do not hallucinate timelines or phrases."""

def _build_deep_analytical_prompt(question: str, context: dict, history: str = "", platform: str = "youtube") -> str:
    all_metadata = context.get("all_metadata", [])
    chunks = context.get("chunks", [])
    analytics_summary = context.get("analytics_summary", {})
    hook_summary = context.get("hook_summary", "")
    semantic_profiles = context.get("semantic_profiles", [])

    completeness = _data_completeness(all_metadata)
    summaries = "\n".join([_video_summary(v) for v in all_metadata]) if all_metadata else "No videos."
    chunks_block = _chunk_context(chunks) if chunks else "## No platform transcript chunks available. Evaluating via metadata store metrics."
    coverage_block = _coverage_text(semantic_profiles)
    winners = _winners_block(analytics_summary, semantic_profiles)

    history_block = f"## Conversation History Context\n{history}\n" if history else ""

    system = """You are a rigorous creator-growth analyst specialized in cross-platform media conversion dynamics (YouTube vs Instagram). 

**Strict Operational Constraints:**
1. **Differentiate Platform Origins Exclusively**: You are analyzing a mixed platform dataset. You must clearly state what belongs to YouTube and what belongs to Instagram. Never mix up metadata attributes.
2. **Platform Performance Auditing Rules**: 
   - YouTube calculates Engagement Rate relative to Views.
   - Instagram calculations evaluate Engagement using absolute interaction volume weights because View counts are subject to profile access layers. Acknowledge this platform metric schema change explicitly if comparing performance.
3. **Evidence Extraction Protection**: Every assertion must link back to specific platform data tokens or Hook Segment Texts. Never claim evidence is missing unless all retrieved blocks for that platform are blank.
4. **Confidence Node**: Finalize every evaluation section with an explicit analytical certainty score (High/Medium/Low).
"""

    prompt = f"""{system}

{history_block}## Data Architecture Ingested
- **Cross-Platform Winners**: {winners or 'None'}
- **Calibrated Hook Breakdown**: {hook_summary or 'None'}
- **Coverage Summary**: {coverage_block or 'None'}

### Full Ingested Asset Metrics List
{summaries}

{chunks_block}

---
## Target Query Task
User Question: {question}
Data Completeness Baseline:
{completeness}

Answer:"""
    return prompt

def build_prompt(question: str, context: dict, history: str = "", platform: str = "youtube", intent: str = "dataset_deep") -> str:
    if intent == "casual":
        return _build_casual_prompt(question, history)
    elif intent == "general_qa":
        return _build_general_qa_prompt(question, history)
    elif intent == "dataset_simple":
        return _build_minimal_fact_prompt(question, context, history)
    elif intent == "dataset_comparison":
        return _build_comparison_prompt(question, context, history)
    elif intent == "transcript_query":
        return _build_transcript_query_prompt(question, context, history)
    else:
        return _build_deep_analytical_prompt(question, context, history, platform)