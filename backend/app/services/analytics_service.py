from app.db.sqlite import get_connection
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
def get_semantic_profiles_for_dataset(dataset_id: str) -> list[dict]:
    """Return semantic profile for each video in the dataset."""
    videos = get_videos_by_dataset(dataset_id)
    profiles = []
    for v in videos:
        profile = get_video_semantic_profile(v["video_id"], dataset_id)
        profile["video_id"] = v["video_id"]
        profile["title"] = v.get("title", "")
        profiles.append(profile)
    return profiles
def get_video_semantic_profile(video_id: str, dataset_id: str) -> dict:
    """Aggregate semantic features across all chunks of a video."""
    client = QdrantClient(host="localhost", port=6333)
    results = client.scroll(
        collection_name="video_chunks",
        scroll_filter=Filter(must=[
            FieldCondition(key="video_id", match=MatchValue(value=video_id)),
            FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))
        ]),
        limit=1000
    )
    chunks = results[0]
    if not chunks:
        return {}

    total = len(chunks)
    avg_humor = sum(c.payload.get("semantic_features", {}).get("humor_score", 0) for c in chunks) / total
    avg_curiosity = sum(c.payload.get("semantic_features", {}).get("curiosity_score", 0) for c in chunks) / total
    avg_emotion = sum(c.payload.get("semantic_features", {}).get("emotion", 0) for c in chunks) / total
    avg_conflict = sum(1 for c in chunks if c.payload.get("semantic_features", {}).get("conflict")) / total
    avg_question = sum(1 for c in chunks if c.payload.get("semantic_features", {}).get("question")) / total
    avg_cta = sum(c.payload.get("semantic_features", {}).get("cta_score", 0) for c in chunks) / total

    # Hook score = maximum hook_score in first 3 chunks (opening)
    opening_chunks = [c for c in chunks if c.payload.get("start_time", 0) <= 15]
    if opening_chunks:
        hook_score = max(c.payload.get("semantic_features", {}).get("hook_score", 0) for c in opening_chunks)
    else:
        hook_score = max(c.payload.get("semantic_features", {}).get("hook_score", 0) for c in chunks) if chunks else 0

    return {
        "hook_score": round(hook_score, 1),
        "avg_humor": round(avg_humor, 1),
        "avg_curiosity": round(avg_curiosity, 1),
        "avg_emotion": round(avg_emotion, 1),
        "avg_conflict": round(avg_conflict * 100, 1),  # percentage
        "avg_question": round(avg_question * 100, 1),
        "avg_cta": round(avg_cta, 1)
    }
def compute_engagement(views, likes, comments):
    if views and views > 0:
        return round((likes + comments) / views * 100, 4)
    return 0.0

def get_videos_by_dataset(dataset_id: str) -> list[dict]:
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
        followers = data.get("follower_count", 0) or 0

        data["engagement_rate"] = compute_engagement(views, likes, comments)
        data["like_ratio"] = round((likes / views) * 100, 4) if views else 0
        data["comment_ratio"] = round((comments / views) * 100, 4) if views else 0
        data["comment_like_ratio"] = round((comments / likes) * 100, 4) if likes else 0
        data["follower_view_ratio"] = round(followers / views, 6) if views else 0
        videos.append(data)

    # Compute rankings within the dataset
    if videos:
        ranked = sorted(videos, key=lambda x: x.get("views", 0), reverse=True)
        for i, v in enumerate(ranked):
            v["rank_by_views"] = i + 1
        ranked = sorted(videos, key=lambda x: x["engagement_rate"], reverse=True)
        for i, v in enumerate(ranked):
            v["rank_by_engagement"] = i + 1
        ranked = sorted(videos, key=lambda x: x.get("likes", 0), reverse=True)
        for i, v in enumerate(ranked):
            v["rank_by_likes"] = i + 1
        ranked = sorted(videos, key=lambda x: x.get("comments", 0), reverse=True)
        for i, v in enumerate(ranked):
            v["rank_by_comments"] = i + 1
    return videos

def get_top_performing_video(dataset_id: str) -> dict | None:
    videos = get_videos_by_dataset(dataset_id)
    if not videos:
        return None
    return max(videos, key=lambda v: v["engagement_rate"])

