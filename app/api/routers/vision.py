# app/api/routers/vision.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import tempfile
import os
from typing import List
from fastapi.encoders import jsonable_encoder
from cv.inference import predict_menu_top3_names
from app.db.session import get_db
from app.crud import menu as crud_menu
from app.crud import nutrition as crud_nutrition
from app.schemas.menu import MenuWithNutrition

router = APIRouter()

@router.post("/vision/recognize-food", response_model=List[MenuWithNutrition])
async def recognize_food_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    업로드된 음식 이미지를 인식 → 후보 메뉴명들을 얻고 → DB에서 영양정보 합쳐서 반환
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # ✅ CV 추론 (cv/inference 내부에서 YOLO 사용한다면, 그 파일에도 import 필요)
        predicted_names = predict_menu_top3_names(tmp_path)  # e.g. ['비빔밥', '김치찌개', '된장찌개']

        results: List[MenuWithNutrition] = []
        for name in predicted_names:
            found_menus = crud_menu.search_by_name(db=db, query=name, limit=1)
            if not found_menus:
                continue

            found_menu = found_menus[0]
            nutrition_data = crud_nutrition.get_nutrition_by_food_code(
                db=db, food_code=found_menu.food_code
            )

            menu_with_nutrition_data = {
                **jsonable_encoder(found_menu),
                "kcal": getattr(nutrition_data, "energy_kcal", None) if nutrition_data else None,
                "macro": {
                    "carb": getattr(nutrition_data, "carb_g", None),
                    "protein": getattr(nutrition_data, "protein_g", None),
                    "fat": getattr(nutrition_data, "fat_g", None),
                } if nutrition_data else None,
                "allergens": [],  # 알레르겐 정보 없으면 빈 배열
            }
            results.append(MenuWithNutrition.model_validate(menu_with_nutrition_data))

        return results

    except HTTPException:
        # 위에서 명시적으로 던진 HTTPException은 그대로 전파
        raise
    except Exception as e:
        # ❌ 내부 오류는 500으로
        print(f"CV inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"음식 인식 또는 DB 조회 중 오류: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
