import os
import sys
import pandas as pd
import re
import logging

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.menu import Menu
from app.models.nutrition import Nutrition
from app.models.base import Base
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_csv(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"CSV not found in candidates: {candidates}")

def read_csv(path):
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV with all attempted encodings: {path}")

def clean_code(x):
    s = str(x).strip()
    s = re.sub(r"\.0+$", "", s)
    return s

def to_num(v):
    return None if pd.isna(v) or v == 'N/A' else float(v)

def init_db(db: Session):
    """
    데이터베이스 테이블을 생성합니다.
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

def load_seed_data(db: Session):
    """
    CSV 파일로부터 메뉴 및 영양 정보를 읽어 데이터베이스에 적재합니다.
    """
    foods_path = find_csv([settings.FOODS_CSV])
    nutr_path = find_csv([settings.NUTRIENTS_CSV])

    df_foods = read_csv(foods_path)
    df_nutr = read_csv(nutr_path)

    # 데이터 정규화
    df_foods["food_code"] = df_foods["food_code"].map(clean_code)
    df_foods["slug"] = df_foods["slug"].astype(str).str.strip()
    df_foods["std_name"] = df_foods["food_name"].astype(str).str.strip()
    df_foods["category"] = df_foods["category_name"].astype(str).str.strip()

    df_nutr["food_code"] = df_nutr["food_code"].map(clean_code)

    # --- Menu 데이터 적재 (Upsert) ---
    logger.info(f"Upserting {len(df_foods)} rows into 'menu' table...")
    for _, row in df_foods.iterrows():
        existing_menu = db.query(Menu).filter(Menu.food_code == row["food_code"]).first()
        if existing_menu:
            existing_menu.slug = row["slug"]
            existing_menu.std_name = row["std_name"]
            existing_menu.category = row["category"]
        else:
            new_menu = Menu(
                food_code=row["food_code"],
                slug=row["slug"],
                std_name=row["std_name"],
                category=row["category"],
            )
            db.add(new_menu)
    db.commit()
    logger.info("Menu data upserted.")

    # --- Nutrition 데이터 적재 ---
    # 먼저 기존 Nutrition 데이터 모두 삭제 (중복 방지)
    logger.info("Deleting existing nutrition data...")
    db.query(Nutrition).delete()
    db.commit()

    existing_codes = {m.food_code for m in db.query(Menu.food_code).all()}
    
    nutr_to_add = []
    skipped_count = 0
    logger.info(f"Inserting {len(df_nutr)} rows into 'nutrition' table...")
    for _, row in df_nutr.iterrows():
        if row["food_code"] not in existing_codes:
            skipped_count += 1
            continue
        
        nutr_to_add.append(
            Nutrition(
                food_code=row["food_code"],
                energy_kcal=to_num(row.get("energy_kcal")),
                water_g=to_num(row.get("water_g")),
                protein_g=to_num(row.get("protein_g")),
                fat_g=to_num(row.get("fat_g")),
                carb_g=to_num(row.get("carb_g")),
                sugars_g=to_num(row.get("sugars_g")),
                fiber_g=to_num(row.get("fiber_g")),
                sodium_mg=to_num(row.get("sodium_mg")),
            )
        )

    if nutr_to_add:
        db.bulk_save_objects(nutr_to_add)
        db.commit()

    logger.info("✅ Seed data loaded successfully!")
    logger.info(f"  - Menu rows upserted: {len(df_foods)}")
    logger.info(f"  - Nutrition rows inserted: {len(nutr_to_add)} (skipped {skipped_count} rows lacking a corresponding menu entry)")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        # 1. (선택) DB 테이블 초기화
        init_db(db)
        
        # 2. 시드 데이터 적재
        load_seed_data(db)
    finally:
        db.close()