from app.db.sqlite import get_connection
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import json

def compute_engagement(views, likes, comments):
    if views and views > 0:
        return round((likes + comments) / views * 100, 4)
    return 0.0

def get_videos_by_dataset(dataset_id: str, video_ids: list[str] = None) -> list[dict]:
    conn = get_connection()
    
    # Query matching active links mapping tables to preserve isolated environments
    if video_ids is not None:
        if not video_ids:
            conn.close()
            return []
        placeholders = ",".join(["?"] * len(video_ids))
        query = f"SELECT * FROM videos WHERE video_id IN ({placeholders})"
        rows = conn.execute(query, video_ids).fetchall()
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
        followers = data.get("follower_count", 0) or 0

        data["engagement_rate"] = compute_engagement(views, likes, comments)
        data["like_ratio"] = round((likes / views) * 100, 4) if views else 0
        data["comment_ratio"] = round((comments / views) * 100, 4) if views else 0
        data["comment_like_ratio"] = round((comments / likes) * 100, 4) if likes else 0
        data["follower_view_ratio"] = round(followers / views, 6) if views else 0
        data["views_per_follower"] = round(views / followers, 2) if followers else None

        data["likes_per_1000_views"] = round((likes / views) * 1000, 2) if views else 0.0
        data["comments_per_1000_views"] = round((comments / views) * 1000, 2) if views else 0.0

        if data["views_per_follower"] is not None:
            data["engagement_efficiency"] = round(data["engagement_rate"] * data["views_per_follower"], 2)
        else:
            data["engagement_efficiency"] = None

        videos.append(data)

    if videos:
        for metric in ["views", "engagement_rate", "likes", "comments"]:
            ranked = sorted(videos, key=lambda x: x.get(metric, 0) or 0, reverse=True)
            for i, v in enumerate(ranked):
                v[f"rank_by_{metric}"] = i + 1

    return videos

def get_top_performing_video(dataset_id: str, video_ids: list[str] = None) -> dict | None:
    videos = get_videos_by_dataset(dataset_id, video_ids)
    if not videos:
        return None
    return max(videos, key=lambda v: v["engagement_rate"])

def get_average_engagement(dataset_id: str, video_ids: list[str] = None) -> float:
    videos = get_videos_by_dataset(dataset_id, video_ids)
    if not videos:
        return 0.0
    total = sum(v["engagement_rate"] for v in videos)
    return round(total / len(videos), 4)

def rank_videos_by_engagement(dataset_id: str, video_ids: list[str] = None) -> list[dict]:
    videos = get_videos_by_dataset(dataset_id, video_ids)
    videos.sort(key=lambda v: v["engagement_rate"], reverse=True)
    return videos

def get_platform_summary_for_dataset(dataset_id: str, video_ids: list[str] = None) -> dict:
    videos = get_videos_by_dataset(dataset_id, video_ids)
    if not videos:
        return {
            "count": 0, "total_views": 0, "total_likes": 0, "total_comments": 0,
            "best_engagement": "None", "best_engagement_value": 0.0,
            "most_views_title": "None", "most_views_value": 0,
            "most_likes_title": "None", "most_likes_value": 0,
            "most_comments_title": "None", "most_comments_value": 0,
            "largest_creator": "None", "largest_creator_followers": 0,
            "average_engagement": 0.0, "outlier_videos": [],
            "best_views_per_follower_title": "None", "best_views_per_follower_value": 0.0
        }

    total_views = sum(v.get("views", 0) or 0 for v in videos)
    total_likes = sum(v.get("likes", 0) or 0 for v in videos)
    total_comments = sum(v.get("comments", 0) or 0 for v in videos)

    best_engagement = max(videos, key=lambda v: v["engagement_rate"])
    most_views = max(videos, key=lambda v: v.get("views", 0) or 0)
    most_likes = max(videos, key=lambda v: v.get("likes", 0) or 0)
    most_comments = max(videos, key=lambda v: v.get("comments", 0) or 0)
    largest_creator = max(videos, key=lambda v: v.get("follower_count", 0) or 0)

    avg_engagement = get_average_engagement(dataset_id, video_ids)

    vpf_values = [v["views_per_follower"] for v in videos if v["views_per_follower"] is not None]
    median_vpf = sorted(vpf_values)[len(vpf_values) // 2] if vpf_values else 1.0
    outliers = [v for v in videos if v["views_per_follower"] and v["views_per_follower"] > 10 * median_vpf]
    
    valid_vpf_videos = [v for v in videos if v["views_per_follower"] is not None]
    if valid_vpf_videos:
        best_vpf = max(valid_vpf_videos, key=lambda v: v["views_per_follower"])
        best_vpf_title = best_vpf["title"]
        best_vpf_val = best_vpf["views_per_follower"]
    else:
        best_vpf_title = "None"
        best_vpf_val = 0.0

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
        "average_engagement": avg_engagement,
        "outlier_videos": [v["title"] for v in outliers],
        "best_views_per_follower_title": best_vpf_title,
        "best_views_per_follower_value": best_vpf_val,
    }

