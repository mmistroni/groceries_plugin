
from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import date
#https://code.visualstudio.com/docs/python/tutorial-fastapi
# Need to add a validate so we can check what is going on

from enum import Enum


class ProvisionType(Enum):
    CAR = 1
    TV = 2
    PHONE = 3
    GAS = 4
    COUNCIL = 5
    HOUSE_INSURANCE = 6
    LIFE_INSURANCE = 7
    OTHER = 8
    
    def __str__(self):
        return f"{self.name}"
    def from_integer(val:int) -> str:
        for  provision_type in ProvisionType:
            if provision_type == val:
                return provision_type.name
def get_provision_type_name(provision_type: ProvisionType) -> str:
    return provision_type.name

class Provision(BaseModel):
  id: Optional[int]
  description: str
  provisionType:ProvisionType  
  provisionDate:date
  provisionAmount:float
  user:str
  
  class Config:
    use_enum_values = False
    orm_model = True
    from_attributes = True
  
  @computed_field(return_type=str)
  def total_cost(self):
    return ProvisionType.from_integer(self.provisionType)

   
    



  
class ItemPayload(BaseModel):
    item_id: Optional[int]
    item_name: str
    quantity: int 