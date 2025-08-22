from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.schemas.menu import Menu
from app.schemas.nutrition import Nutrition
from app.db.session import get_db
from app.crud import get_menu_by_food_code, get_nutrition_by_food_code, get_menus
from app.models.menu import Menu as DBMenu

router = APIRouter()

@router.get("/menu/search", response_model=List[Menu])
def search_menu(q: str, db: Session = Depends(get_db)):
    print(f"DEBUG: search_menu called with q={q}") # Debug print
    # Basic search by std_name or food_code
    menus = db.query(DBMenu).filter(
        (DBMenu.std_name.ilike(f"%{q}%")) | 
        (DBMenu.food_code.ilike(f"%{q}%"))
    ).all()
    return menus

@router.get("/menu/{food_code}", response_model=Menu)
def get_menu(food_code: str, db: Session = Depends(get_db)):
    menu = get_menu_by_food_code(db, food_code=food_code)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu

@router.get("/menu/{food_code}/nutrition", response_model=Nutrition)
def get_nutrition(food_code: str, db: Session = Depends(get_db), portion_g: Optional[float] = Query(None, gt=0)):
    nutrition = get_nutrition_by_food_code(db, food_code=food_code)
    if not nutrition:
        raise HTTPException(status_code=404, detail="Nutrition not found")

    if portion_g and nutrition.energy_kcal:
        # Scale nutrition values based on portion_g
        scale_factor = portion_g / 100.0  # Assuming nutrition values are per 100g
        nutrition.energy_kcal *= scale_factor
        nutrition.water_g = (nutrition.water_g or 0) * scale_factor
        nutrition.protein_g = (nutrition.protein_g or 0) * scale_factor
        nutrition.fat_g = (nutrition.fat_g or 0) * scale_factor
        nutrition.carb_g = (nutrition.carb_g or 0) * scale_factor
        nutrition.sugars_g = (nutrition.sugars_g or 0) * scale_factor
        nutrition.fiber_g = (nutrition.fiber_g or 0) * scale_factor
        nutrition.sodium_mg = (nutrition.sodium_mg or 0) * scale_factor

    return nutrition

# Removed similar endpoint as it requires a more complex recommendation engine.
# @router.get("/menu/{menu_id}/similar", response_model=List[Menu])
# def similar(menu_id: str, request: Request, k: int = 5):
#     catalog = request.app.state.catalog
#     return [Menu(**m) for m in catalog.similar(menu_id, k=k)]