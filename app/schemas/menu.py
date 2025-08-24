from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from app.schemas.nutrition import Nutrition # Import Nutrition schema

class MenuBase(BaseModel):
    food_code: str
    slug: str
    std_name: str
    category: Optional[str] = None

class MenuCreate(MenuBase):
    pass

class MenuUpdate(MenuBase):
    food_code: Optional[str] = None
    slug: Optional[str] = None
    std_name: Optional[str] = None

class Menu(MenuBase):
    menu_id: int
    std_name_norm: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# New schema for Menu with Nutrition
class MenuWithNutrition(Menu): # Inherit from Menu
    kcal: Optional[float] = None
    macro: Optional[Dict[str, float]] = None # {carb_g: float, protein_g: float, fat_g: float}