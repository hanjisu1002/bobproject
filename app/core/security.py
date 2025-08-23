from datetime import datetime, timedelta
import jwt  # PyJWT
from typing import Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.schemas.auth import TokenData

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

def verify_token(token: str) -> Optional[Dict]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# JWT Bearer 토큰 인증
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """현재 인증된 사용자 정보 가져오기"""
    token = credentials.credentials
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="액세스 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 ID를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(user_id=user_id)
