from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

db_url = settings.sqlalchemy_database_uri

# Create SQLAlchemy engine
try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
except Exception as e:
    # Fallback / graceful initialization
    engine = create_engine(
        db_url,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
