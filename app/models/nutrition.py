from sqlalchemy import Column, Integer, Text, REAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Nutrition(Base):
    __tablename__ = "nutrition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    food_code = Column(Text, ForeignKey('menu.food_code', ondelete='CASCADE'), nullable=False)
    energy_kcal = Column(REAL)
    water_g = Column(REAL)
    protein_g = Column(REAL)
    fat_g = Column(REAL)
    carb_g = Column(REAL)
    sugars_g = Column(REAL)
    fiber_g = Column(REAL)
    sodium_mg = Column(REAL)
    created_at = Column(DateTime, default=func.now())

    menu = relationship("Menu", back_populates="nutrition")

    def __repr__(self):
        return f"<Nutrition(food_code='{self.food_code}', energy_kcal={self.energy_kcal})>"
