from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base

# Database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DB_URL

# Create the SQLAlchemy engine
# PostgreSQL doesn't need check_same_thread
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings for development
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL settings for production
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
