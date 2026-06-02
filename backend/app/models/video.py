# backend/app/models/video.py

from pydantic import BaseModel, HttpUrl, field_validator
from typing import List

class VideoInput(BaseModel):
    youtube_urls: List[HttpUrl] = []
    instagram_urls: List[HttpUrl] = []

    @field_validator('youtube_urls', 'instagram_urls')
    def check_at_least_one(cls, v, info):
        # validation is done later in the route handler
        return v