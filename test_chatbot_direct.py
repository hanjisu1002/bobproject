#!/usr/bin/env python3
"""
챗봇을 직접 테스트하는 스크립트
"""

import sys
import os

# LLM 디렉토리를 Python 경로에 추가
sys.path.append('LLM')

def test_chatbot_direct():
    """챗봇을 직접 테스트"""
    try:
        print("🤖 챗봇 직접 테스트 시작...")
        
        # API 키 설정 확인
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
            return False
        
        print(f"✅ API 키 설정됨: {api_key[:10]}...")
        
        # 챗봇 import 및 생성
        print("📦 챗봇 모듈 import 중...")
        from LLM.Chatbot import Chatbot
        
        print("🤖 챗봇 인스턴스 생성 중...")
        csv_files = ["LLM/food_data_description.csv", "LLM/drink.csv", "LLM/sidedish.csv"]
        side_drink_files = ["LLM/sidedish.csv", "LLM/drink.csv"]
        bot = Chatbot(csv_files=csv_files, side_and_drink_files=side_drink_files)
        
        # 테스트 질문들
        test_questions = [
            "안녕하세요! 챗봇이 잘 작동하나요?",
            "오늘 점심으로 뭘 먹으면 좋을까요?",
            "김치찌개의 영양 정보를 알려주세요"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n💬 테스트 {i}: {question}")
            try:
                response = bot.ask(question)
                print(f"🤖 응답: {response[:200]}...")
                print("✅ 성공!")
            except Exception as e:
                print(f"❌ 실패: {e}")
                return False
        
        print("\n🎉 모든 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 챗봇 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_chatbot_direct()
    if success:
        print("\n✅ 챗봇이 정상적으로 작동합니다!")
    else:
        print("\n❌ 챗봇 테스트에 실패했습니다.")
