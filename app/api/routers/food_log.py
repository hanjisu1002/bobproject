from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.schemas.food_log import FoodLogCreate, FoodLogResponse
from app.utils.deps import get_current_user
from app.db.session import get_db
from app.crud import food_log as food_log_crud
from datetime import date

router = APIRouter()

@router.post("/food_logs", response_model=FoodLogResponse, status_code=status.HTTP_201_CREATED)
def create_food_log_entry(
    food_log: FoodLogCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 음식 섭취 기록을 생성합니다.
    """
    user_id = user["user_id"]
    return food_log_crud.create_food_log(db, user_id=user_id, food_log=food_log)

@router.get("/food_logs/by_date", response_model=list[FoodLogResponse])
def get_food_logs_by_date_endpoint(
    target_date: date = Query(..., description="조회할 날짜 (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 날짜의 사용자 음식 섭취 기록을 조회합니다.
    """
    user_id = user["user_id"]
    return food_log_crud.get_food_logs_by_user_and_date(db, user_id=user_id, target_date=target_date)

@router.get("/food_logs/all", response_model=list[FoodLogResponse])
def get_all_food_logs_endpoint(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 모든 음식 섭취 기록을 조회합니다.
    """
    user_id = user["user_id"]
    return food_log_crud.get_all_food_logs_by_user(db, user_id=user_id)
