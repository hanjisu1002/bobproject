from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from app.models.user_preferences import UserPreferences
from app.schemas.profile import UpdateProfile
import json

def get_profile(db: Session, user_id: int) -> tuple[UserProfile | None, UserPreferences | None]:
    db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    db_preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    return db_profile, db_preferences

def upsert_profile(db: Session, user_id: int, profile_data: UpdateProfile) -> UserProfile:
    db_profile, db_preferences = get_profile(db, user_id)
    if not db_profile:
        db_profile = UserProfile(user_id=user_id)
        db.add(db_profile)

    if not db_preferences:
        db_preferences = UserPreferences(user_id=user_id)
        db.add(db_preferences)

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ["exclude_allergens", "diet_types", "like_cuisines", "dislike_items"]:
            # Handle user preferences separately
            if key == "exclude_allergens" and value is not None:
                db_preferences.exclude_allergens_json = json.dumps(value)
            elif key == "diet_types" and value is not None:
                db_preferences.diet_types_json = json.dumps(value)
            elif key == "like_cuisines" and value is not None:
                db_preferences.like_cuisines_json = json.dumps(value)
            elif key == "dislike_items" and value is not None:
                db_preferences.dislike_items_json = json.dumps(value)
        else:
            # Handle UserProfile fields
            if key == "daily_kcal_goal":
                setattr(db_profile, "daily_kcal_target", value)
            elif key == "macro_ratio":
                if value is not None and db_profile.daily_kcal_target is not None: # Check if daily_kcal_target is available
                    total_kcal = db_profile.daily_kcal_target
                    
                    # Convert percentages to grams
                    carb_g = (total_kcal * value.get("carb", 0) / 100) / 4
                    protein_g = (total_kcal * value.get("protein", 0) / 100) / 4
                    fat_g = (total_kcal * value.get("fat", 0) / 100) / 9

                    # Store as gram-based dictionary
                    gram_macro = {
                        "carb_g": round(carb_g, 2),
                        "protein_g": round(protein_g, 2),
                        "fat_g": round(fat_g, 2)
                    }
                    setattr(db_profile, "macro_json", json.dumps(gram_macro))
                else:
                    setattr(db_profile, "macro_json", None) # Set to None if value is None or daily_kcal_target is None
            elif key == "sex" and value is not None: # Add sex handling
                setattr(db_profile, "sex", value)
            elif key == "age" and value is not None: # Add age handling
                setattr(db_profile, "age", value)
            else:
                setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    db.refresh(db_preferences)
    return db_profile