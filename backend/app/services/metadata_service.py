from app.services.youtube_service import YouTubeService
from app.services.instagram_service import InstagramService
from app.core.logger import logger

class MetadataService:
    def __init__(self):
        self.youtube = YouTubeService()
        self.instagram = InstagramService()

    def collect_all(self, youtube_url: str, instagram_url: str) -> dict:
        """
        Gather metadata from both platforms.
        Returns a dict with keys 'youtube' and 'instagram'.
        """
        logger.info("Collecting metadata for both URLs")
        youtube_data = self.youtube.get_metadata(youtube_url)
        instagram_data = self.instagram.get_metadata(instagram_url)

        return {
            "youtube": youtube_data,
            "instagram": instagram_data,
        }