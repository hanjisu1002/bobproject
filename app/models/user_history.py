from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    menu_id = Column(Integer, ForeignKey('menu.menu_id', ondelete='CASCADE'), nullable=False)
    action = Column(Text, nullable=False) # CHECK (action IN ('view','select','dismiss','scan'))
    ts = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="history")
    menu = relationship("Menu", back_populates="user_history")

    def __repr__(self):
        return f"<UserHistory(user_id={self.user_id}, menu_id={self.menu_id}, action='{self.action}')>"
