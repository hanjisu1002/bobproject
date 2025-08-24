from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), primary_key=True)
    daily_kcal_target = Column(Integer)
    macro_json = Column(Text)  # JSON string
    activity_level = Column(Text)
    is_completed = Column(Boolean, nullable=False, default=False)  # boolean으로 변경
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id})>"
