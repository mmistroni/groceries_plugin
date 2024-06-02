
from pydantic import BaseModel
from datetime import date

class Provision(BaseModel):
  id: int | None = None
  description: str
  provisionDate: date
  amount:float
  user:str 