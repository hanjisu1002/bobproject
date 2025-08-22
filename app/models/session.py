from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Session(Base):
    __tablename__ = "session"

    token = Column(Text, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(token='{self.token}', user_id={self.user_id})>"
