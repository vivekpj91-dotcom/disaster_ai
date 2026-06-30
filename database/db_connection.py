import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings

# Determine directory path to create local sqlite database folder if missing
if settings.DATABASE_URL.startswith("sqlite:///"):
    # extract relative path, e.g. ./database/database.db
    db_relative_path = settings.DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_relative_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

# Create Database Engine
# For SQLite, we enforce check_same_thread=False to support multi-threaded FastAPI calls safely.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # Automatically checks connection health before issuing queries
)

# Declarative base model class
Base = declarative_base()

# Local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that yields a local database session and cleans it up after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
