from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.schemas.menu import Menu, MenuWithNutrition # Import MenuWithNutrition
from app.schemas.nutrition import Nutrition
from app.db.session import get_db
from app.crud import get_menu_by_food_code, get_nutrition_by_food_code, get_menus
from app.models.menu import Menu as DBMenu
from app.models.nutrition import Nutrition as DBNutrition # Import DBNutrition
from sqlalchemy import distinct # Add this import

router = APIRouter()

# Move this endpoint to be defined BEFORE /menu/{food_code}
@router.get("/menu/categories", response_model=list[str])
def get_unique_categories(db: Session = Depends(get_db)):
    """
    Returns a list of unique categories from the menu table.
    """
    categories = db.query(distinct(DBMenu.category)).order_by(DBMenu.category).all()
    return [c[0] for c in categories if c[0] is not None] # Extract string from tuple and filter None

@router.get("/menu/by_category", response_model=List[MenuWithNutrition]) # Changed response_model
def get_menus_by_category(category: str, db: Session = Depends(get_db)):
    """
    Returns a list of menus belonging to a specific category with nutrition info.
    """
    menus_with_nutrition = db.query(
        DBMenu,
        DBNutrition.energy_kcal,
        DBNutrition.carb_g,
        DBNutrition.protein_g,
        DBNutrition.fat_g
    ).outerjoin(DBNutrition, DBMenu.food_code == DBNutrition.food_code)\
    .filter(DBMenu.category == category).all()

    result = []
    for menu, kcal, carb, protein, fat in menus_with_nutrition:
        macro_dict = {"carb_g": carb, "protein_g": protein, "fat_g": fat} if all(v is not None for v in [carb, protein, fat]) else None
        result.append(MenuWithNutrition(
            food_code=menu.food_code,
            slug=menu.slug,
            std_name=menu.std_name,
            category=menu.category,
            menu_id=menu.menu_id,
            std_name_norm=menu.std_name_norm,
            created_at=menu.created_at,
            updated_at=menu.updated_at,
            kcal=kcal,
            macro=macro_dict
        ))
    return result

@router.get("/menu/search", response_model=List[MenuWithNutrition]) # Changed response_model
def search_menu(q: str, db: Session = Depends(get_db)):
    print(f"DEBUG: search_menu called with q={q}") # Debug print
    # Basic search by std_name or food_code
    menus_with_nutrition = db.query(
        DBMenu,
        DBNutrition.energy_kcal,
        DBNutrition.carb_g,
        DBNutrition.protein_g,
        DBNutrition.fat_g
    ).outerjoin(DBNutrition, DBMenu.food_code == DBNutrition.food_code)\
    .filter(
        (DBMenu.std_name.ilike(f"%{q}%")) | 
        (DBMenu.food_code.ilike(f"%{q}%"))
    ).all()

    result = []
    for menu, kcal, carb, protein, fat in menus_with_nutrition:
        macro_dict = {"carb_g": carb, "protein_g": protein, "fat_g": fat} if all(v is not None for v in [carb, protein, fat]) else None
        result.append(MenuWithNutrition(
            food_code=menu.food_code,
            slug=menu.slug,
            std_name=menu.std_name,
            category=menu.category,
            menu_id=menu.menu_id,
            std_name_norm=menu.std_name_norm,
            created_at=menu.created_at,
            updated_at=menu.updated_at,
            kcal=kcal,
            macro=macro_dict
        ))
    return result

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