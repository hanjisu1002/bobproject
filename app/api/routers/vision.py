# app/api/routers/vision.py
from __future__ import annotations

import os
import tempfile
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import menu as crud_menu
from app.crud import nutrition as crud_nutrition
from app.schemas.menu import MenuWithNutrition
from app.services.cv_runtime import get_sessions
from cv.inference import predict_menu_top3_names

router = APIRouter()
log = logging.getLogger("app.vision")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "4"))  # 업로드 용량 제한 (MB)
CHUNK_SIZE = 1024 * 1024                              # 1MB씩 저장

@router.post("/vision/recognize-food", response_model=List[MenuWithNutrition], tags=["vision"])
async def recognize_food_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    업로드된 음식 이미지를 인식 → 후보 메뉴명(top-3) → DB 영양정보와 합쳐 반환
    최종 경로: /v1/vision/recognize-food
    """
    # --- CV 세션 확보 (함수 안에서!) ---
    try:
        det_sess, cls_sess = get_sessions(request.app)
    except Exception as e:
        log.exception("CV session init/get failed: %s", e)
        raise HTTPException(status_code=500, detail=f"CV 세션 준비 중 오류: {e}")

    # --- 업로드 검증 ---
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"업로드 용량 초과: {MAX_UPLOAD_MB}MB 이내로 업로드해주세요.")

    tmp_path = None
    try:
        # --- 임시파일 저장 (메모리 피크 방지) ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                tmp.write(chunk)

        # --- CV 추론 ---
        if det_sess is None or cls_sess is None:
            # YOLO(ultralytics) 모드
            yolo = getattr(request.app.state, "yolo", None)
            if yolo is None:
                raise HTTPException(status_code=500, detail="CV 백엔드 초기화 실패(YOLO/ONNX 모두 없음)")
            predicted_names = predict_menu_top3_names(tmp_path, yolo=yolo)
        else:
            # ONNX 모드
            predicted_names = predict_menu_top3_names(tmp_path, det_sess=det_sess, cls_sess=cls_sess)

        if not predicted_names:
            return []

        # --- 중복 제거 ---
        seen = set()
        unique_names = []
        for n in predicted_names:
            if n not in seen:
                seen.add(n)
                unique_names.append(n)

        # --- DB 조회 + 응답 조립 ---
        results: List[MenuWithNutrition] = []
        for name in unique_names:
            found_menus = crud_menu.search_by_name(db=db, query=name, limit=1)
            if not found_menus:
                continue

            found_menu = found_menus[0]
            nutrition_data = crud_nutrition.get_nutrition_by_food_code(
                db=db, food_code=found_menu.food_code
            )

            payload = {
                **jsonable_encoder(found_menu),
                "kcal": getattr(nutrition_data, "energy_kcal", None) if nutrition_data else None,
                "macro": (
                    {
                        "carb": getattr(nutrition_data, "carb_g", None),
                        "protein": getattr(nutrition_data, "protein_g", None),
                        "fat": getattr(nutrition_data, "fat_g", None),
                    }
                    if nutrition_data else None
                ),
                "allergens": [],
            }
            results.append(MenuWithNutrition.model_validate(payload))

        return results

    except HTTPException:
        raise
    except Exception as e:
        log.exception("CV inference failed: %s", e)
        raise HTTPException(status_code=500, detail=f"음식 인식 또는 DB 조회 중 오류: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
