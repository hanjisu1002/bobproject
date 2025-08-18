from datetime import datetime, timedelta
import jwt  # PyJWT
from typing import Dict
from app.core.config import settings

def _encode(payload: Dict) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def _exp(minutes: int = 30):
    return datetime.utcnow() + timedelta(minutes=minutes)

def create_access_token(sub: str) -> str:
    payload = {"sub": sub, "type": "access", "exp": _exp(settings.ACCESS_TTL_MIN)}
    return _encode(payload)

def create_refresh_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TTL_DAYS),
    }
    return _encode(payload)
