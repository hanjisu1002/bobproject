from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from app.schemas.profile import UpdateProfile

def get_profile(db: Session, user_id: int) -> UserProfile | None:
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

def upsert_profile(db: Session, user_id: int, profile_data: UpdateProfile) -> UserProfile:
    db_profile = get_profile(db, user_id)
    if not db_profile:
        db_profile = UserProfile(user_id=user_id)
        db.add(db_profile)

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile
