from app.core.logger import logger

class InstagramService:
    def get_metadata(self, url: str) -> dict:
        """
        Currently returns a minimal placeholder.
        Full Instagram scraping will be added in a later phase.
        """
        logger.info(f"Instagram metadata stub for {url}")
        # TODO: implement real extraction (requires login or public API)
        return {
            "platform": "instagram",
            "creator": None,
            "views": None,
            "likes": None,
            "comments": None,
            "follower_count": None,
            "hashtags": [],
            "upload_date": None,
            "duration": None,
        }