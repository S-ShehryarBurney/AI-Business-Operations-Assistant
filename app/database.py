import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()

database_url = os.environ.get("DATABASE_URL")
engine = create_engine(database_url) if database_url else None

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine) if engine else None


def require_database_config():
    if engine is None or SessionLocal is None or database_url is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL before using database-backed features."
        )


def get_session():
    require_database_config()
    return SessionLocal()