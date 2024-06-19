# sql alchemy, we need a postgre sql db
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection details (replace with your actual credentials)
DATABASE_URL = "sqlite:///todo.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ToDoDB(Base):
  __tablename__ = "todos"

  id = Column(Integer, primary_key=True)
  description = Column(String)
  provisionDate = Column(Date)
  amount  = Column(Float)
  user = Column(String)
  

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()