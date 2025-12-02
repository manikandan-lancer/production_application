import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# ------------------------------------------
# Load DATABASE_URL from environment
# ------------------------------------------
raw_url = os.getenv("DATABASE_URL")

if not raw_url:
    raise RuntimeError("❌ DATABASE_URL is missing. Add it in Render Environment Variables.")

# ------------------------------------------
# Fix URL for SQLAlchemy
# Render gives URL like:
# postgresql://user:pass@host/db?sslmode=require
#
# SQLAlchemy requires:
# postgresql+psycopg2://user:pass@host/db?sslmode=require
# ------------------------------------------

if raw_url.startswith("postgres://"):  
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)

elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Remove unsupported param "channel_binding=require"
raw_url = raw_url.replace("&channel_binding=require", "")
raw_url = raw_url.replace("?channel_binding=require", "")

# Ensure sslmode=require
if "sslmode" not in raw_url:
    if "?" in raw_url:
        raw_url += "&sslmode=require"
    else:
        raw_url += "?sslmode=require"

DATABASE_URL = raw_url

# ------------------------------------------
# Create Engine
# ------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)