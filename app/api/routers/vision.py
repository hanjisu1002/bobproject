from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import tempfile
import os
from typing import List
from fastapi.encoders import jsonable_encoder # Added import

from cv.inference import predict_menu_top3_names
from app.db.session import get_db
from app.crud import menu as crud_menu
from app.crud import nutrition as crud_nutrition # Import crud_nutrition
from app.schemas.menu import Menu as MenuSchema, MenuWithNutrition # Import MenuWithNutrition

router = APIRouter()

@router.post("/vision/recognize-food", response_model=List[MenuWithNutrition]) # Change response_model
async def recognize_food_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    업로드된 음식 이미지를 인식하여, 각 후보 메뉴에 대한 상세 영양 정보를 DB에서 조회 후 반환합니다.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    tmp_path = None  # Initialize tmp_path
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # CV 모델 추론 함수 호출
        predicted_names = predict_menu_top3_names(tmp_path)
        
        # DB에서 각 메뉴의 상세 정보 조회
        results = []
        for name in predicted_names:
            # 이름으로 메뉴 검색 (첫 번째 결과 사용)
            found_menus = crud_menu.search_by_name(db=db, query=name, limit=1)
            if found_menus:
                found_menu = found_menus[0]
                # 영양 정보 조회
                nutrition_data = crud_nutrition.get_nutrition_by_food_code(db=db, food_code=found_menu.food_code)
                
                # MenuWithNutrition 스키마에 맞게 데이터 조합
                menu_with_nutrition_data = {
                    **jsonable_encoder(found_menu),
                    "kcal": nutrition_data.energy_kcal if nutrition_data else None, # Use energy_kcal
                    "macro": {
                        "carb": nutrition_data.carb_g if nutrition_data else None,
                        "protein": nutrition_data.protein_g if nutrition_data else None,
                        "fat": nutrition_data.fat_g if nutrition_data else None,
                    } if nutrition_data else None,
                    "allergens": [], # Allergens not in Nutrition model, provide empty list
                }
                results.append(MenuWithNutrition.model_validate(menu_with_nutrition_data))
        
        return results
    
    except Exception as e:
        # 오류 발생 시 로그를 남기거나 더 상세한 예외 처리를 할 수 있습니다.
        print(f"Error during food recognition: {e}")
        raise HTTPException(status_code=500, detail="음식 인식 또는 DB 조회 중 오류가 발생했습니다.")
    
    finally:
        # 임시 파일 삭제
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
