import pandas as pd
from app.core.config import settings
from app.schemas.menu import Menu
from app.schemas.nutrition import Nutrition
from typing import Dict, Any, Optional

class Catalog:
    def __init__(self):
        self.menu_df = pd.read_csv(settings.FOODS_CSV)
        self.nutrition_df = pd.read_csv(settings.NUTRIENTS_CSV)
        self.menu_by_id: Dict[int, Dict[str, Any]] = self.menu_df.set_index('food_code').to_dict(orient='index')
        self.nutrition_by_food_code: Dict[str, Dict[str, Any]] = self.nutrition_df.set_index('food_code').to_dict(orient='index')

    def get_nutrition_scaled(self, menu_id: int, portion_g: Optional[float] = None) -> Optional[Dict[str, float]]:
        menu_item = self.menu_by_id.get(menu_id)
        if not menu_item:
            return None

        food_code = menu_item.get('food_code')
        nutrition_data = self.nutrition_by_food_code.get(food_code)

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