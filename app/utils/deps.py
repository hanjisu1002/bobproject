from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from app.core.config import settings
from app.db.session import get_db
from app.crud.session import get_session_by_token

# 1. 보안 스키마 정의
bearer_scheme = HTTPBearer()

def get_current_user(db: Session = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """토큰을 검증하고 현재 로그인된 사용자 정보를 반환합니다."""
    # 2. HTTPBearer가 자동으로 scheme과 credentials(토큰)을 파싱해줌
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme.")

    token = creds.credentials
    try:
        # 3. JWT 토큰 자체의 유효성 검증 (만료시간, 서명 등)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # 4. DB에 해당 토큰 세션이 존재하는지 확인 (로그아웃 여부 체크)
        session = get_session_by_token(db, token=token)
        if not session:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # 5. 세션의 소유자와 토큰의 소유자가 일치하는지 확인
        if session.user_id != int(user_id):
            raise HTTPException(status_code=401, detail="Token user mismatch")

        return {"user_id": int(user_id), "token": token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
