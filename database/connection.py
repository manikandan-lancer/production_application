from sqlalchemy import create_engine
from config.settings import *

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?sslmode=require"
)

engine = create_engine(DATABASE_URL, echo=False)