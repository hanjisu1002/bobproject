from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class FoodRecognitionResult(BaseModel):
    """이미지에서 인식된 음식 정보"""
    food_name: str
    confidence: float
    nutrition_info: Optional[Dict[str, Any]] = None
    serving_size: Optional[float] = None

class UserContext(BaseModel):
    """현재 로그인된 사용자의 컨텍스트 정보"""
    user_id: str
    daily_kcal_goal: Optional[int] = None
    macro_ratio: Optional[Dict[str, float]] = None
    activity_level: Optional[str] = None
    exclude_allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    like_cuisines: Optional[List[str]] = None
    dislike_items: Optional[List[str]] = None
    current_meal_context: Optional[FoodRecognitionResult] = None

class ChatRequest(BaseModel):
    """챗봇 대화 요청"""
    message: str = Field(..., description="사용자 메시지")
    user_context: UserContext = Field(..., description="사용자 컨텍스트 정보")
    food_recognition: Optional[FoodRecognitionResult] = Field(None, description="이미지 인식 결과")

class ChatResponse(BaseModel):
    """챗봇 응답"""
    response: str = Field(..., description="챗봇 답변")
    context_updated: bool = Field(False, description="컨텍스트 업데이트 여부")
    suggested_actions: Optional[List[str]] = Field(None, description="제안하는 액션들")
    nutrition_tips: Optional[Dict[str, Any]] = Field(None, description="영양 관련 팁")

class ChatHistory(BaseModel):
    """대화 히스토리"""
    message_id: str
    timestamp: str
    user_message: str
    bot_response: str
    user_context: UserContext
    food_recognition: Optional[FoodRecognitionResult] = None
