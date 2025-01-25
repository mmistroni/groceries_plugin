from fastapi import FastAPI, Request, Query, Depends
from fastapi.templating import Jinja2Templates
from models import Provision, ItemPayload, ProvisionType
from datetime import date, datetime
from fastapi.staticfiles import StaticFiles
import logging
import random
from typing import List
from database import get_db, get_provisions_from_db, insert_provision, delete_provision, update_provision

app = FastAPI()

async def get_provisions():
    # Load the list of items from database.py (replace with your actual loading logic)
    provs = get_provisions_from_db(limit=40)
    provision_list =  dict((prov.id, prov) for prov in provs)
    return provs


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
    return templates.TemplateResponse('dtsample.html', context={'request' : request, 'result': result})


@app.post("/addprovision2")
async def post_provision2(request : Request):
    provision_id = _generate_random_int()
    request_data = await request.json()
    
    provision_type_string = request_data.get("provisionType")
    provision_type_enum = ProvisionType[provision_type_string]

    
    new_provision = Provision(
        provisionType=provision_type_enum,
        provisionAmount=request_data['provisionAmount'],
        description=request_data['description'],
        provisionDate=datetime.strptime(request_data['provisionDate'], '%Y%m%d'),
        user=request_data['user']
    )
    insert_provision(new_provision)
    #provision_list[provision_id] = new_provision
    # we should use this method and fetch provision
    return {"status": "SUCCESS"}


@app.post("/updateprovision")
async def post_provision2(request : Request):
    request_data = await request.json()
    
    provision_id = int(request_data.get("id"))    
    provision_type_string = request_data.get("provisionType")
    provision_type_enum = ProvisionType[provision_type_string]


    data = {'provisionAmount' : float(request_data['provisionAmount']),
            'description' : request_data['description'],
            'user'  : request_data['user'],
            'provisionType' : provision_type_enum,
            'id' : provision_id,
            'provisionDate' : datetime.strptime(request_data['provisionDate'], '%Y%m%d')}

    existing = Provision(**data);
    update_provision(existing);
    
    
    return {"status": "SUCCESS"}


@app.post("/deleteprovision/")
async def deleteProvision(request : Request):
    
    request_data = await request.json()
    provision_id = int(request_data.get("id"))
    logging.info(f'We should delete provision with id:{provision_id}')
    
    delete_provision(provision_id)
    
    
    return {"status": "SUCCESS"}

@app.get("/api/provisions")
async def get_provision(
    option: str = Query(None),
    start: str = Query(None),
    end: str = Query(None)
    ) -> List[Provision] :
    
    # we should use this method and fetch provision
    data =  await get_provisions() #[p for p in provision_list.values()]
    
    if option:
        # Filter provisions based on the option
        # ...
        logging.info(f'Selected option:{option}')
        data = [p for p in data if p.provisionType.name == option]
        logging.info(f'Obtained:{len(data)}')
        

    if  start and end:
        logging.info(f'start type:{type(start)}')
        cob_start = datetime.strptime(start, '%Y-%m-%d').date()
        cob_end = datetime.strptime(end, '%Y-%m-%d').date()
        
        filtered =  [p for p in data if p.provisionDate >= cob_start \
                        and p.provisionDate <= cob_end]
    return filtered

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