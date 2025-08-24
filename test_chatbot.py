#!/usr/bin/env python3
"""
챗봇 API 테스트 스크립트
"""

import requests
import json
from datetime import datetime

# API 기본 URL (로컬 테스트용)
BASE_URL = "http://localhost:8000/api"

def test_chatbot_health():
    """챗봇 헬스 체크 테스트"""
    print("=== 챗봇 헬스 체크 테스트 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/chatbot/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"오류 발생: {e}")
        print()

def test_chatbot_chat():
    """챗봇 대화 테스트 (인증 없이)"""
    print("=== 챗봇 대화 테스트 (인증 없이) ===")
    
    # 테스트용 요청 데이터
    test_request = {
        "message": "안녕하세요! 오늘 점심으로 비빔밥을 먹었는데, 영양적으로 어떤가요?",
        "user_context": {
            "user_id": "test_user_123",
            "daily_kcal_goal": 2000,
            "macro_ratio": {"carb": 0.5, "protein": 0.3, "fat": 0.2},
            "activity_level": "mid",
            "exclude_allergens": ["새우", "견과류"],
            "diet_types": ["체중 관리"],
            "like_cuisines": ["한식", "일식"],
            "dislike_items": ["매운 음식"]
        },
        "food_recognition": {
            "food_name": "비빔밥",
            "confidence": 0.95,
            "nutrition_info": {
                "calories": 450,
                "protein": 15,
                "carbs": 65,
                "fat": 12
            },
            "serving_size": 300
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chatbot/chat",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("예상된 결과: 인증이 필요합니다")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"오류 발생: {e}")
        print()

def test_chatbot_with_image():
    """이미지 인식과 함께 챗봇 테스트"""
    print("=== 이미지 인식과 함께 챗봇 테스트 ===")
    
    test_request = {
        "message": "이 음식의 칼로리는 얼마나 되나요?",
        "user_context": {
            "user_id": "test_user_123",
            "daily_kcal_goal": 1800,
            "activity_level": "low"
        },
        "food_recognition": {
            "food_name": "김치찌개",
            "confidence": 0.88,
            "nutrition_info": {
                "calories": 320,
                "protein": 18,
                "carbs": 25,
                "fat": 15
            },
            "serving_size": 250
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chatbot/chat/with-image",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("예상된 결과: 인증이 필요합니다")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"오류 발생: {e}")
        print()

def main():
    """메인 테스트 함수"""
    print("🤖 챗봇 API 테스트 시작")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. 헬스 체크 테스트
    test_chatbot_health()
    
    # 2. 기본 대화 테스트
    test_chatbot_chat()
    
    # 3. 이미지 인식과 함께 테스트
    test_chatbot_with_image()
    
    print("=" * 50)
    print("✅ 모든 테스트 완료!")
    print("\n📝 참고사항:")
    print("- 인증이 필요한 엔드포인트는 401 상태 코드를 반환합니다")
    print("- 실제 사용을 위해서는 JWT 토큰이 필요합니다")
    print("- GOOGLE_API_KEY가 설정되어야 LLM 기능이 작동합니다")

if __name__ == "__main__":
    main()