def get_average_engagement(dataset_id: str) -> float:
    videos = get_videos_by_dataset(dataset_id)
    if not videos:
        return 0.0
    total = sum(v["engagement_rate"] for v in videos)
    return round(total / len(videos), 4)

def rank_videos_by_engagement(dataset_id: str) -> list[dict]:
    videos = get_videos_by_dataset(dataset_id)
    videos.sort(key=lambda v: v["engagement_rate"], reverse=True)
    return videos

def get_platform_summary_for_dataset(dataset_id: str) -> dict:
    videos = get_videos_by_dataset(dataset_id)
    if not videos:
        return {"count": 0}
    total_views = sum(v.get("views", 0) or 0 for v in videos)
    total_likes = sum(v.get("likes", 0) or 0 for v in videos)
    total_comments = sum(v.get("comments", 0) or 0 for v in videos)
    best_engagement = max(videos, key=lambda v: v["engagement_rate"])
    most_views = max(videos, key=lambda v: v.get("views", 0) or 0)
    most_likes = max(videos, key=lambda v: v.get("likes", 0) or 0)
    most_comments = max(videos, key=lambda v: v.get("comments", 0) or 0)
    largest_creator = max(videos, key=lambda v: v.get("follower_count", 0) or 0)
    avg_engagement = get_average_engagement(dataset_id)

    return {
        "count": len(videos),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "best_engagement": best_engagement["title"],
        "best_engagement_value": best_engagement["engagement_rate"],
        "most_views_title": most_views["title"],
        "most_views_value": most_views["views"],
        "most_likes_title": most_likes["title"],
        "most_likes_value": most_likes["likes"],
        "most_comments_title": most_comments["title"],
        "most_comments_value": most_comments["comments"],
        "largest_creator": largest_creator["creator"],
        "largest_creator_followers": largest_creator["follower_count"],
        "average_engagement": avg_engagement
    }

def get_detailed_rankings_for_dataset(dataset_id: str) -> list[dict]:
    return get_videos_by_dataset(dataset_id)

def compare_videos_in_dataset(dataset_id: str, video_id_a: str, video_id_b: str) -> dict:
    conn = get_connection()
    row_a = conn.execute(
        "SELECT * FROM videos WHERE video_id = ? AND dataset_id = ?",
        (video_id_a, dataset_id)
    ).fetchone()
    row_b = conn.execute(
        "SELECT * FROM videos WHERE video_id = ? AND dataset_id = ?",
        (video_id_b, dataset_id)
    ).fetchone()
    conn.close()
    if not row_a or not row_b:
        return {"error": "One or both videos not found in the specified dataset"}

    def extract(row):
        d = dict(row)
        if d.get("hashtags"):
            d["hashtags"] = json.loads(d["hashtags"])
        views = d.get("views") or 0
        likes = d.get("likes") or 0
        comments = d.get("comments") or 0
        followers = d.get("follower_count") or 0
        d["engagement_rate"] = compute_engagement(views, likes, comments)
        d["like_ratio"] = round((likes / views) * 100, 4) if views else 0
        d["comment_ratio"] = round((comments / views) * 100, 4) if views else 0
        d["comment_like_ratio"] = round((comments / likes) * 100, 4) if likes else 0
        d["follower_view_ratio"] = round(followers / views, 6) if views else 0
        return d

    a = extract(row_a)
    b = extract(row_b)

    views_a = a.get("views", 0) or 0
    views_b = b.get("views", 0) or 0
    likes_a = a.get("likes", 0) or 0
    likes_b = b.get("likes", 0) or 0
    comments_a = a.get("comments", 0) or 0
    comments_b = b.get("comments", 0) or 0
    followers_a = a.get("follower_count", 0) or 0
    followers_b = b.get("follower_count", 0) or 0

    reach_multiplier = views_a / views_b if views_b else float('inf')
    engagement_delta = a.get("engagement_rate", 0) - b.get("engagement_rate", 0)
    follower_delta = followers_a - followers_b
    comment_delta = comments_a - comments_b
    like_delta = likes_a - likes_b

    return {
        "video_a": a,
        "video_b": b,
        "differences": {
            "reach_multiplier": round(reach_multiplier, 2) if reach_multiplier != float('inf') else "∞",
            "engagement_delta": round(engagement_delta, 4),
            "follower_delta": follower_delta,
            "comment_delta": comment_delta,
            "like_delta": like_delta
        }
    }