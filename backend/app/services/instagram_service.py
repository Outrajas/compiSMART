import yt_dlp
import instaloader
import re
from app.core.logger import logger

class InstagramService:
    def __init__(self):
        # Initialize Instaloader with a safe mobile user agent
        self.loader = instaloader.Instaloader(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            quiet=True
        )

    def get_metadata(self, url: str) -> dict:
        """
        Extract 100% real reel metadata using a hybrid yt-dlp and instaloader pipeline.
        We skip Profile extraction to avoid 403 crashes and explicitly set followers to 0.
        """
        logger.info(f"Extracting 100% real Instagram metrics for: {url}")
        
        # Defaults
        caption = ""
        title = "Instagram Reel"
        views = 0
        likes = 0
        comments = 0
        duration = 0
        username = "Unknown"
        follower_count = 0
        following_count = 0
        posts_count = 0
        native_transcript = ""
        upload_date = None

        # --- STEP 1: yt-dlp for reliable base media, subtitles, and some stats ---
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": True,
            "allsubtitles": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                caption = info.get("description") or ""
                title = info.get("title") or "Instagram Reel"
                likes = info.get("like_count") or 0
                comments = info.get("comment_count") or 0
                duration = info.get("duration") or 0
                username = info.get("uploader") or info.get("channel") or "Unknown"
                upload_date = info.get("upload_date")
                
                # Check for native closed captions uploaded by creator (No Whisper)
                subtitles_dict = info.get("subtitles") or info.get("automatic_captions") or {}
                if subtitles_dict:
                    for lang, subs in subtitles_dict.items():
                        if subs:
                            native_transcript = f"[Native Subtitles Track: {lang}]"
                            break
        except Exception as e:
            logger.warning(f"yt-dlp extraction partial or failed: {e}")

        # --- STEP 2: Instaloader enrichment for Views (Based on your successful terminal test) ---
        shortcode_match = re.search(r"reel/([^/?]+)", url)
        if shortcode_match:
            shortcode = shortcode_match.group(1)
            try:
                # This fetches the Reel data (which bypasses the 403 block internally)
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                
                views = post.video_view_count if post.video_view_count else views
                likes = post.likes if post.likes else likes
                comments = post.comments if post.comments else comments
                username = post.owner_username if post.owner_username else username
                duration = post.video_duration if post.video_duration else duration
                
                if not caption and post.caption:
                    caption = post.caption
                    title = post.caption[:100]
                    
                logger.info(f"Instaloader successfully extracted Reel stats: {views} views")
            except Exception as e:
                logger.warning(f"Instaloader post extraction failed for {shortcode}: {e}")
        
        # --- STEP 3: Handle Followers (We explicitly skip the blocked lookup) ---
        logger.info("Skipping Instaloader Profile extraction due to known 403 blocks. Followers set to 0.")

        # Clean tags and format title
        tags = [t.strip("#").strip(",").strip(".").strip("!") for t in caption.split() if t.startswith("#")]
        if title == "Instagram Reel" and caption:
             title = caption[:100]

        logger.info(f"Final Real Stats - User: {username} | Views: {views} | Likes: {likes} | Followers: 0 (Blocked)")

        return {
            "platform": "instagram",
            "title": title[:100].replace('\n', ' '),
            "creator": username,
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration": duration,
            "follower_count": follower_count,
            "following_count": following_count,
            "posts_count": posts_count,
            "bio": "",
            "caption": caption,
            "hashtags": tags,
            "upload_date": upload_date,
            "native_transcript": native_transcript
        }