def get_detailed_rankings_for_dataset(dataset_id: str, video_ids: list[str] = None) -> list[dict]:
    return get_videos_by_dataset(dataset_id, video_ids)

def compare_videos_in_dataset(dataset_id: str, video_id_a: str, video_id_b: str) -> dict:
    conn = get_connection()
    row_a = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id_a,)).fetchone()
    row_b = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id_b,)).fetchone()
    conn.close()

    if not row_a or not row_b:
        return {"error": "One or both videos not found"}

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
        d["views_per_follower"] = round(views / followers, 2) if followers else None
        d["likes_per_1000_views"] = round((likes / views) * 1000, 2) if views else 0.0
        d["comments_per_1000_views"] = round((comments / views) * 1000, 2) if views else 0.0
        return d

    a = extract(row_a)
    b = extract(row_b)

    diff = {
        "reach_multiplier": round(a.get("views", 0) / b.get("views", 1), 2) if b.get("views") else 0,
        "engagement_delta": round(a.get("engagement_rate", 0) - b.get("engagement_rate", 0), 4),
        "follower_delta": (a.get("follower_count") or 0) - (b.get("follower_count") or 0),
        "comment_delta": (a.get("comments") or 0) - (b.get("comments") or 0),
        "like_delta": (a.get("likes") or 0) - (b.get("likes") or 0),
        "views_per_follower_a": a["views_per_follower"],
        "views_per_follower_b": b["views_per_follower"],
    }

    return {"video_a": a, "video_b": b, "differences": diff}

def get_video_semantic_profile(video_id: str, dataset_id: str) -> dict:
    client = QdrantClient(host="localhost", port=6333)
    
    # Isolate context strictly to matching parameters
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
        # Fallback filter matching just the video_id row if dataset links shifted
        results = client.scroll(
            collection_name="video_chunks",
            scroll_filter=Filter(must=[
                FieldCondition(key="video_id", match=MatchValue(value=video_id))
            ]),
            limit=1000
        )
        chunks = results[0]
        if not chunks:
            return {}

    total = len(chunks)
    features_list = [c.payload.get("semantic_features", {}) for c in chunks]

    avg = lambda key: round(sum(f.get(key, 0) for f in features_list) / total, 1) if total else 0.0
    avg_bool = lambda key: round(sum(1 for f in features_list if f.get(key)) / total * 100, 1) if total else 0.0

    opening = [c for c in chunks if c.payload.get("start_time", 0) <= 15]
    hook = max((c.payload.get("semantic_features", {}).get("hook_score", 0) for c in opening), default=0)
    if not opening and chunks:
        hook = max((c.payload.get("semantic_features", {}).get("hook_score", 0) for c in chunks))

    conn = get_connection()
    row = conn.execute("SELECT duration FROM videos WHERE video_id = ?", (video_id,)).fetchone()
    conn.close()
    
    duration = row["duration"] if row and row["duration"] else 0
    last_end = max(c.payload.get("end_time", 0) for c in chunks) if chunks else 0
    coverage = round((last_end / duration) * 100, 1) if duration else 0

    breakdown = {
        "question": avg_bool("question"),
        "conflict": avg_bool("conflict"),
        "emotion": avg("emotion"),
        "humor": avg("humor_score"),
        "curiosity": avg("curiosity_score"),
        "cta": avg("cta_score"),
    }

    return {
        "hook_score": round(hook, 1),
        "avg_humor": avg("humor_score"),
        "avg_curiosity": avg("curiosity_score"),
        "avg_emotion": avg("emotion"),
        "avg_conflict": avg_bool("conflict"),
        "avg_question": avg_bool("question"),
        "avg_cta": avg("cta_score"),
        "transcript_coverage": coverage,
        "total_segments": total,
        "hook_breakdown": breakdown,
    }

def get_semantic_profiles_for_dataset(dataset_id: str, video_ids: list[str] = None) -> list[dict]:
    videos = get_videos_by_dataset(dataset_id, video_ids)
    profiles = []
    for v in videos:
        profile = get_video_semantic_profile(v["video_id"], dataset_id)
        if profile:
            profile["video_id"] = v["video_id"]
            profile["title"] = v.get("title", "")
            profiles.append(profile)
    return profiles