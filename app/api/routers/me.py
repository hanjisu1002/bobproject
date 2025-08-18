from fastapi import APIRouter, Depends
from app.schemas.profile import Profile, UpdateProfile
from app.schemas.preferences import Preferences
from app.utils.deps import get_current_user

router = APIRouter()

_profiles = {}      # user_id -> Profile
_preferences = {}   # user_id -> Preferences

@router.get("/profile", response_model=Profile)
def get_profile(user=Depends(get_current_user)):
    uid = user["user_id"]
    return _profiles.get(uid, Profile(user_id=uid))

@router.put("/profile", response_model=Profile)
def update_profile(body: UpdateProfile, user=Depends(get_current_user)):
    uid = user["user_id"]
    current = _profiles.get(uid, Profile(user_id=uid))
    data = current.model_dump()
    for k, v in body.model_dump(exclude_none=True).items():
        data[k] = v
    prof = Profile(**data)
    _profiles[uid] = prof
    return prof

@router.get("/preferences", response_model=Preferences)
def get_preferences(user=Depends(get_current_user)):
    uid = user["user_id"]
    return _preferences.get(uid, Preferences())

@router.put("/preferences", response_model=Preferences)
def put_preferences(body: Preferences, user=Depends(get_current_user)):
    uid = user["user_id"]
    _preferences[uid] = body
    return body
