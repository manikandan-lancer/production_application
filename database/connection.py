from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable missing!")

# -----------------------------------------
# SAFE ENGINE CONFIG FOR CLOUD DATABASES
# -----------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # <-- IMPORTANT: validates connection before use
    pool_recycle=1800,            # recycle connections every 30 min
    pool_size=5,                  # max pool connections
    max_overflow=10,              # extra temporary connections
    connect_args={"sslmode": "require"}  # ensure SSL handshake is correct
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# -----------------------------------------
# GET SESSION FUNCTION
# Ensures fresh, stable DB connection
# -----------------------------------------
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()