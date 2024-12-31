# sql alchemy, we need a postgre sql db
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection details (replace with your actual credentials)
# Database Connection String
DATABASE_URL = "mysql+pymysql://root:admin@localhost:3306/zkbudget" 


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Provision(Base):
  __tablename__ = 'provision'
  id = Column(Integer, primary_key=True)
  description = Column(String)
  provisionType = Column(Integer)  
  provisionDate = Column(Date)
  provisionAmount = Column(Float, name='amount')
  user = Column(String)
  



def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
    
    
def get_provisions(limit : int = None):
  results = SessionLocal().query(Provision).order_by(Provision.id.desc())
  if limit:
    return [p for p in results.limit(limit)]
  return [p for p in results]
  
  