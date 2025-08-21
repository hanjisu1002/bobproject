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
    # PostgreSQL for production (Render)
    DB_URL: str = "postgresql://smartbite_user:06WMuWM221m8uikEmZ7F3Y1jcDT2eVF7@dpg-d2j9eendiees73bupsm0-a.singapore-postgres.render.com/smartbite"
    
    # 🔹 CORS Settings
    ALLOWED_ORIGINS: str = "https://bobproject.vercel.app,http://localhost:3000,http://localhost:19006"

    class Config:
        env_file = ".env"

settings = Settings()
