from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class Profile(BaseModel):
    user_id: str
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None   # {"carb":0.5,"protein":0.3,"fat":0.2}
    activity_level: Optional[str] = None             # "low","mid","high"
    exclude_allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    like_cuisines: Optional[List[str]] = None
    dislike_items: Optional[List[str]] = None
    is_completed: Optional[bool] = False  # boolean 필드 추가

class UpdateProfile(BaseModel):
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None
    activity_level: Optional[str] = None
    exclude_allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    like_cuisines: Optional[List[str]] = None
    dislike_items: Optional[List[str]] = None
    is_completed: Optional[bool] = None  # boolean 필드 추가
