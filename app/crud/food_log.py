from sqlalchemy.orm import Session
from app.models.user_food_log import UserFoodLog
from app.models.menu import Menu
from app.models.nutrition import Nutrition
from app.schemas.food_log import FoodLogCreate, FoodLogResponse
from datetime import date, datetime, time
import pytz

def create_food_log(db: Session, user_id: int, food_log: FoodLogCreate) -> UserFoodLog:
    db_food_log = UserFoodLog(**food_log.model_dump(), user_id=user_id)
    db.add(db_food_log)
    db.commit()
    db.refresh(db_food_log)
    return db_food_log

def _get_food_log_with_details(db: Session, query):
    results = query.join(Menu, UserFoodLog.menu_id == Menu.menu_id)
    results = results.outerjoin(Nutrition, Menu.food_code == Nutrition.food_code)
    results = results.all()

    food_logs_with_details = []
    for log, menu, nutrition in results:
        kcal = None
        macro = None
        if nutrition and log.portion_g:
            # Assuming nutrition values are per 100g
            scale = log.portion_g / 100.0
            kcal = nutrition.energy_kcal * scale if nutrition.energy_kcal else None
            macro = {
                "carb_g": nutrition.carb_g * scale if nutrition.carb_g else 0,
                "protein_g": nutrition.protein_g * scale if nutrition.protein_g else 0,
                "fat_g": nutrition.fat_g * scale if nutrition.fat_g else 0,
            }

        food_logs_with_details.append(FoodLogResponse(
            id=log.id,
            user_id=log.user_id,
            consumed_at=log.consumed_at,
            menu_id=log.menu_id,
            portion_g=log.portion_g,
            meal_type=log.meal_type,
            menu_name=menu.std_name if menu else None,
            kcal=kcal,
            macro=macro
        ))
    return food_logs_with_details

def get_food_logs_by_user_and_date(db: Session, user_id: int, target_date: date) -> list[FoodLogResponse]:
    KST = pytz.timezone('Asia/Seoul')
    
    # Create timezone-aware KST datetimes for the start and end of the target_date
    start_of_day_kst = KST.localize(datetime.combine(target_date, time.min))
    end_of_day_kst = KST.localize(datetime.combine(target_date, time.max))

    # Convert KST datetimes to UTC for database query
    start_of_day_utc = start_of_day_kst.astimezone(pytz.utc)
    end_of_day_utc = end_of_day_kst.astimezone(pytz.utc)

    query = db.query(UserFoodLog, Menu, Nutrition).filter(
        UserFoodLog.user_id == user_id,
        UserFoodLog.consumed_at >= start_of_day_utc,
        UserFoodLog.consumed_at <= end_of_day_utc
    )
    return _get_food_log_with_details(db, query)

def get_all_food_logs_by_user(db: Session, user_id: int) -> list[FoodLogResponse]:
    query = db.query(UserFoodLog, Menu, Nutrition).filter(
        UserFoodLog.user_id == user_id
    )
    return _get_food_log_with_details(db, query)