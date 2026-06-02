import yt_dlp
from app.core.logger import logger

class YouTubeService:
    def get_metadata(self, url: str) -> dict:
        """
        Extract metadata from a YouTube video using yt-dlp.
        Returns a dictionary with keys: title, creator, views, likes,
        comments, duration, upload_date, hashtags, follower_count.
        follower_count is extracted from the channel if available.
        """
        logger.info(f"Extracting YouTube metadata for {url}")

        ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,

    # COOKIE FIX
    "cookiefile": "/app/cookies.txt",

    # Browser-like headers
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }
}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # yt-dlp returns different structures for playlists/videos
            # We assume it's a single video
            metadata = {
                "title": info.get("title"),
                "creator": info.get("uploader"),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "comments": info.get("comment_count"),
                "duration": info.get("duration"),          # in seconds
                "upload_date": info.get("upload_date"),    # YYYYMMDD
                "hashtags": info.get("tags") or [],        # list of tags
                "follower_count": info.get("channel_follower_count"),
            }

            # Clean None values (optional, keep as None if not found)
            logger.info(f"YouTube metadata extracted: {metadata.get('title')}")
            return metadata

        except Exception as e:
            logger.error(f"YouTube extraction failed: {e}")
            raise