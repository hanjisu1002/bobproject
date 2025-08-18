from sqlalchemy import Column, Integer, String, Text, DateTime, REAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Menu(Base):
    __tablename__ = "menu"

    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    food_code = Column(Text, unique=True, nullable=False)
    slug = Column(Text, unique=True, nullable=False)
    std_name = Column(Text, nullable=False)
    category = Column(Text)
    std_name_norm = Column(Text) # This is a GENERATED column in SQL, but SQLAlchemy doesn't directly support GENERATED for SQLite in this way. We'll handle it in application logic or rely on the DB.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    nutrition = relationship("Nutrition", back_populates="menu")
    user_history = relationship("UserHistory", back_populates="menu")

    def __repr__(self):
        return f"<Menu(food_code='{self.food_code}', std_name='{self.std_name}')>"
