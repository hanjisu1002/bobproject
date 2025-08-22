from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.schemas.profile import Profile, UpdateProfile
from app.schemas.preferences import Preferences
from app.utils.deps import get_current_user
from app.db.session import get_db
from app.crud import profile as profile_crud, user as user_crud
from app.models.user_profile import UserProfile
import json

router = APIRouter()

@router.get("/profile", response_model=Profile)
def get_profile(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인된 사용자의 프로필을 반환합니다."""
    user_id = user["user_id"]
    db_profile, db_preferences = profile_crud.get_profile(db, user_id=user_id)
    
    profile_data = {"user_id": str(user_id)}
    if db_profile:
        profile_data["daily_kcal_goal"] = db_profile.daily_kcal_target
        if db_profile.macro_json:
            profile_data["macro_ratio"] = json.loads(db_profile.macro_json)
        profile_data["activity_level"] = db_profile.activity_level

    if db_preferences:
        if db_preferences.exclude_allergens_json:
            profile_data["exclude_allergens"] = json.loads(db_preferences.exclude_allergens_json)
        if db_preferences.diet_types_json:
            profile_data["diet_types"] = json.loads(db_preferences.diet_types_json)
        if db_preferences.like_cuisines_json:
            profile_data["like_cuisines"] = json.loads(db_preferences.like_cuisines_json)
        if db_preferences.dislike_items_json:
            profile_data["dislike_items"] = json.loads(db_preferences.dislike_items_json)

    return Profile(**profile_data)

@router.put("/profile", response_model=Profile)
def update_profile(profile_in: UpdateProfile, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """사용자 프로필을 생성하거나 업데이트합니다."""
    user_id = user["user_id"]
    db_profile = profile_crud.upsert_profile(db, user_id=user_id, profile_data=profile_in)
    
    # After updating, fetch the complete profile including preferences to return
    db_profile, db_preferences = profile_crud.get_profile(db, user_id=user_id)
    profile_data = {"user_id": str(user_id)}
    if db_profile:
        profile_data["daily_kcal_goal"] = db_profile.daily_kcal_target
        if db_profile.macro_json:
            profile_data["macro_ratio"] = json.loads(db_profile.macro_json)
        profile_data["activity_level"] = db_profile.activity_level

    if db_preferences:
        if db_preferences.exclude_allergens_json:
            profile_data["exclude_allergens"] = json.loads(db_preferences.exclude_allergens_json)
        if db_preferences.diet_types_json:
            profile_data["diet_types"] = json.loads(db_preferences.diet_types_json)
        if db_preferences.like_cuisines_json:
            profile_data["like_cuisines"] = json.loads(db_preferences.like_cuisines_json)
        if db_preferences.dislike_items_json:
            profile_data["dislike_items"] = json.loads(db_preferences.dislike_items_json)

    return Profile(**profile_data)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인된 사용자 계정을 삭제합니다."""
    user_id = user["user_id"]
    user_crud.delete_user(db, user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# TODO: 선호도 관련 API를 DB와 연동해야 합니다.
@router.get("/preferences", response_model=Preferences, deprecated=True)
def get_preferences(user=Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.put("/preferences", response_model=Preferences, deprecated=True)
def put_preferences(body: Preferences, user=Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Not Implemented")