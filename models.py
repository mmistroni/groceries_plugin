
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
#https://code.visualstudio.com/docs/python/tutorial-fastapi
# Need to add a validate so we can check what is going on

from enum import Enum


class ProvisionType(Enum):
    CAR = 1
    TV = 2
    PHONE = 3,
    GAS = 4,
    COUNCIL = 5,
    HOUSE_INSURANCE = 6,
    LIFE_INSURANCE = 7,
    OTHER = 8

class Provision(BaseModel):
  id: Optional[int]
  description: str
  provisionType:ProvisionType
  provisionDate:str
  provisionAmount:float
  user:str

  @property
  def provisionTypeName(self):
        return self.provisionType.name
      
  class Config:
        extra = "forbid"  # Optional: Prevent unexpected fields
        orm_mode = True  # Optional: For ORM integration
        arbitrary_types_allowed = True  # Allow custom types like enums
        fields = {"provisionTypeName"}  # Include the custom property in serialization



  
class ItemPayload(BaseModel):
    item_id: Optional[int]
    item_name: str
    quantity: int 