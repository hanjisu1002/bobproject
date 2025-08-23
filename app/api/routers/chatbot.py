from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.schemas.chatbot import ChatRequest, ChatResponse, ChatHistory
from app.core.chatbot_service import chatbot_service
from app.core.security import get_current_user
from app.schemas.auth import TokenData
import uuid
from datetime import datetime

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
        # 챗봇 응답 생성
        response = await chatbot_service.get_response(
            message=request.message,
            user_context=request.user_context,
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
        response = await chatbot_service.get_response(
            message=request.message,
            user_context=request.user_context,
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
        user_profile = await chatbot_service._get_user_profile(user_id)
        
        # 오늘 섭취한 음식 정보 가져오기
        today_foods = await chatbot_service._get_today_food_logs(user_id)
        
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
    
    health_status = {
        "status": "healthy",
        "llm_available": chatbot_service.chatbot is not None,
        "food_data_loaded": chatbot_service.food_data is not None,
        "api_key_configured": chatbot_service.api_key is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    if not health_status["api_key_configured"]:
        health_status["status"] = "warning"
        health_status["message"] = "GOOGLE_API_KEY가 설정되지 않았습니다"
    
    if not health_status["llm_available"]:
        health_status["status"] = "warning"
        health_status["message"] = "LLM 챗봇을 사용할 수 없습니다"
    
    return health_status
