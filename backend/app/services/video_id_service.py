from app.db.sqlite import get_connection

def generate_video_id(platform: str) -> str:
    """Generate next ID like YT_001 or IG_001."""
    prefix = "YT_" if platform == "youtube" else "IG_"
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(video_id) FROM videos WHERE platform = ?", (platform,)
    ).fetchone()
    conn.close()
    max_id = row[0]
    if max_id and max_id.startswith(prefix):
        num = int(max_id[len(prefix):])
        next_num = num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"