from fastapi import Header, HTTPException
import jwt
from app.core.config import settings

def get_current_user(authorization: str = Header(...)):
    # Expect: "Bearer <token>"
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Bad scheme")
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if payload.get("type") != "access":
            raise ValueError("Not access token")
        return {"user_id": payload["sub"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
