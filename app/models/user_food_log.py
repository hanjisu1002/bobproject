from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class UserFoodLog(Base):
    __tablename__ = "user_food_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    menu_id = Column(Integer, ForeignKey('menu.menu_id', ondelete='CASCADE'), nullable=False)
    portion_g = Column(REAL, nullable=False)
    meal_type = Column(Text)
    consumed_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="food_logs")
    menu = relationship("Menu", back_populates="food_logs")
