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
    
    q_count = v.get("question_count", 0)
    e_words = v.get("emotion_words", 0)
    c_score = v.get("conflict_score", 0)
    h_score = v.get("humor_score", 0)

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
    if hashtags:
        lines.append(f"Tags: {', '.join(hashtags[:5])}")
    
    # FIX: Explicitly enforce the LLM's understanding of chronological placement
    if hook_text:
        lines.append(f"First 15s Hook Transcript (Intro Text): {hook_text[:300]}")
        
    lines.append(f"Global Transcript Stats: {q_count} questions, {e_words} emotion markers, {c_score} conflict markers, {h_score} humor markers")
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

def _full_transcript_context(all_metadata: list[dict]) -> str:
    lines = ["## Full Transcripts (Chronological)"]
    for v in all_metadata:
        title = v.get("title", v.get("video_id", "Unknown"))
        platform = str(v.get("platform", "unknown")).upper()
        transcript = v.get("transcript", "")
        if not transcript:
            transcript = "[No transcript available for this video]"
        lines.append(f"### [{platform}] {title}\n{transcript}\n")
    return "\n".join(lines)

def _build_full_transcript_prompt(question: str, context: dict, history: str = "") -> str:
    all_metadata = context.get("all_metadata", [])
    transcripts_block = _full_transcript_context(all_metadata)
    history_block = f"## Conversation History Context\n{history}\n" if history else ""
    
    return f"""You are a transcript retrieval engine. The user has requested the full or complete transcript for the video(s).

{history_block}
{transcripts_block}

User question: {question}

Respond by providing the full transcript text exactly as requested, grouped clearly by video. Do not summarize, truncate, or use semantic RAG chunks. Do not hallucinate content. Provide the chronological text."""

def _build_transcript_comparison_prompt(question: str, context: dict, history: str = "", platform: str = "mixed") -> str:
    all_metadata = context.get("all_metadata", [])
    transcripts_block = _full_transcript_context(all_metadata)
    summaries = "\n".join([_video_summary(v) for v in all_metadata]) if all_metadata else "No videos."
    history_block = f"## Conversation History Context\n{history}\n" if history else ""
    
    return f"""You are a rigorous creator-growth analyst specialized in cross-platform media. The user wants to compare the full transcripts of the videos.

{history_block}

## Full Transcripts for Comparison
{transcripts_block}

## Metadata Context & Global Transcript Statistics
{summaries}

User question: {question}

Compare the transcripts directly. Analyze length, dialogue density, emotional language, questions, conflict, humor, and storytelling based ONLY on the full text provided above. Provide concrete verbatim examples from the text to back up your points."""

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
    chunks_block = _chunk_context(chunks) if chunks else "## No semantic vector chunks were queried for this specific task. Evaluate using Metadata and Global Transcript Stats."
    coverage_block = _coverage_text(semantic_profiles)
    winners = _winners_block(analytics_summary, semantic_profiles)

    history_block = f"## Conversation History Context\n{history}\n" if history else ""

    system = """You are a rigorous creator-growth analyst specialized in cross-platform media conversion dynamics (YouTube vs Instagram). 

**Strict Operational Constraints:**
1. **Differentiate Platform Origins Exclusively**: You are analyzing a mixed platform dataset. You must clearly state what belongs to YouTube and what belongs to Instagram. Never mix up metadata attributes.
2. **Platform Performance Auditing Rules**: 
   - YouTube calculates Engagement Rate relative to Views.
   - Instagram calculations evaluate Engagement using absolute interaction volume weights because View counts are subject to profile access layers. Acknowledge this platform metric schema change explicitly if comparing performance.
3. **Evidence Extraction Protection**: An Instagram caption or Hook Segment Text IS valid transcript evidence. Furthermore, Global Transcript Stats provide the exact density of emotional/conflict/humor terms across the full video. Never claim transcript evidence is missing if Hook Segment Text or Global Transcript Stats are provided.
4. **Confidence Node**: Finalize every evaluation section with an explicit analytical certainty score (High/Medium/Low).
5. **Hook Analysis Priority**: To analyze hooks, intros, or the beginning of a video, you MUST rely exclusively on the 'First 15s Hook Transcript (Intro Text)' field provided in the Asset Metrics List. Do NOT try to piece together the start of the video using random semantic vector chunks.
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
    elif intent == "full_transcript":
        return _build_full_transcript_prompt(question, context, history)
    elif intent == "transcript_comparison":
        return _build_transcript_comparison_prompt(question, context, history, platform)
    else:
        return _build_deep_analytical_prompt(question, context, history, platform)