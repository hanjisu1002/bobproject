from sqlalchemy.orm import Session
from app.models.menu import Menu
from app.models.nutrition import Nutrition
from app.schemas.menu import MenuCreate, MenuUpdate
from app.schemas.nutrition import NutritionCreate, NutritionUpdate

def get_menu(db: Session, menu_id: int):
    return db.query(Menu).filter(Menu.menu_id == menu_id).first()

def get_menu_by_food_code(db: Session, food_code: str):
    return db.query(Menu).filter(Menu.food_code == food_code).first()

def get_menus(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Menu).offset(skip).limit(limit).all()

def create_menu(db: Session, menu: MenuCreate):
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

def update_menu(db: Session, menu_id: int, menu: MenuUpdate):
    db_menu = db.query(Menu).filter(Menu.menu_id == menu_id).first()
    if db_menu:
        for key, value in menu.dict(exclude_unset=True).items():
            setattr(db_menu, key, value)
        db.commit()
        db.refresh(db_menu)
    return db_menu

def delete_menu(db: Session, menu_id: int):
    db_menu = db.query(Menu).filter(Menu.menu_id == menu_id).first()
    if db_menu:
        db.delete(db_menu)
        db.commit()
    return db_menu

# Nutrition CRUD operations

def get_nutrition(db: Session, nutrition_id: int):
    return db.query(Nutrition).filter(Nutrition.id == nutrition_id).first()

def get_nutrition_by_food_code(db: Session, food_code: str):
    return db.query(Nutrition).filter(Nutrition.food_code == food_code).first()

def create_nutrition(db: Session, nutrition: NutritionCreate):
    db_nutrition = Nutrition(**nutrition.dict())
    db.add(db_nutrition)
    db.commit()
    db.refresh(db_nutrition)
    return db_nutrition

def update_nutrition(db: Session, nutrition_id: int, nutrition: NutritionUpdate):
    db_nutrition = db.query(Nutrition).filter(Nutrition.id == nutrition_id).first()
    if db_nutrition:
        for key, value in nutrition.dict(exclude_unset=True).items():
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
