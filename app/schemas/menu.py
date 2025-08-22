from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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