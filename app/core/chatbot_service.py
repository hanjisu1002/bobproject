import os
import pandas as pd
from typing import Dict, List, Any, Optional
from app.schemas.chatbot import UserContext, FoodRecognitionResult, ChatResponse
from app.schemas.profile import Profile
from app.crud.profile import get_profile_by_user_id
from app.crud.food_log import get_user_food_logs_today
import sys

# LLM 모듈 import 시도
try:
    sys.path.append('LLM')
    from LLM.Chatbot import Chatbot
    LLM_AVAILABLE = True
    print("✅ LLM 모듈 import 성공")
except ImportError as e:
    print(f"❌ LLM.Chatbot import 실패: {e}")
    LLM_AVAILABLE = False

class ChatbotService:
    """챗봇 서비스 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.chatbot = None
        self.food_data = None
        self._load_food_data()
        self._initialize_chatbot()
    
    def _load_food_data(self):
        """음식 데이터 로드"""
        try:
            # LLM 디렉토리의 CSV 파일들 로드
            food_df = pd.read_csv('LLM/food_data_description.csv')
            drink_df = pd.read_csv('LLM/drink.csv')
            sidedish_df = pd.read_csv('LLM/sidedish.csv')
            
            # 데이터 통합
            self.food_data = {
                'main_dishes': food_df,
                'drinks': drink_df,
                'sidedishes': sidedish_df
            }
            print("✅ 음식 데이터 로드 완료")
        except Exception as e:
            print(f"❌ 음식 데이터 로드 실패: {e}")
            self.food_data = None
    
    def _initialize_chatbot(self):
        """챗봇 초기화"""
        if self.api_key and self.food_data is not None and LLM_AVAILABLE:
            try:
                self.chatbot = Chatbot()
                print("✅ LLM 챗봇 초기화 완료")
            except Exception as e:
                print(f"❌ LLM 챗봇 초기화 실패: {e}")
                self.chatbot = None
        else:
            if not self.api_key:
                print("⚠️ GOOGLE_API_KEY가 설정되지 않음")
            if not self.food_data:
                print("⚠️ 음식 데이터를 로드할 수 없음")
            if not LLM_AVAILABLE:
                print("⚠️ LLM 모듈을 import할 수 없음")
            print("⚠️ LLM 챗봇 초기화 건너뜀")
            self.chatbot = None
    
    async def get_response(
        self, 
        message: str, 
        user_context: UserContext,
        food_recognition: Optional[FoodRecognitionResult] = None
    ) -> ChatResponse:
        """챗봇 응답 생성"""
        
        # 컨텍스트 정보 구성
        context_info = self._build_context_info(user_context, food_recognition)
        
        # 사용자 프로필 정보 가져오기
        user_profile = await self._get_user_profile(user_context.user_id)
        
        # 오늘 섭취한 음식 정보 가져오기
        today_foods = await self._get_today_food_logs(user_context.user_id)
        
        # LLM 챗봇 사용 가능한 경우
        if self.chatbot:
            try:
                response = await self._get_llm_response(
                    message, context_info, user_profile, today_foods, food_recognition
                )
                return response
            except Exception as e:
                print(f"LLM 챗봇 오류: {e}")
                return self._get_fallback_response(message, context_info)
        
        # LLM 챗봇 사용 불가능한 경우 기본 응답
        return self._get_fallback_response(message, context_info)
    
    def _build_context_info(
        self, 
        user_context: UserContext, 
        food_recognition: Optional[FoodRecognitionResult]
    ) -> Dict[str, Any]:
        """컨텍스트 정보 구성"""
        context = {
            "user_id": user_context.user_id,
            "daily_kcal_goal": user_context.daily_kcal_goal,
            "macro_ratio": user_context.macro_ratio,
            "activity_level": user_context.activity_level,
            "exclude_allergens": user_context.exclude_allergens,
            "diet_types": user_context.diet_types,
            "like_cuisines": user_context.like_cuisines,
            "dislike_items": user_context.dislike_items
        }
        
        if food_recognition:
            context["current_food"] = {
                "name": food_recognition.food_name,
                "confidence": food_recognition.confidence,
                "nutrition": food_recognition.nutrition_info,
                "serving_size": food_recognition.serving_size
            }
        
        return context
    
    async def _get_user_profile(self, user_id: str) -> Optional[Profile]:
        """사용자 프로필 정보 가져오기"""
        try:
            # 데이터베이스 세션을 가져와야 하지만, 현재는 더미 데이터 반환
            # TODO: 실제 데이터베이스 연동 시 수정 필요
            return None
        except Exception as e:
            print(f"프로필 조회 실패: {e}")
            return None
    
    async def _get_today_food_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """오늘 섭취한 음식 로그 가져오기"""
        try:
            # 데이터베이스 세션을 가져와야 하지만, 현재는 더미 데이터 반환
            # TODO: 실제 데이터베이스 연동 시 수정 필요
            return []
        except Exception as e:
            print(f"음식 로그 조회 실패: {e}")
            return []
    
    async def _get_llm_response(
        self, 
        message: str, 
        context_info: Dict[str, Any],
        user_profile: Optional[Profile],
        today_foods: List[Dict[str, Any]],
        food_recognition: Optional[FoodRecognitionResult]
    ) -> ChatResponse:
        """LLM을 사용한 응답 생성"""
        
        # 프롬프트 구성
        prompt = self._build_enhanced_prompt(message, context_info, user_profile, today_foods, food_recognition)
        
        # LLM 챗봇에 전달
        try:
            # 여기서 실제 LLM.Chatbot의 메서드를 호출
            # 현재는 더미 응답으로 대체
            response_text = f"LLM 응답: {message}에 대한 답변입니다."
            
            return ChatResponse(
                response=response_text,
                context_updated=True,
                suggested_actions=["영양 정보 기록", "식단 계획 수정"],
                nutrition_tips={"calories": "적정 칼로리 유지", "protein": "단백질 섭취 증가 권장"}
            )
        except Exception as e:
            print(f"LLM 응답 생성 실패: {e}")
            return self._get_fallback_response(message, context_info)
    
    def _build_enhanced_prompt(
        self, 
        message: str, 
        context_info: Dict[str, Any],
        user_profile: Optional[Profile],
        today_foods: List[Dict[str, Any]],
        food_recognition: Optional[FoodRecognitionResult]
    ) -> str:
        """향상된 프롬프트 구성"""
        
        prompt_parts = [
            f"사용자 ID: {context_info['user_id']}",
            f"일일 목표 칼로리: {context_info.get('daily_kcal_goal', '설정되지 않음')} kcal",
            f"활동 수준: {context_info.get('activity_level', '설정되지 않음')}"
        ]
        
        if context_info.get('exclude_allergens'):
            prompt_parts.append(f"알레르기 제외: {', '.join(context_info['exclude_allergens'])}")
        
        if context_info.get('diet_types'):
            prompt_parts.append(f"다이어트 타입: {', '.join(context_info['diet_types'])}")
        
        if food_recognition:
            prompt_parts.append(f"현재 음식: {food_recognition.food_name} (신뢰도: {food_recognition.confidence:.2f})")
        
        if today_foods:
            total_calories = sum(food.get('calories', 0) for food in today_foods)
            prompt_parts.append(f"오늘 섭취 칼로리: {total_calories} kcal")
        
        prompt_parts.append(f"사용자 메시지: {message}")
        
        return "\n".join(prompt_parts)
    
    def _get_fallback_response(self, message: str, context_info: Dict[str, Any]) -> ChatResponse:
        """LLM 사용 불가능 시 기본 응답"""
        
        # 간단한 키워드 기반 응답
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['칼로리', '영양', '영양소']):
            response = "영양 정보에 대해 질문하셨군요! 현재 이미지에서 인식된 음식의 영양 정보를 분석해드릴 수 있습니다."
        elif any(word in message_lower for word in ['추천', '추천해', '추천해줘']):
            response = "식단 추천을 원하시는군요! 사용자의 목표와 선호도를 고려해서 맞춤형 추천을 제공할 수 있습니다."
        elif any(word in message_lower for word in ['다이어트', '체중', '감량']):
            response = "체중 관리에 대해 질문하셨군요! 현재 섭취한 음식과 목표를 고려해서 조언을 드릴 수 있습니다."
        else:
            response = "안녕하세요! 영양 코치 AI입니다. 음식 사진을 업로드하시면 영양 분석과 맞춤형 조언을 제공해드립니다."
        
        return ChatResponse(
            response=response,
            context_updated=False,
            suggested_actions=["음식 사진 업로드", "영양 정보 조회"],
            nutrition_tips={"general": "균형 잡힌 식단이 중요합니다"}
        )

# 전역 인스턴스
chatbot_service = ChatbotService()
