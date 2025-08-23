# 실행 예시
from inference import predict_menu_top3_per_box

if __name__ == "__main__":
    # 테스트할 이미지 경로
    image_path = "samples/삼겹살+물냉면.jpg"

    # 박스별 top3 메뉴 예측 실행
    results = predict_menu_top3_per_box(image_path)

    # 출력 보기
    for i, labels in enumerate(results, start=1):
        print(f"Box {i} Top3:", labels)
