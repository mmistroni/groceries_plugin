
from pydantic import BaseModel
from typing import Optional
from datetime import date
#https://code.visualstudio.com/docs/python/tutorial-fastapi
class Provision(BaseModel):
  id: Optional[int]
  description: str
  provisionType:str
  provisionDate: date
  amount:float
  user:str
  
class ItemPayload(BaseModel):
    item_id: Optional[int]
    item_name: str
    quantity: int 