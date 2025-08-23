from sqlalchemy import Column, Integer, Text, DateTime, Computed # Import Computed
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Menu(Base):
    __tablename__ = "menu"

    menu_id = Column(Integer, primary_key=True, index=True)
    food_code = Column(Text, unique=True, nullable=False)
    slug = Column(Text, unique=True, nullable=False)
    std_name = Column(Text, nullable=False)
    category = Column(Text)
    std_name_norm = Column(Text, Computed("lower(replace(replace(replace(replace(std_name,' ',''),'-',''),'_',''),'/',''))")) # Use Computed
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    nutrition = relationship("Nutrition", back_populates="menu", uselist=False)
    food_logs = relationship("UserFoodLog", back_populates="menu")
    user_history = relationship("UserHistory", back_populates="menu")


    def __repr__(self):
        return f"<Menu(food_code='{self.food_code}', std_name='{self.std_name}')>"
