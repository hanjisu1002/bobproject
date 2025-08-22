from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    reco_id: Optional[str] = None
    score: int
    message: Optional[str] = None

class FeedbackResponse(FeedbackCreate):
    id: int
    user_id: int
    ts: datetime

    class Config:
        from_attributes = True
