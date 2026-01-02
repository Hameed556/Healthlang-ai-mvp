"""
Database Connection and Session Management

This module handles PostgreSQL database connections using SQLAlchemy.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
from loguru import logger

from app.config import settings
from app.models.database_models import Base


# Get the appropriate database URL based on environment
database_url = settings.get_database_url()

# Log which database is being used
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Using database: {database_url.split('@')[-1] if '@' in database_url else 'local'}")

# Create SQLAlchemy engine
engine = create_engine(
    database_url,
    poolclass=NullPool if database_url.startswith("sqlite") else None,
    echo=settings.DEBUG,
    future=True,
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in Base metadata.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_database() -> None:
    """
    Drop all tables and recreate them.
    WARNING: This will delete all data!
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("Recreating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database reset complete")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            # SQLAlchemy 2.0 requires executable SQL objects
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
