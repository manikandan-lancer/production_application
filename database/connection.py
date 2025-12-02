import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

raw_url = os.getenv("DATABASE_URL")

if not raw_url:
    raise RuntimeError("DATABASE_URL is missing. Add it in Render dashboard.")

# Clean accidental quotes
raw_url = raw_url.strip().strip('"').strip("'")

# Convert postgres/postgresql to required SQLAlchemy URL
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Ensure sslmode=require
if "sslmode=" not in raw_url:
    if "?" in raw_url:
        raw_url += "&sslmode=require"
    else:
        raw_url += "?sslmode=require"

DATABASE_URL = raw_url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)