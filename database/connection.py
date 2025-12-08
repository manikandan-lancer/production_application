from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://...YOUR DATABASE URL..."

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ----------------------------
# FIX: Add get_session function
# ----------------------------
def get_session():
    return SessionLocal()
