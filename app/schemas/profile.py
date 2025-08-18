from pydantic import BaseModel, Field
from typing import Optional, Dict

class Profile(BaseModel):
    user_id: str
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None   # {"carb":0.5,"protein":0.3,"fat":0.2}
    activity_level: Optional[str] = None             # "low","mid","high"

class UpdateProfile(BaseModel):
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None
    activity_level: Optional[str] = None
