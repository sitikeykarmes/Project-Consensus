# backend/app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./whatsapp_aidb.db")


# PostgreSQL needs pool settings; SQLite needs check_same_thread
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,     # auto-reconnect if connection dropped
    )
else:
    # SQLite fallback (local dev without .env)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()