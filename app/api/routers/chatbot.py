# app/api/routers/chatbot.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Tuple
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.crud.profile import get_profile_by_user_id
from sqlalchemy.orm import Session
from app.db.session import get_db
import uuid
from datetime import datetime
import sys
import os
from pathlib import Path


# ✅ LLM 디렉토리 위치를 유연하게 탐색: /app/LLM 또는 레포 루트 /LLM
_P = Path(__file__).resolve()
CANDIDATES = [
    _P.parents[2] / "LLM",   # /app/LLM
    _P.parents[3] / "LLM",   # /LLM (레포 루트)
    Path.cwd() / "LLM",      # 현재 작업 디렉토리 기준
]
LLM_DIR = next((p for p in CANDIDATES if p.exists()), CANDIDATES[1])

# from LLM.Chatbot import Chatbot 형태를 위해 '부모'를 sys.path에 추가
if str(LLM_DIR.parent) not in sys.path:
    sys.path.insert(0, str(LLM_DIR.parent))

# (디버그) 실제 참조 경로/파일 존재 여부 로그
print(f"[LLM_DIR] => {LLM_DIR.resolve()}")
for _f in ["food_data_description.csv", "drink.csv", "sidedish.csv"]:
    _p = LLM_DIR / _f
    print(f"[CHECK] {_p} exists={_p.exists()}")

# 전역 챗봇 인스턴스
_chatbot = None

def _resolve_llm_path(rel: str) -> str:
    """LLM 내부 CSV 등 상대경로를 절대경로로 변환"""
    return str(LLM_DIR / rel)

def get_chatbot():
    """챗봇 인스턴스 반환 (지연 로딩)"""
    global _chatbot
    if _chatbot is None:
        try:
            from LLM.Chatbot import Chatbot
            print("🤖 챗봇 인스턴스 생성 중...")

            csv_files = [
                _resolve_llm_path("food_data_description.csv"),
                _resolve_llm_path("drink.csv"),
                _resolve_llm_path("sidedish.csv"),
            ]
            side_drink_files = [
                _resolve_llm_path("sidedish.csv"),
                _resolve_llm_path("drink.csv"),
            ]

            _chatbot = Chatbot(
                csv_files=csv_files,
                side_and_drink_files=side_drink_files
            )
            print("✅ 챗봇 초기화 성공!")
        except Exception as e:
            print(f"❌ 챗봇 초기화 실패: {e}")
            return None
    return _chatbot

def _build_user_profile_payload(db: Session, user_id: str) -> dict:
    """DB에서 프로필/선호 불러와 챗봇에 넘길 payload 생성"""
    profile, prefs = get_profile_by_user_id(db, user_id)
    payload = {}

    if profile:
        # DB 칼럼명에 맞게 안정적으로 매핑
        # daily_kcal_target 또는 daily_kcal_goal 등 프로젝트에 맞게 조정
        if hasattr(profile, "daily_kcal_target") and profile.daily_kcal_target is not None:
            payload["calories"] = profile.daily_kcal_target
        elif hasattr(profile, "daily_kcal_goal") and profile.daily_kcal_goal is not None:
            payload["calories"] = profile.daily_kcal_goal

        macros = getattr(profile, "macro_json", None)
        if isinstance(macros, dict):
            # 키가 다르면 여기서 보정
            payload["protein_g"] = macros.get("protein_g") or macros.get("protein")
            payload["fat_g"]     = macros.get("fat_g") or macros.get("fat")
            payload["carbs_g"]   = macros.get("carbs_g") or macros.get("carb") or macros.get("carbs")

    if prefs:
        allergens = getattr(prefs, "exclude_allergens_json", None)
        if isinstance(allergens, list) and allergens:
            payload["allergens"] = allergens

        prefers_list = []
        for key in ("diet_types_json", "like_cuisines_json"):
            v = getattr(prefs, key, None)
            if isinstance(v, list):
                prefers_list.extend(v)
        if prefers_list:
            payload["prefers"] = prefers_list

    # None 제거
    return {k: v for k, v in payload.items() if v is not None}

router = APIRouter()

@router.post("/chatbot/chat", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    챗봇과 대화하기
    - POST /v1/chatbot/chat (main.py에서 prefix 부여)
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")

    # user_id 일치 검증 (양쪽 str로 통일)
    try:
        current_user_id = str(current_user.user_id)
        request_user_id = str(request.user_context.user_id)
        if request_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"자신의 계정에서만 사용할 수 있습니다 (요청: {request_user_id}, 현재: {current_user_id})"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 ID 검증 실패: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="사용자 ID 검증에 실패했습니다")

    # 챗봇 인스턴스
    bot = get_chatbot()
    if bot is None:
        raise HTTPException(status_code=500, detail="챗봇을 초기화할 수 없습니다")

    # 사용자 프로필/선호 → 챗봇에 세팅
    user_payload = _build_user_profile_payload(db, current_user_id)
    if user_payload:
        bot.set_user_profile(user_payload)
    else:
        print(f"DEBUG: No profile/preferences for user {current_user_id}. Using defaults.")

    # 이미지 인식 결과가 있으면 초기 음식명 전달
    initial_food_name = None
    if request.food_recognition and request.food_recognition.food_name:
        initial_food_name = request.food_recognition.food_name

    try:
        response_text = bot.ask(request.message, initial_food_name=initial_food_name)
    except Exception as e:
        print(f"❌ 챗봇 응답 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류: {e}")

    return ChatResponse(
        message_id=str(uuid.uuid4()),
        user_id=current_user_id,
        message=request.message,
        response=response_text,
        timestamp=datetime.now(),
        food_recognition=request.food_recognition
    )

@router.post("/chatbot/chat/with-image", response_model=ChatResponse)
async def chat_with_image_recognition(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지 인식 결과와 함께 챗봇과 대화하기
    - POST /v1/chatbot/chat/with-image
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")

    # 여기에서도 ID 비교를 문자열로 통일
    current_user_id = str(current_user.user_id)
    request_user_id = str(request.user_context.user_id)
    if request_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="자신의 계정에서만 사용할 수 있습니다")

    if not request.food_recognition:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 인식 결과가 필요합니다")

    bot = get_chatbot()
    if bot is None:
        raise HTTPException(status_code=500, detail="챗봇을 초기화할 수 없습니다")

    user_payload = _build_user_profile_payload(db, current_user_id)
    if user_payload:
        bot.set_user_profile(user_payload)

    initial_food_name = request.food_recognition.food_name or None

    try:
        response_text = bot.ask(request.message, initial_food_name=initial_food_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류: {e}")

    return ChatResponse(
        message_id=str(uuid.uuid4()),
        user_id=current_user_id,
        message=request.message,
        response=response_text,
        timestamp=datetime.now(),
        food_recognition=request.food_recognition
    )
