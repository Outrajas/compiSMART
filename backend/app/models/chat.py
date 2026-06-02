# backend/app/models/chat.py

from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    platform: str       # "youtube" or "instagram" (or "both" if cross-platform)
    dataset_id: str
    question: str