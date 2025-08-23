# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

class Settings(BaseSettings):
    # .env 사용 + 알 수 없는 환경변수는 무시(충돌 방지)
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",         # 모르는 키가 와도 에러내지 않음
        case_sensitive=False,   # 환경변수 대소문자 혼용 시 편의(선택)
    )

    APP_NAME: str = "Personalized Meal API"
    API_PREFIX: str = "/v1"
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 30
    REFRESH_TTL_DAYS: int = 14

    # CSV 경로
    FOODS_CSV: str = "seed/foods.csv"
    NUTRIENTS_CSV: str = "seed/nutrients.csv"

    # ✅ Database URL: 여러 환경변수 이름을 모두 허용(DATABASE_URL, DB_URL, db_url)
    DATABASE_URL: str = Field(
        default="postgresql://smartbite_user:06WMuWM221m8uikEmZ7F3Y1jcDT2eVF7@dpg-d2j9eendiees73bupsm0-a.singapore-postgres.render.com/smartbite",
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL", "db_url"),
    )

    # CORS
    # 개발 편의를 위해 모든 Origin 허용 (운영 환경에서는 특정 도메인만 허용 권장)
    ALLOWED_ORIGINS: str = "https://bobproject.vercel.app,http://localhost:3000,http://localhost:19006,http://localhost:8081"

settings = Settings()
