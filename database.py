# sql alchemy, we need a postgre sql db
import logging
from sqlalchemy import func, extract
import os

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Provision as PydanticProvision
from models import ProvisionType 
# Database connection details (replace with your actual credentials)
# Database Connection String
DATABASE_URL = f"mysql+pymysql://{os.environ['ZKBUDGET_DB']}" # get it from env


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Provision(Base):
  __tablename__ = 'PROVISION'
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
    

def insert_provision(pydanticProv : PydanticProvision) -> PydanticProvision :
  logging.info('Inserting provision')
  sqlProvision = populate_sqlalchemy_from_pydantic( Provision, pydanticProv)
  db = SessionLocal()
  db.add(sqlProvision)
  db.commit()
  db.refresh(sqlProvision)
  return _sqlalchemy_to_pydantic(sqlProvision)


def update_provision(pydanticProv : PydanticProvision) -> PydanticProvision :
  logging.info('Updatingg provision')
  session = SessionLocal()
  provision_id = pydanticProv.id
  provision = session.query(Provision).filter(Provision.id == provision_id).first()
  if provision:
      provision = populate_sqlalchemy_from_pydantic(provision, pydanticProv, update=True)
      session.commit()
      print(f"Provision with ID {provision_id} updated successfully.")
  else:
      print(f"Provision with ID {provision_id} not found.")
  return _sqlalchemy_to_pydantic(provision)

def delete_provision(provision_id: int) -> None :
  """
    Deletes a Provision record from the database by its ID.

    Args:
        provision_id: The ID of the Provision to delete.
    """
    
  logging.info('Updatingg provision')
  session = SessionLocal()
  provision = session.query(Provision).filter(Provision.id == provision_id).first()
  if provision:
      session.delete(provision)
      session.commit()
      print(f"Provision with ID {provision_id} deleted successfully.")
  else:
      print(f"Provision with ID {provision_id} not found.")

  
    
def get_provisions_from_db(limit : int = None):
  results = SessionLocal().query(Provision).order_by(Provision.provisionDate.desc())
  if limit:
    provs =   [_sqlalchemy_to_pydantic(p) for p in results.limit(limit)]
  else:
    provs = [_sqlalchemy_to_pydantic(p) for p in results ] 
  return provs

def _sqlalchemy_to_pydantic(sqlalchemy_obj):
    return PydanticProvision.model_validate(sqlalchemy_obj.__dict__)
  

def query_for_charts():
    query = SessionLocal().query(
        extract('year', Provision.provisionDate).label('year'),
        extract('month', Provision.provisionDate).label('month'),
        Provision.provision,
        func.sum(Provision.provisionAmount).label('total_amount')
    ).group_by(
        extract('year', Provision.provisionDate),
        extract('month', Provision.provisionDate),
        Provision.provisionType
    ).order_by(
        extract('year', Provision.provisionDate),
        extract('month', Provision.provisionDate),
        Provision.provisionType
    )

    results = query.all()
    provs = [_sqlalchemy_to_pydantic(p) for p in results ]
    return provs

  
def populate_sqlalchemy_from_pydantic(sqlalchemy_model, pydantic_model, update=False):
    """
    Populates an SQLAlchemy model instance with data from a Pydantic model.

    Args:
        db_session: An SQLAlchemy database session.
        sqlalchemy_model: The SQLAlchemy model class.
        pydantic_model: The Pydantic model instance.

    Returns:
        An instance of the SQLAlchemy model populated with data from the Pydantic model.
    """

    sqlalchemy_instance = sqlalchemy_model()  if not update else sqlalchemy_model
    for key, value in pydantic_model.dict().items():
        if hasattr(sqlalchemy_instance, key):
            if isinstance(value, ProvisionType): 
                setattr(sqlalchemy_instance, key, value.value) 
            else:
                setattr(sqlalchemy_instance, key, value)
    return sqlalchemy_instance
  

  
  