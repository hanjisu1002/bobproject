from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.schemas.chatbot import ChatRequest, ChatResponse, ChatHistory
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.crud.profile import get_profile_by_user_id
from app.crud.food_log import get_user_food_logs_today
import uuid
from datetime import datetime
import sys
import os

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
    current_user: TokenData = Depends(get_current_user)
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
    
    # 사용자 ID 일치 확인
    if request.user_context.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 계정에서만 사용할 수 있습니다"
        )
    
    try:
        # 챗봇 인스턴스 가져오기
        bot = get_chatbot()
        if bot is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="챗봇을 초기화할 수 없습니다"
            )
        
        # 사용자 프로필 설정
        if request.user_context.profile:
            bot.set_user_profile(request.user_context.profile)
        
        # 챗봇 응답 생성
        response_text = bot.ask(request.message)
        
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

@router.post("/chat/with-image", response_model=ChatResponse)
async def chat_with_image_recognition(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user)
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
        
        # 사용자 프로필 설정
        if request.user_context.profile:
            bot.set_user_profile(request.user_context.profile)
        
        # 챗봇 응답 생성
        response_text = bot.ask(request.message)
        
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

@router.get("/context/{user_id}", response_model=dict)
async def get_user_chat_context(
    user_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    사용자의 챗봇 대화 컨텍스트 정보 가져오기
    
    현재 로그인된 사용자의 프로필, 목표, 선호도 등의 정보를 반환합니다.
    """
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다"
        )
    
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 정보만 조회할 수 있습니다"
        )
    
    try:
        # 사용자 프로필 정보 가져오기
        user_profile = await get_profile_by_user_id(user_id)
        
        # 오늘 섭취한 음식 정보 가져오기
        today_foods = await get_user_food_logs_today(user_id)
        
        context = {
            "user_id": user_id,
            "profile": user_profile.dict() if user_profile else None,
            "today_foods": today_foods,
            "total_calories_today": sum(food.get('calories', 0) for food in today_foods)
        }
        
        return context
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"컨텍스트 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def chatbot_health_check():
    """
    챗봇 서비스 상태 확인
    
    LLM 연결 상태와 음식 데이터 로드 상태를 확인합니다.
    """
    
    bot = get_chatbot()
    
    health_status = {
        "status": "healthy",
        "llm_available": bot is not None,
        "food_data_loaded": bot is not None and hasattr(bot, 'master_df'),
        "api_key_configured": os.getenv("GOOGLE_API_KEY") is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    if not health_status["api_key_configured"]:
        health_status["status"] = "warning"
        health_status["message"] = "GOOGLE_API_KEY가 설정되지 않았습니다"
    
    if not health_status["llm_available"]:
        health_status["status"] = "warning"
        health_status["message"] = "LLM 챗봇을 사용할 수 없습니다"
    
    return health_status
