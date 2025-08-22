from pydantic import BaseModel
from typing import List, Optional
from app.schemas.menu import Menu
from app.schemas.nutrition import Nutrition

class RecommendationItem(BaseModel):
    menu: Menu
    nutrition: Optional[Nutrition] = None
    score: float = 1.0

class RecommendationResponse(BaseModel):
    items: List[RecommendationItem]
