#!/usr/bin/env python3
"""
메모리 사용량 모니터링 및 최적화 상태 확인 스크립트
"""

import os
import psutil
import gc
import sys
from typing import Dict, Any

def get_memory_info() -> Dict[str, Any]:
    """현재 메모리 사용량 정보 반환"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size (MB)
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size (MB)
        "percent": process.memory_percent(),         # 메모리 사용률 (%)
        "available_mb": psutil.virtual_memory().available / 1024 / 1024,  # 사용 가능한 메모리 (MB)
        "total_mb": psutil.virtual_memory().total / 1024 / 1024,         # 전체 메모리 (MB)
    }

def check_environment_variables() -> Dict[str, str]:
    """메모리 최적화 환경변수 확인"""
    memory_vars = [
        "PYTORCH_CUDA_ALLOC_CONF",
        "TRANSFORMERS_CACHE",
        "HF_HOME",
        "TOKENIZERS_PARALLELISM",
        "PYTORCH_NO_CUDA_MEMORY_CACHING",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
        "PYTHONMALLOC",
        "PYTHONHASHSEED"
    ]
    
    env_status = {}
    for var in memory_vars:
        value = os.getenv(var, "NOT_SET")
        env_status[var] = value
    
    return env_status

def test_chatbot_memory_usage():
    """챗봇 초기화 시 메모리 사용량 테스트"""
    try:
        print("🧠 챗봇 메모리 사용량 테스트 시작...")
        
        # 초기 메모리 상태
        initial_memory = get_memory_info()
        print(f"📊 초기 메모리: {initial_memory['rss_mb']:.1f} MB")
        
        # 챗봇 import
        print("📦 LLM.Chatbot 모듈 import 중...")
        sys.path.append('LLM')
        from LLM.Chatbot import Chatbot
        
        # import 후 메모리 상태
        import_memory = get_memory_info()
        print(f"📊 import 후 메모리: {import_memory['rss_mb']:.1f} MB")
        print(f"📈 import 메모리 증가: {import_memory['rss_mb'] - initial_memory['rss_mb']:.1f} MB")
        
        # 챗봇 인스턴스 생성 (CSV 파일 경로 명시)
        print("🤖 챗봇 인스턴스 생성 중...")
        csv_files = ["LLM/food_data_description.csv", "LLM/drink.csv", "LLM/sidedish.csv"]
        side_drink_files = ["LLM/sidedish.csv", "LLM/drink.csv"]
        bot = Chatbot(csv_files=csv_files, side_and_drink_files=side_drink_files)
        
        # 인스턴스 생성 후 메모리 상태
        instance_memory = get_memory_info()
        print(f"📊 인스턴스 생성 후 메모리: {instance_memory['rss_mb']:.1f} MB")
        print(f"📈 인스턴스 메모리 증가: {instance_memory['rss_mb'] - import_memory['rss_mb']:.1f} MB")
        
        # 첫 번째 질문 (모델 로딩 트리거)
        print("💬 첫 번째 질문으로 모델 로딩 트리거...")
        response = bot.ask("안녕하세요")
        
        # 모델 로딩 후 메모리 상태
        model_memory = get_memory_info()
        print(f"📊 모델 로딩 후 메모리: {model_memory['rss_mb']:.1f} MB")
        print(f"📈 모델 로딩 메모리 증가: {model_memory['rss_mb'] - instance_memory['rss_mb']:.1f} MB")
        
        # 전체 메모리 증가량
        total_increase = model_memory['rss_mb'] - initial_memory['rss_mb']
        print(f"📈 전체 메모리 증가: {total_increase:.1f} MB")
        
        # 가비지 컬렉션 실행
        print("🗑️ 가비지 컬렉션 실행...")
        gc.collect()
        
        # GC 후 메모리 상태
        gc_memory = get_memory_info()
        print(f"📊 GC 후 메모리: {gc_memory['rss_mb']:.1f} MB")
        print(f"📉 GC로 절약된 메모리: {model_memory['rss_mb'] - gc_memory['rss_mb']:.1f} MB")
        
        return {
            "success": True,
            "initial_mb": initial_memory['rss_mb'],
            "final_mb": gc_memory['rss_mb'],
            "total_increase_mb": total_increase,
            "gc_saved_mb": model_memory['rss_mb'] - gc_memory['rss_mb']
        }
        
    except Exception as e:
        print(f"❌ 챗봇 메모리 테스트 실패: {e}")
        return {"success": False, "error": str(e)}

def main():
    """메인 함수"""
    print("🚀 메모리 최적화 상태 확인 시작")
    print("=" * 60)
    
    # 1. 현재 메모리 상태
    print("\n1️⃣ 현재 메모리 상태")
    memory_info = get_memory_info()
    print(f"   📊 사용 중인 메모리: {memory_info['rss_mb']:.1f} MB")
    print(f"   📊 가상 메모리: {memory_info['vms_mb']:.1f} MB")
    print(f"   📊 메모리 사용률: {memory_info['percent']:.1f}%")
    print(f"   📊 사용 가능한 메모리: {memory_info['available_mb']:.1f} MB")
    print(f"   📊 전체 메모리: {memory_info['total_mb']:.1f} MB")
    
    # 2. 환경변수 확인
    print("\n2️⃣ 메모리 최적화 환경변수 확인")
    env_status = check_environment_variables()
    for var, value in env_status.items():
        status = "✅" if value != "NOT_SET" else "❌"
        print(f"   {status} {var}: {value}")
    
    # 3. 챗봇 메모리 테스트
    print("\n3️⃣ 챗봇 메모리 사용량 테스트")
    test_result = test_chatbot_memory_usage()
    
    # 4. 결과 요약
    print("\n" + "=" * 60)
    print("📊 메모리 최적화 결과 요약")
    
    if test_result["success"]:
        print(f"   🧠 초기 메모리: {test_result['initial_mb']:.1f} MB")
        print(f"   🚀 최종 메모리: {test_result['final_mb']:.1f} MB")
        print(f"   📈 총 증가량: {test_result['total_increase_mb']:.1f} MB")
        print(f"   🗑️ GC 절약량: {test_result['gc_saved_mb']:.1f} MB")
        
        # Render 무료 티어 기준 평가
        if test_result['final_mb'] < 400:
            print("   🎉 메모리 사용량이 Render 무료 티어에 적합합니다!")
        elif test_result['final_mb'] < 500:
            print("   ⚠️ 메모리 사용량이 Render 무료 티어 한계에 근접합니다.")
        else:
            print("   ❌ 메모리 사용량이 Render 무료 티어를 초과합니다.")
    else:
        print(f"   ❌ 테스트 실패: {test_result.get('error', 'Unknown error')}")
    
    # 5. 최적화 권장사항
    print("\n💡 메모리 최적화 권장사항:")
    print("   1. 환경변수가 모두 설정되어 있는지 확인")
    print("   2. 지연 로딩이 제대로 작동하는지 확인")
    print("   3. 불필요한 모델은 즉시 해제")
    print("   4. 정기적인 가비지 컬렉션 실행")

if __name__ == "__main__":
    main()
