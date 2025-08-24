from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class Profile(BaseModel):
    user_id: str
    name: Optional[str] = None
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None   # {"carb_g":250.0,"protein_g":150.0,"fat_g":44.0}
    activity_level: Optional[str] = None             # "low","mid","high"
    exclude_allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    like_cuisines: Optional[List[str]] = None
    dislike_items: Optional[List[str]] = None
    is_completed: Optional[bool] = False  # boolean 필드 추가

class UpdateProfile(BaseModel):
    sex: Optional[str] = None # 성별 필드 추가
    age: Optional[int] = Field(None, ge=0) # 나이 필드 추가
    daily_kcal_goal: Optional[int] = Field(None, ge=0)
    macro_ratio: Optional[Dict[str, float]] = None
    activity_level: Optional[str] = None
    exclude_allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    like_cuisines: Optional[List[str]] = None
    dislike_items: Optional[List[str]] = None
    is_completed: Optional[bool] = None  # boolean 필드 추가
