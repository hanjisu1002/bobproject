from pydantic import BaseModel
from typing import List, Optional

class Preferences(BaseModel):
    allergens_exclude: List[str] = []
    diet_type: Optional[str] = None      # "vegan","halal","none"
    like_foods: List[str] = []
    dislike_foods: List[str] = []
    like_countries: List[str] = []
    dislike_countries: List[str] = []
