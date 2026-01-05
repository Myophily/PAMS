from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./asset_data.db")

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=True  # Log all SQL queries for debugging in Phase 1
)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI endpoints.
    Provides database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema.
    Creates all tables and configures SQLite pragmas.
    """
    # Import all models to ensure they're registered with Base
    from app.models import account, transaction, holding, market_data, asset_snapshot

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Configure SQLite pragmas for better performance and data integrity
    with engine.connect() as conn:
        # Enable foreign key constraints (SQLite defaults to OFF)
        conn.execute(text("PRAGMA foreign_keys = ON;"))

        # Enable WAL mode for better concurrency
        conn.execute(text("PRAGMA journal_mode = WAL;"))

        # Set synchronous mode to NORMAL for better performance
        conn.execute(text("PRAGMA synchronous = NORMAL;"))

        conn.commit()

    print("Database initialized successfully!")
    print(f"Database location: {DATABASE_URL}")
