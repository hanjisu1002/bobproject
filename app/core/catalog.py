import pandas as pd
from app.core.config import settings
from app.schemas.menu import Menu
from app.schemas.nutrition import Nutrition
from typing import Dict, Any, Optional

class Catalog:
    def __init__(self):
        # 지연 로딩을 위한 초기화 지연
        self._menu_df = None
        self._nutrition_df = None
        self._menu_by_id = None
        self._nutrition_by_food_code = None
        self._initialized = False

    def _ensure_initialized(self):
        """필요할 때만 데이터 로딩 (메모리 절약)"""
        if not self._initialized:
            print("🔄 Catalog 데이터 로딩 중...")
            try:
                self._menu_df = pd.read_csv(settings.FOODS_CSV)
                self._nutrition_df = pd.read_csv(settings.NUTRIENTS_CSV)
                self._menu_by_id = self._menu_df.set_index('food_code').to_dict(orient='index')
                self._nutrition_by_food_code = self._nutrition_df.set_index('food_code').to_dict(orient='index')
                self._initialized = True
                print("✅ Catalog 데이터 로딩 완료")
            except Exception as e:
                print(f"❌ Catalog 데이터 로딩 실패: {e}")
                # 기본값 설정
                self._menu_df = pd.DataFrame()
                self._nutrition_df = pd.DataFrame()
                self._menu_by_id = {}
                self._nutrition_by_food_code = {}
                self._initialized = True

    @property
    def menu_df(self):
        self._ensure_initialized()
        return self._menu_df

    @property
    def nutrition_df(self):
        self._ensure_initialized()
        return self._nutrition_df

    @property
    def menu_by_id(self):
        self._ensure_initialized()
        return self._menu_by_id

    @property
    def nutrition_by_food_code(self):
        self._ensure_initialized()
        return self._nutrition_by_food_code

    def get_nutrition_scaled(self, menu_id: int, portion_g: Optional[float] = None) -> Optional[Dict[str, float]]:
        self._ensure_initialized()
        
        menu_item = self._menu_by_id.get(menu_id)
        if not menu_item:
            return None

        food_code = menu_item.get('food_code')
        nutrition_data = self._nutrition_by_food_code.get(food_code)

        if not nutrition_data:
            return None

        # Assuming 100g is the standard portion for nutrition data in CSV
        standard_portion_g = 100.0
        
        if portion_g is None:
            # If portion_g is not provided, return nutrition for standard portion (e.g., 100g)
            return {
                "kcal": nutrition_data.get("energy_kcal", 0.0),
                "carb": nutrition_data.get("carb_g", 0.0),
                "protein": nutrition_data.get("protein_g", 0.0),
                "fat": nutrition_data.get("fat_g", 0.0),
                # Add other nutrients if needed
            }
        else:
            # Scale nutrition data based on provided portion_g
            scale_factor = portion_g / standard_portion_g
            return {
                "kcal": nutrition_data.get("energy_kcal", 0.0) * scale_factor,
                "carb": nutrition_data.get("carb_g", 0.0) * scale_factor,
                "protein": nutrition_data.get("protein_g", 0.0) * scale_factor,
                "fat": nutrition_data.get("fat_g", 0.0) * scale_factor,
                # Add other nutrients if needed
            }