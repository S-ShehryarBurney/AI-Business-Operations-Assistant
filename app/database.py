import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL not found.")

engine = create_engine(database_url)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)