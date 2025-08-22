from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.schemas.auth import SignUpRequest, LoginRequest, TokenPair
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.crud import user as user_crud, session as session_crud
from app.utils.deps import get_current_user

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def signup(body: SignUpRequest, db: Session = Depends(get_db)):
    """회원가입을 처리하고 토큰 쌍을 반환합니다."""
    if user_crud.get_user_by_email(db, email=body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = user_crud.create_user(db, user=body)
    
    access_token = create_access_token(sub=str(user.user_id))
    refresh_token = create_refresh_token(sub=str(user.user_id))
    
    # 생성된 액세스 토큰으로 세션 생성
    session_crud.create_session(db, user_id=user.user_id, token=access_token)
    
    return TokenPair(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """로그인을 처리하고 새로운 토큰 쌍을 반환합니다."""
    user = user_crud.get_user_by_email(db, email=body.email)
    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(sub=str(user.user_id))
    refresh_token = create_refresh_token(sub=str(user.user_id))

    # 새로운 액세스 토큰으로 세션 생성
    session_crud.create_session(db, user_id=user.user_id, token=access_token)

    return TokenPair(access_token=access_token, refresh_token=refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 사용자의 세션을 무효화(삭제)합니다."""
    token = user.get("token")
    if token:
        session_crud.delete_session_by_token(db, token=token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)