from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/recognize")
async def recognize(file: UploadFile = File(...), k: int = 3):
    # 더미 응답
    return {"topk": [
        {"label": "bibimbap", "score": 0.82},
        {"label": "bulgogi",  "score": 0.12},
        {"label": "ramen",    "score": 0.06},
    ][:k]}
