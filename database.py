# sql alchemy, we need a postgre sql db
import logging


from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Provision as PydanticProvision

# Database connection details (replace with your actual credentials)
# Database Connection String
DATABASE_URL = "mysql+pymysql://root:admin@localhost:3306/zkbudget" 


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Provision(Base):
  __tablename__ = 'provision'
  id = Column(Integer, primary_key=True, autoincrement=True)
  description = Column(String)
  provisionType = Column(Integer)  
  provisionDate = Column(DateTime)
  provisionAmount = Column(Float, name='amount')
  user = Column(String)
  



def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
    

def insert_provision(pydanticProv : PydanticProvision) -> int :
  logging.info('Inserting provision')
  sqlProvision = populate_sqlalchemy_from_pydantic(pydanticProv, Provision)
  
  db = get_db()
  db.add(sqlProvision)
  db.commit()
  db.refresh(sqlProvision)
  return _sqlalchemy_to_pydantic(sqlProvision)

    
def get_provisions_from_db(limit : int = None):
  results = SessionLocal().query(Provision).order_by(Provision.id.desc())
  if limit:
    provs =   [_sqlalchemy_to_pydantic(p) for p in results.limit(limit)]
  else:
    provs = [_sqlalchemy_to_pydantic(p) for p in results ] 
  return provs

def _sqlalchemy_to_pydantic(sqlalchemy_obj):
    return PydanticProvision.model_validate(sqlalchemy_obj.__dict__)
  
  
def populate_sqlalchemy_from_pydantic(sqlalchemy_model, pydantic_model):
    """
    Populates an SQLAlchemy model instance with data from a Pydantic model.

    Args:
        db_session: An SQLAlchemy database session.
        sqlalchemy_model: The SQLAlchemy model class.
        pydantic_model: The Pydantic model instance.

    Returns:
        An instance of the SQLAlchemy model populated with data from the Pydantic model.
    """

    sqlalchemy_instance = sqlalchemy_model() 
    for key, value in pydantic_model.dict().items():
        if hasattr(sqlalchemy_instance, key):
            setattr(sqlalchemy_instance, key, value)
    return sqlalchemy_instance
  

  
  