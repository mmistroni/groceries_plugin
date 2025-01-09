
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional
from datetime import date, datetime
#https://code.visualstudio.com/docs/python/tutorial-fastapi
# Need to add a validate so we can check what is going on

from enum import Enum


class ProvisionType(Enum):
    HOUSE_INSURANCE = 0
    PHONE = 1
    BALANCE = 2
    LIFE_INSURANCE = 3
    BALANCE2 = 4
    WATER = 5
    GAS = 6
    TEMP0 = 7
    CAR = 8
    COUNCIL = 9
    TV = 10
    TEMP = 11
    TEMP2 = 12
    OTHER = 13
    
    def __str__(self):
        return f"{self.name}"
    def from_integer(val:int) -> str:
        for  provision_type in ProvisionType:
            if provision_type == val:
                return provision_type.name
def get_provision_type_name(provision_type: ProvisionType) -> str:
    return provision_type.name


class Provision(BaseModel):
    id: Optional[int] = Field(default=None) 
    description: str
    provisionType:ProvisionType  
    provisionDate:datetime
    provisionAmount:float
    user:str
    
    class Config:
        use_enum_values = False
        orm_model = True
        from_attributes = True
    
    @field_validator('provisionDate')
    @classmethod
    def convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
  
        
    
    @computed_field(return_type=str)
    def total_cost(self):
        return ProvisionType.from_integer(self.provisionType)



   
    



  
class ItemPayload(BaseModel):
    item_id: Optional[int]
    item_name: str
    quantity: int 