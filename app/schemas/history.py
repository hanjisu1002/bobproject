from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserHistoryCreate(BaseModel):
    menu_id: int
    action: str

class UserHistoryResponse(UserHistoryCreate):
    id: int
    user_id: int
    ts: datetime

    class Config:
        from_attributes = True
