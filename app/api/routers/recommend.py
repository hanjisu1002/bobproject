from fastapi import APIRouter, Depends, Query, Request, HTTPException
from typing import Optional, List
from app.utils.deps import get_current_user
from app.schemas.reco import RecommendationResponse, RecommendationItem
from app.schemas.nutrition import Nutrition
from app.schemas.menu import Menu
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.crud import profile as profile_crud, food_log as food_log_crud
from datetime import date, datetime, time
import json

router = APIRouter()

@router.get("/recommendations", response_model=RecommendationResponse)
def recommend(request: Request,
              meal: Optional[str] = Query(None),
              user=Depends(get_current_user),
              db: Session = Depends(get_db)):
    user_id = user["user_id"]
    db_profile, db_preferences = profile_crud.get_profile(db, user_id)

    if not db_profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please complete your profile first.")

    # 1. Calculate Daily Goals
    daily_kcal_goal = db_profile.daily_kcal_target if db_profile.daily_kcal_target else 2000
    macro_ratio = json.loads(db_profile.macro_json) if db_profile.macro_json else {"carb": 0.5, "protein": 0.3, "fat": 0.2}

    daily_carb_g = (daily_kcal_goal * macro_ratio.get("carb", 0)) / 4 if macro_ratio.get("carb") else 0
    daily_protein_g = (daily_kcal_goal * macro_ratio.get("protein", 0)) / 4 if macro_ratio.get("protein") else 0
    daily_fat_g = (daily_kcal_goal * macro_ratio.get("fat", 0)) / 9 if macro_ratio.get("fat") else 0

    # 2. Calculate Consumed Nutrients for today
    today = date.today()
    food_logs = food_log_crud.get_food_logs_by_user_and_date(db, user_id, today)

    consumed_kcal = 0.0
    consumed_carb = 0.0
    consumed_protein = 0.0
    consumed_fat = 0.0

    catalog = request.app.state.catalog

    for log_entry in food_logs:
        menu_data = catalog.menu_by_id.get(log_entry.menu_id)
        if menu_data:
            nut_dict = catalog.get_nutrition_scaled(log_entry.menu_id, portion_g=log_entry.portion_g)
            if nut_dict:
                consumed_kcal += nut_dict.get("kcal", 0.0)
                consumed_carb += nut_dict.get("carb", 0.0)
                consumed_protein += nut_dict.get("protein", 0.0)
                consumed_fat += nut_dict.get("fat", 0.0)

    # 3. Calculate Remaining Budget
    remaining_kcal = max(0.0, daily_kcal_goal - consumed_kcal)
    remaining_carb = max(0.0, daily_carb_g - consumed_carb)
    remaining_protein = max(0.0, daily_protein_g - consumed_protein)
    remaining_fat = max(0.0, daily_fat_g - consumed_fat)

    # 4. Identify Deficient Nutrients (simple approach: highest remaining percentage of daily goal)
    deficient_macros = {}
    if daily_carb_g > 0: deficient_macros["carb"] = remaining_carb / daily_carb_g
    if daily_protein_g > 0: deficient_macros["protein"] = remaining_protein / daily_protein_g
    if daily_fat_g > 0: deficient_macros["fat"] = remaining_fat / daily_fat_g

    # Sort by highest remaining percentage to prioritize
    sorted_deficient_macros = sorted(deficient_macros.items(), key=lambda item: item[1], reverse=True)

    # 5. Filter Food Catalog & Score
    recommendation_items = []
    all_menu_items = catalog.menu_by_id.values()

    # User preferences for filtering
    exclude_allergens = json.loads(db_preferences.exclude_allergens_json) if db_preferences and db_preferences.exclude_allergens_json else []
    dislike_items = json.loads(db_preferences.dislike_items_json) if db_preferences and db_preferences.dislike_items_json else []
    diet_types = json.loads(db_preferences.diet_types_json) if db_preferences and db_preferences.diet_types_json else []
    like_cuisines = json.loads(db_preferences.like_cuisines_json) if db_preferences and db_preferences.like_cuisines_json else []

    for m in all_menu_items:
        menu = Menu(**m)

        # Basic filtering based on user preferences
        if menu.std_name in dislike_items: # Assuming std_name is what user dislikes
            continue
        # TODO: Implement allergen and diet type filtering if menu items have these attributes

        nut_dict = catalog.get_nutrition_scaled(menu.id, portion_g=None) # Get nutrition for a standard portion
        if not nut_dict:
            continue
        nut = Nutrition(**nut_dict)

        # Filter out items that exceed remaining kcal or any macro (even if deficient)
        if nut.kcal > remaining_kcal or nut.carb > remaining_carb or nut.protein > remaining_protein or nut.fat > remaining_fat:
            continue

        score = 0.0

        # Score based on contribution to deficient macros
        for macro, _ in sorted_deficient_macros:
            if macro == "carb" and nut.carb > 0: score += nut.carb * 0.1 # Arbitrary weight
            if macro == "protein" and nut.protein > 0: score += nut.protein * 0.2 # Protein often more critical
            if macro == "fat" and nut.fat > 0: score += nut.fat * 0.05 # Arbitrary weight
        
        # Score based on calorie fit (closer to remaining_kcal is better, without exceeding)
        if remaining_kcal > 0:
            kcal_fit_score = 1 - abs(nut.kcal - remaining_kcal) / remaining_kcal
            score += max(0, kcal_fit_score) * 0.5 # Arbitrary weight

        # Score based on liked cuisines (if menu has a cuisine attribute)
        # TODO: Add cuisine attribute to Menu model and data
        # if menu.cuisine in like_cuisines: score += 1.0

        if score > 0: # Only add items with a positive score
            recommendation_items.append(RecommendationItem(menu=menu, nutrition=nut, score=score))

    # Sort and return top N
    recommendation_items.sort(key=lambda x: x.score, reverse=True)
    return RecommendationResponse(items=recommendation_items[:10])
