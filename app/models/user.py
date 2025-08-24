from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=True) # 이름 필드 추가
    email = Column(Text, unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    history = relationship("UserHistory", back_populates="user", cascade="all, delete-orphan")
    food_logs = relationship("UserFoodLog", back_populates="user", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User(email='{self.email}')>"