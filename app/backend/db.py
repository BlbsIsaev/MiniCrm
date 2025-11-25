# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from dotenv import load_dotenv
import os
load_dotenv()


SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./minicrm.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()