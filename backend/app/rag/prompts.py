import re
from typing import Optional, List, Dict, Any

def _video_summary(v: dict) -> str:
    title = v.get("title") or "Untitled"
    creator = v.get("creator")
    platform = v.get("platform", "")
    views = v.get("views")
    likes = v.get("likes")
    comments = v.get("comments")
    eng = v.get("engagement_rate")
    followers = v.get("follower_count")
    duration = v.get("duration")
    upload = v.get("upload_date")
    hashtags = v.get("hashtags", [])

    parts = [f'"{title}"']
    if creator:
        parts.append(f"by {creator}")
    lines = [" ".join(parts)]
    if followers:
        lines.append(f"  Followers: {followers:,}")
    if views:
        lines.append(f"  Views: {views:,}")
    if likes:
        lines.append(f"  Likes: {likes:,}")
    if comments:
        lines.append(f"  Comments: {comments:,}")
    if eng is not None:
        lines.append(f"  Engagement Rate: {eng:.4f}%")
    if duration:
        lines.append(f"  Duration: {duration}s")
    if upload:
        lines.append(f"  Upload Date: {upload}")
    if hashtags and len(hashtags) > 0:
        lines.append(f"  Hashtags: {', '.join(hashtags[:10])}")
    return "\n".join(lines)

def _data_completeness(videos: list[dict]) -> str:
    lines = []
    for v in videos:
        title = v.get("title") or v.get("video_id")
        missing = []
        if not v.get("creator"): missing.append("creator")
        if not v.get("views"): missing.append("views")
        if not v.get("engagement_rate") and v.get("views") is None: missing.append("engagement metrics")
        if not v.get("hashtags"): missing.append("hashtags")
        if not v.get("follower_count"): missing.append("follower count")
        if missing:
            lines.append(f'⚠️ "{title}": missing {", ".join(missing)}.')
        else:
            lines.append(f'✅ "{title}": full metadata available.')
    return "\n".join(lines)

def _chunk_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    lines = ["## Transcript Segments (with semantic scores)"]
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

def build_prompt(question: str, context: dict, history: str = "", platform: str = "youtube") -> str:
    all_metadata = context.get("all_metadata", [])
    chunks = context.get("chunks", [])
    filter_first_5 = context.get("filter_first_5", False)
    analytics_summary = context.get("analytics_summary", {})
    hook_summary = context.get("hook_summary", "No hook data available.")

    for v in all_metadata:
        if not v.get("title"):
            v["title"] = v["video_id"]
    for c in chunks:
        c["title"] = c.get("video_id", "?")

    completeness = _data_completeness(all_metadata)
    summaries = "\n".join([_video_summary(v) for v in all_metadata]) if all_metadata else "No videos available."
    chunks_block = _chunk_context(chunks) if chunks else ""

    analytics_block = ""
    if analytics_summary.get("count", 0) > 0:
        analytics_block = f"""## Analytics Overview
Total videos analyzed: {analytics_summary['count']}
Average Engagement Rate: {analytics_summary['average_engagement']}%
Best Engagement: "{analytics_summary['best_engagement']}" ({analytics_summary['best_engagement_value']}%)
Most Views: "{analytics_summary['most_views_title']}" ({analytics_summary['most_views_value']:,})
Largest Creator: {analytics_summary['largest_creator']} ({analytics_summary['largest_creator_followers']:,} followers)
"""

    history_block = f"## Conversation History\n{history}\n" if history else ""

    system = f"""You are an expert creator-growth analyst for {platform.capitalize()}. You must base every claim on the concrete semantic metrics provided below. Never guess or invent reasons.

**CRITICAL RULE:** When comparing videos, you MUST directly reference the following per-video semantic scores that have been pre-computed from the video transcripts. Do not say "it was more engaging" or "the content resonated better" unless you can point to specific numbers like a higher hook score, greater emotional intensity, earlier conflict, etc.

**Semantic Scores Per Video (0-10 scale):**
{hook_summary}

**How to use them:**
- **Hook Score:** high value means strong opening (question/conflict/curiosity). Compare hook scores to explain difference in initial attention.
- **Emotional Intensity:** high = more emotionally charged language.
- **Conflict Presence:** high = more segments contain opposition/contrast, which can drive retention.
- **Curiosity Score:** high = more questions/cliffhangers that keep viewers watching.
- **Humour Score:** high = more humorous elements.
- **CTA Score:** high = more direct calls to action.

**Response Format:**
1. Start with a bold summary of the key insight.
2. Use `### 🏆 Performance Summary` with bullet points of engagement rates and winner.
3. Use `### 🔍 Why This Happened` with a table or bullet list comparing the semantic scores (Hook, Emotion, Conflict, Curiosity, CTA, Humour) between the top and the other videos. For each metric, explain in one line how it likely contributed to the performance difference.
4. If transcript chunks are provided, quote the exact text and timestamp to support your semantic findings.
5. Use `### 📈 Recommendations` to give actionable, data-driven advice based on what the top video did better in the semantic dimensions. Be specific (e.g., "Increase Hook Score by adding a question or conflict in the first 3 seconds").
6. End with a **Confidence** line (High/Medium/Low) and a brief reason.

**Platform Isolation Rule:**
You only analyze {platform.capitalize()} videos. Never compare across platforms.

**Data Quality Overview:**
{completeness}
"""

    prompt = f"""{system}
{history_block}## User Question
{question}

## Available Data (only {platform.capitalize()})
{analytics_block}
{summaries}

{chunks_block}

Now answer the question following the guidelines above. Use the provided semantic scores as your primary evidence."""
    return prompt