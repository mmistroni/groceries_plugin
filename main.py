from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from models import Provision, ItemPayload
from datetime import date
from fastapi.staticfiles import StaticFiles
import random
from typing import List

app = FastAPI()


provision_list: dict[int, Provision] = { 1 : Provision(id=1, provisionType=1, provisionAmount=10.0, description="Eggs", provisionDate='2024-08-02', user="XXXXX"),
                                         2 : Provision(id=2, provisionType=2, provisionAmount=100.0, description="Council", provisionDate='2024-08-02', user="XXXXX"),
                                         3 : Provision(id=3, provisionType=3, provisionAmount=1000.0, description="Car", provisionDate='2024-08-02', user="XXXXX")
                                         }
grocery_list: dict[int, ItemPayload] = {}
templates = Jinja2Templates(directory="public/")

app.mount("/public", StaticFiles(directory="public"), name="static")


@app.get("/")
def root(request:Request):
    result = "Type a number"
    return templates.TemplateResponse('index.html', context={'request' : request, 'result': result})


@app.get("/tester")
def tester(request:Request):
    result = "Type a number"
    return templates.TemplateResponse('sample_bs.html', context={'request' : request, 'result': result})


@app.post("/items/{item_name}/{quantity}")
def add_item(item_name: str, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0.")
    # if item already exists, we'll just add the quantity.
    # get all item names
    items_ids = {item.item_name: item.item_id if item.item_id is not None else 0 for item in grocery_list.values()}
    if item_name in items_ids.keys():
        # get index of item_name in item_ids, which is the item_id
        item_id = items_ids[item_name]
        grocery_list[item_id].quantity += quantity
# otherwise, create a new item
    else:
        # generate an ID for the item based on the highest ID in the grocery_list
        item_id = max(grocery_list.keys()) + 1 if grocery_list else 0
        grocery_list[item_id] = ItemPayload(
            item_id=item_id, item_name=item_name, quantity=quantity
        )

    return {"item": grocery_list[item_id]}

@app.post("/provision/{provisionType}/{amount}/{description}/{provisionDate}/{user}")
def add_provision(provisionType: int, provisionAmount:float, description: str, provisionDate : str,
                  user : str):
    provision_id = _generate_random_int()
    
    return {"status": "SUCCESS"}

@app.post("/addprovision")
def post_provision(provision : Provision):
    provision_id = _generate_random_int()
    provision_list[provision_id] = provision
    # we should use this method and fetch provision
    return {"status": "SUCCESS"}

@app.get("/api/provisions")
def get_provision() -> List[Provision]:
    
    # we should use this method and fetch provision
    data =  [p for p in provision_list.values()]
    return data

def _generate_random_int() -> int:
  """Generates a random integer without a specific range."""
  return random.getrandbits(64)

# table with filters https://designeradeeba.medium.com/building-a-table-filter-using-bootstrap-and-javascript-4edab0ed606e
'''

from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/submit_form")
async def create_item(name: str = Form(...), surname: str = Form(...), age: int = Form(...)):
    return {"name": name, "surname": surname, "age": age}


'''