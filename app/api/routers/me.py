from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.schemas.profile import Profile, UpdateProfile
from app.schemas.preferences import Preferences
from app.utils.deps import get_current_user
from app.db.session import get_db
from app.crud import profile as profile_crud, user as user_crud
from app.models.user_profile import UserProfile

router = APIRouter()

@router.get("/profile", response_model=Profile)
def get_profile(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인된 사용자의 프로필을 반환합니다."""
    user_id = user["user_id"]
    db_profile = profile_crud.get_profile(db, user_id=user_id)
    if not db_profile:
        # 프로필이 없으면 기본값으로 생성하여 반환
        return Profile(user_id=user_id)
    return db_profile

@router.put("/profile", response_model=Profile)
def update_profile(profile_in: UpdateProfile, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """사용자 프로필을 생성하거나 업데이트합니다."""
    user_id = user["user_id"]
    db_profile = profile_crud.upsert_profile(db, user_id=user_id, profile_data=profile_in)
    return db_profile

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