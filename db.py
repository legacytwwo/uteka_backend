from os import environ
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
Base = declarative_base()
engine = create_engine(environ["SQLALCHEMY_DATABASE_URL"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from models.core import *

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()