"""Database engine and session management."""
from typing import Generator
from backend.core.config import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except ImportError:
    engine = None  # type: ignore
    SessionLocal = None  # type: ignore
    Base = object  # type: ignore

def get_db():
    """Dependency generator for database sessions."""
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
