
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
#https://code.visualstudio.com/docs/python/tutorial-fastapi
# Need to add a validate so we can check what is going on
class Provision(BaseModel):
  id: Optional[int]
  description: str
  provisionType:int
  provisionDate:str
  provisionAmount:float
  user:str
  
class ItemPayload(BaseModel):
    item_id: Optional[int]
    item_name: str
    quantity: int 