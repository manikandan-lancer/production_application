# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# -------------------------------
# Load database URL (Render / Neon)
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL not set in environment variables")

# -------------------------------
# SQLAlchemy Engine
# -------------------------------
engine = create_engine(DATABASE_URL)

# -------------------------------
# Base for model inheritance
# -------------------------------
Base = declarative_base()

# -------------------------------
# Session factory
# -------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)