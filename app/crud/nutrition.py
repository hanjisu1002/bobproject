from sqlalchemy.orm import Session
from app.models.nutrition import Nutrition
from app.schemas.nutrition import NutritionCreate, NutritionUpdate

def get_nutrition(db: Session, nutrition_id: int) -> Nutrition | None:
    return db.query(Nutrition).filter(Nutrition.id == nutrition_id).first()

def get_nutrition_by_food_code(db: Session, food_code: str) -> Nutrition | None:
    return db.query(Nutrition).filter(Nutrition.food_code == food_code).first()

def create_nutrition(db: Session, nutrition: NutritionCreate) -> Nutrition:
    db_nutrition = Nutrition(**nutrition.model_dump())
    db.add(db_nutrition)
    db.commit()
    db.refresh(db_nutrition)
    return db_nutrition

def update_nutrition(db: Session, nutrition_id: int, nutrition: NutritionUpdate) -> Nutrition | None:
    db_nutrition = db.query(Nutrition).filter(Nutrition.id == nutrition_id).first()
    if db_nutrition:
        update_data = nutrition.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_nutrition, key, value)
        db.commit()
        db.refresh(db_nutrition)
    return db_nutrition

def delete_nutrition(db: Session, nutrition_id: int):
    db_nutrition = db.query(Nutrition).filter(Nutrition.id == nutrition_id).first()
    if db_nutrition:
        db.delete(db_nutrition)
        db.commit()
    return db_nutrition
