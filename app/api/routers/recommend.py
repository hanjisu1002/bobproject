from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
from app.utils.deps import get_current_user
from app.schemas.reco import RecommendationResponse, RecommendationItem
from app.schemas.nutrition import Nutrition
from app.schemas.menu import Menu

router = APIRouter()

@router.get("/recommendations", response_model=RecommendationResponse)
def recommend(request: Request,
              meal: str = "lunch",
              kcal_max: Optional[int] = Query(None, gt=0),
              user=Depends(get_current_user)):
    catalog = request.app.state.catalog
    items = []
    for m in catalog.menu_by_id.values():
        menu = Menu(**m)
        nut_dict = catalog.get_nutrition_scaled(menu.id, portion_g=None)
        if not nut_dict:
            continue
        nut = Nutrition(**nut_dict)
        if kcal_max and nut.kcal > kcal_max:
            continue
        items.append(RecommendationItem(menu=menu, nutrition=nut, score=1.0))
    return RecommendationResponse(items=items[:10])
