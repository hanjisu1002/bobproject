#!/usr/bin/env python3
"""
챗봇 API 온라인 테스트 스크립트
온라인 서버: https://bobproject-server.onrender.com/
"""

import requests
import json
from datetime import datetime

# 온라인 서버 URL
BASE_URL = "https://bobproject-server.onrender.com/api"

def test_chatbot_health():
    """챗봇 헬스 체크 테스트"""
    print("=== 챗봇 헬스 체크 테스트 ===")
    print(f"서버: {BASE_URL}/chatbot/health")
    
    try:
        response = requests.get(f"{BASE_URL}/chatbot/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 서버 응답이 너무 느립니다")
        print()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print()

def test_chatbot_chat():
    """챗봇 대화 테스트 (인증 없이)"""
    print("=== 챗봇 대화 테스트 (인증 없이) ===")
    print(f"서버: {BASE_URL}/chatbot/chat")
    
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
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ 예상된 결과: 인증이 필요합니다 (JWT 토큰 필요)")
        elif response.status_code == 200:
            print(f"✅ 성공! Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 예상치 못한 상태 코드: {response.status_code}")
            print(f"Response: {response.text}")
        print()
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 서버 응답이 너무 느립니다")
        print()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print()

def test_chatbot_with_image():
    """이미지 인식과 함께 챗봇 테스트"""
    print("=== 이미지 인식과 함께 챗봇 테스트 ===")
    print(f"서버: {BASE_URL}/chatbot/chat/with-image")
    
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
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ 예상된 결과: 인증이 필요합니다 (JWT 토큰 필요)")
        elif response.status_code == 200:
            print(f"✅ 성공! Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 예상치 못한 상태 코드: {response.status_code}")
            print(f"Response: {response.text}")
        print()
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 서버 응답이 너무 느립니다")
        print()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print()

def test_server_status():
    """서버 전체 상태 확인"""
    print("=== 서버 전체 상태 확인 ===")
    print(f"서버: https://bobproject-server.onrender.com/health")
    
    try:
        response = requests.get("https://bobproject-server.onrender.com/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ 서버가 정상적으로 작동 중입니다")
        else:
            print(f"❌ 서버 상태 이상: {response.status_code}")
        print()
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print()

def main():
    """메인 테스트 함수"""
    print("🤖 챗봇 API 온라인 테스트 시작")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"테스트 서버: https://bobproject-server.onrender.com/")
    print("=" * 60)
    
    # 1. 서버 전체 상태 확인
    test_server_status()
    
    # 2. 챗봇 헬스 체크 테스트
    test_chatbot_health()
    
    # 3. 기본 대화 테스트
    test_chatbot_chat()
    
    # 4. 이미지 인식과 함께 테스트
    test_chatbot_with_image()
    
    print("=" * 60)
    print("✅ 모든 테스트 완료!")
    print("\n📝 테스트 결과 해석:")
    print("- 401 상태 코드: 정상 (인증이 필요한 엔드포인트)")
    print("- 200 상태 코드: 성공 (API가 정상 작동)")
    print("- 타임아웃: 서버 응답 지연 (무료 서버의 일반적인 현상)")
    print("\n🔑 다음 단계:")
    print("- JWT 토큰을 발급받아 실제 인증 테스트")
    print("- GOOGLE_API_KEY 설정으로 LLM 기능 활성화")

if __name__ == "__main__":
    main()
