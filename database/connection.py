from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# ----------------------------
# Database URL from environment
# ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

# ----------------------------
# SQLAlchemy Setup
# ----------------------------
engine = create_engine(DATABASE_URL)

# Base class for models
Base = declarative_base()

# DB Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)