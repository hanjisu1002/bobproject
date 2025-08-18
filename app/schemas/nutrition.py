from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NutritionBase(BaseModel):
    food_code: str
    energy_kcal: Optional[float] = None
    water_g: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carb_g: Optional[float] = None
    sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None

class NutritionCreate(NutritionBase):
    pass

class NutritionUpdate(NutritionBase):
    food_code: Optional[str] = None

class Nutrition(NutritionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True