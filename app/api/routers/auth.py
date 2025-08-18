from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from app.schemas.auth import SignUpRequest, LoginRequest, TokenPair
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 인메모리 유저 저장소: email -> {hash, user_id}
_users = {}

@router.post("/signup", response_model=TokenPair)
def signup(body: SignUpRequest):
    if body.email in _users:
        raise HTTPException(status_code=409, detail="Email already exists")
    pw_hash = pwd_context.hash(body.password)
    _users[body.email] = {"hash": pw_hash, "user_id": body.email}
    return TokenPair(
        access_token=create_access_token(body.email),
        refresh_token=create_refresh_token(body.email),
    )

@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest):
    u = _users.get(body.email)
    if not u or not pwd_context.verify(body.password, u["hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenPair(
        access_token=create_access_token(body.email),
        refresh_token=create_refresh_token(body.email),
    )
