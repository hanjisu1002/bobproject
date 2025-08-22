from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel

def get_session_by_token(db: Session, token: str) -> SessionModel | None:
    return db.query(SessionModel).filter(SessionModel.token == token).first()

def create_session(db: Session, user_id: int, token: str) -> SessionModel:
    db_session = SessionModel(user_id=user_id, token=token)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def delete_session_by_token(db: Session, token: str):
    db_session = db.query(SessionModel).filter(SessionModel.token == token).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session
