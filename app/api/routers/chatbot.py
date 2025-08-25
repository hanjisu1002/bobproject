from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.schemas.chatbot import ChatRequest, ChatResponse, ChatHistory
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.crud.profile import get_profile_by_user_id
from app.crud.food_log import get_user_food_logs_today
from sqlalchemy.orm import Session
from app.db.session import get_db
import uuid
from datetime import datetime
import sys
import os
import json # Import json

# LLM 디렉토리를 Python 경로에 추가
sys.path.append('LLM')

# 전역 챗봇 인스턴스
chatbot = None

def get_chatbot():
    """챗봇 인스턴스 반환 (지연 로딩)"""
    global chatbot
    if chatbot is None:
        try:
            from LLM.Chatbot import Chatbot
            print("🤖 챗봇 인스턴스 생성 중...")
            
            # CSV 파일 경로 설정
            csv_files = ["LLM/food_data_description.csv", "LLM/drink.csv", "LLM/sidedish.csv"]
            side_drink_files = ["LLM/sidedish.csv", "LLM/drink.csv"]
            
            chatbot = Chatbot(
                csv_files=csv_files,
                side_and_drink_files=side_drink_files
            )
            print("✅ 챗봇 초기화 성공!")
            
        except Exception as e:
            print(f"❌ 챗봇 초기화 실패: {e}")
            return None
    
    return chatbot

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    챗봇과 대화하기
    
    - **message**: 사용자 메시지
    - **user_context**: 사용자 컨텍스트 정보 (목표, 선호도, 알레르기 등)
    - **food_recognition**: 이미지에서 인식된 음식 정보 (선택사항)
    """
    
    # 사용자 인증 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다"
        )
    
    # 사용자 ID 일치 확인 (타입 안전성 개선)
    try:
        current_user_id = str(current_user.user_id)
        request_user_id = str(request.user_context.user_id)
        
        if request_user_id != current_user_id:
            print(f"⚠️ 사용자 ID 불일치: 요청={request_user_id}, 현재={current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"자신의 계정에서만 사용할 수 있습니다 (요청: {request_user_id}, 현재: {current_user_id})"
            )
    except Exception as e:
        print(f"❌ 사용자 ID 검증 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID 검증에 실패했습니다"
        )
    
    try:
        # 챗봇 인스턴스 가져오기
        bot = get_chatbot()
        if bot is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="챗봇을 초기화할 수 없습니다"
            )
        
        # 사용자 프로필 및 선호도 설정 (DB에서 가져와 챗봇에 반영)
        user_profile_from_db, user_preferences_from_db = get_profile_by_user_id(db, current_user.user_id)
        
        user_profile_data = {}

        if user_profile_from_db:
            user_profile_data["calories"] = user_profile_from_db.daily_kcal_target
            if user_profile_from_db.macro_json:
                # Assuming macro_json is already a dict or None
                macros = user_profile_from_db.macro_json
                user_profile_data["protein_g"] = macros.get("protein_g")
                user_profile_data["fat_g"] = macros.get("fat_g")
                user_profile_data["carbs_g"] = macros.get("carbs_g")

        if user_preferences_from_db:
            if user_preferences_from_db.exclude_allergens_json:
                # Assuming exclude_allergens_json is already a list or None
                user_profile_data["allergens"] = user_preferences_from_db.exclude_allergens_json
            
            prefers_list = []
            if user_preferences_from_db.diet_types_json:
                # Assuming diet_types_json is already a list or None
                prefers_list.extend(user_preferences_from_db.diet_types_json)
            if user_preferences_from_db.like_cuisines_json:
                # Assuming like_cuisines_json is already a list or None
                prefers_list.extend(user_preferences_from_db.like_cuisines_json)
            user_profile_data["prefers"] = prefers_list

        # Filter out None values if the attributes don't exist or are not set
        user_profile_data = {k: v for k, v in user_profile_data.items() if v is not None}

        if user_profile_data: # Only set if there's actual data to set
            bot.set_user_profile(user_profile_data)
        else:
            print(f"DEBUG: No user profile or preferences found in DB for user {current_user.user_id}. Using default chatbot profile.")
        
        # 초기 음식명 설정 (이미지 인식 결과가 있다면)
        initial_food_name = None
        if request.food_recognition and request.food_recognition.food_name:
            initial_food_name = request.food_recognition.food_name
            print(f"DEBUG: Initial food name from recognition: {initial_food_name}")

        # 챗봇 응답 생성
        response_text = bot.ask(request.message, initial_food_name=initial_food_name)
        
        # 응답 생성
        response = ChatResponse(
            message_id=str(uuid.uuid4()),
            user_id=current_user_id,
            message=request.message,
            response=response_text,
            timestamp=datetime.now(),
            food_recognition=request.food_recognition
        )
        
        return response
        
    except Exception as e:
        print(f"❌ 챗봇 응답 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/chat/with-image", response_model=ChatResponse)
async def chat_with_image_recognition(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지 인식 결과와 함께 챗봇과 대화하기
    
    이미지에서 인식된 음식 정보를 바탕으로 더 정확한 답변을 제공합니다.
    """
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다"
        )
    
    if request.user_context.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 계정에서만 사용할 수 있습니다"
        )
    
    if not request.food_recognition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 인식 결과가 필요합니다"
        )
    
    try:
        # 챗봇 인스턴스 가져오기
        bot = get_chatbot()
        if bot is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="챗봇을 초기화할 수 없습니다"
            )
        
        # 사용자 프로필 및 선호도 설정 (DB에서 가져와 챗봇에 반영)
        user_profile_from_db, user_preferences_from_db = get_profile_by_user_id(db, current_user.user_id)
        
        user_profile_data = {}

        if user_profile_from_db:
            user_profile_data["calories"] = user_profile_from_db.daily_kcal_target
            if user_profile_from_db.macro_json:
                # Assuming macro_json is already a dict or None
                macros = user_profile_from_db.macro_json
                user_profile_data["protein_g"] = macros.get("protein_g")
                user_profile_data["fat_g"] = macros.get("fat_g")
                user_profile_data["carbs_g"] = macros.get("carbs_g")

        if user_preferences_from_db:
            if user_preferences_from_db.exclude_allergens_json:
                # Assuming exclude_allergens_json is already a list or None
                user_profile_data["allergens"] = user_preferences_from_db.exclude_allergens_json
            
            prefers_list = []
            if user_preferences_from_db.diet_types_json:
                # Assuming diet_types_json is already a list or None
                prefers_list.extend(user_preferences_from_db.diet_types_json)
            if user_preferences_from_db.like_cuisines_json:
                # Assuming like_cuisines_json is already a list or None
                prefers_list.extend(user_preferences_from_db.like_cuisines_json)
            user_profile_data["prefers"] = prefers_list

        # Filter out None values if the attributes don't exist or are not set
        user_profile_data = {k: v for k, v in user_profile_data.items() if v is not None}

        if user_profile_data: # Only set if there's actual data to set
            bot.set_user_profile(user_profile_data)
        else:
            print(f"DEBUG: No user profile or preferences found in DB for user {current_user.user_id}. Using default chatbot profile.")
        
        # 초기 음식명 설정 (이미지 인식 결과가 있다면)
        initial_food_name = None
        if request.food_recognition and request.food_recognition.food_name:
            initial_food_name = request.food_recognition.food_name
            print(f"DEBUG: Initial food name from recognition: {initial_food_name}")

        # 챗봇 응답 생성
        response_text = bot.ask(request.message, initial_food_name=initial_food_name)
        
        # 응답 생성
        response = ChatResponse(
            message_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            message=request.message,
            response=response_text,
            timestamp=datetime.now(),
            food_recognition=request.food_recognition
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )