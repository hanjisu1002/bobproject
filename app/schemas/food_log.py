from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FoodLogBase(BaseModel):
    menu_id: int
    portion_g: float
    meal_type: Optional[str] = None

class FoodLogCreate(FoodLogBase):
    pass

class FoodLogResponse(FoodLogBase):
    id: int
    user_id: int
    consumed_at: datetime
    menu_name: Optional[str] = None
    kcal: Optional[float] = None
    macro: Optional[dict] = None # {carb: float, protein: float, fat: float}

    class Config:
        from_attributes = True
