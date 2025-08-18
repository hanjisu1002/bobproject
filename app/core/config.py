from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Personalized Meal API"
    API_PREFIX: str = "/v1"
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 30
    REFRESH_TTL_DAYS: int = 14

    # 🔹 CSV 경로 기본값 (project 루트 기준)
    FOODS_CSV: str = "seed/foods.csv"
    NUTRIENTS_CSV: str = "seed/nutrients.csv"
    
    # 🔹 Database
    DB_URL: str = "sqlite:///./data/menu.db"


    class Config:
        env_file = ".env"

settings = Settings()
