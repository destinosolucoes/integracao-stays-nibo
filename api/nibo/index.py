import requests
from fastapi import APIRouter, FastAPI, Body

from .utils import sanitize_dates
from .constants import NIBO_CLIENT_SECRET

def create_debit_schedule(payload):
    url = "https://api.nibo.com.br/empresas/v1/schedules/debit"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = sanitize_dates(payload)
    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_debit_schedule error", response["error_description"], payload)
        return False

    return response

def get_debit_schedule(reservation_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/debit?$filter=contains(description,'{reservation_id}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"]

def update_debit_schedule(schedule_id, payload):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/debit/{schedule_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = sanitize_dates(payload)
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 204:
        return True

    response = response.json()

    if "error" in response:
        print("update_debit_schedule error", response["error_description"], payload)
        return False

    return response

def delete_debit_schedule(schedule_id):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/debit/{schedule_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return True

    response = response.json()

    if "error" in response:
        print("delete_debit_schedule error", response["error_description"])
        return False

    return response

def create_credit_schedule(payload):
    url = "https://api.nibo.com.br/empresas/v1/schedules/credit"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = sanitize_dates(payload)
    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_credit_schedule error", response["error_description"], payload)
        return False

    return response

def get_credit_schedule(reservation_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/credit?$filter=contains(description,'{reservation_id}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"]

def update_credit_schedule(schedule_id, payload):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/credit/{schedule_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = sanitize_dates(payload)
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 204:
        return True

    response = response.json()

    if "error" in response:
        print("update_credit_schedule error", response["error_description"], payload)
        return False

    return response

def delete_credit_schedule(schedule_id):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/credit/{schedule_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return True

    response = response.json()

    if "error" in response:
        print("delete_credit_schedule error", response["error_description"])
        return False

    return response

def get_stakeholder(name: str):
    url = f"https://api.nibo.com.br/empresas/v1/customers?$filter=contains(name,'{name}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"][0] if len(response["items"]) > 0 else False

def get_stakeholder_by_id(stakeholder_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/customers/{stakeholder_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response

def create_stakeholder(name: str):
    url = "https://api.nibo.com.br/empresas/v1/customers"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = {
        "name": name
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.text.replace('"', '')

def get_supplier(name: str):
    url = f"https://api.nibo.com.br/empresas/v1/suppliers?$filter=contains(name,'{name}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"][0] if len(response["items"]) > 0 else False

def get_supplier_by_id(supplier_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/suppliers/{supplier_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response

def create_supplier(name: str):
    url = "https://api.nibo.com.br/empresas/v1/suppliers"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = {
        "name": name
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.text.replace('"', '')

def get_costcenter(description: str):
    url = f"https://api.nibo.com.br/empresas/v1/costcenters?$filter=contains(description,'{description}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"][0] if len(response["items"]) > 0 else False

def get_costcenter_by_id(costcenters_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/costcenters/{costcenters_id}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response

def create_costcenter(description: str):
    url = "https://api.nibo.com.br/empresas/v1/costcenters"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    payload = {
        "Description": description
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.text.replace('"', '')

def find_stakeholder_id(name: str):
    stakeholder = get_stakeholder(name)

    if stakeholder is False:
        stakeholder_id = create_stakeholder(name)
        stakeholder = get_stakeholder_by_id(stakeholder_id)

    return stakeholder["id"]

def find_supplier_id(name: str):
    supplier = get_supplier(name)

    if supplier is False:
        supplier_id = create_supplier(name)
        supplier = get_supplier_by_id(supplier_id)

    return supplier["id"]

def find_costcenter_id(description):
    costcenter = get_costcenter(description)
    if costcenter:
        return costcenter["id"]
    
    costcenter = create_costcenter(description)
    return costcenter["id"]

# Register routes with the main FastAPI app
def register_routes(app: FastAPI):
    router = APIRouter(prefix="/api/nibo", tags=["nibo"])
    
    @router.post("/debit-schedule")
    def create_debit_schedule_endpoint(payload: dict = Body(...)):
        return create_debit_schedule(payload)
    
    @router.get("/debit-schedule/{reservation_id}")
    def get_debit_schedule_endpoint(reservation_id: str):
        return get_debit_schedule(reservation_id)
    
    @router.put("/debit-schedule/{schedule_id}")
    def update_debit_schedule_endpoint(schedule_id: str, payload: dict = Body(...)):
        return update_debit_schedule(schedule_id, payload)
    
    @router.delete("/debit-schedule/{schedule_id}")
    def delete_debit_schedule_endpoint(schedule_id: str):
        return delete_debit_schedule(schedule_id)
    
    @router.post("/credit-schedule")
    def create_credit_schedule_endpoint(payload: dict = Body(...)):
        return create_credit_schedule(payload)
    
    @router.get("/credit-schedule/{reservation_id}")
    def get_credit_schedule_endpoint(reservation_id: str):
        return get_credit_schedule(reservation_id)
    
    @router.put("/credit-schedule/{schedule_id}")
    def update_credit_schedule_endpoint(schedule_id: str, payload: dict = Body(...)):
        return update_credit_schedule(schedule_id, payload)
    
    @router.delete("/credit-schedule/{schedule_id}")
    def delete_credit_schedule_endpoint(schedule_id: str):
        return delete_credit_schedule(schedule_id)
    
    @router.get("/stakeholder/{name}")
    def get_stakeholder_endpoint(name: str):
        return get_stakeholder(name)
    
    @router.get("/stakeholder/id/{stakeholder_id}")
    def get_stakeholder_by_id_endpoint(stakeholder_id: str):
        return get_stakeholder_by_id(stakeholder_id)
    
    @router.post("/stakeholder")
    def create_stakeholder_endpoint(name: str):
        return create_stakeholder(name)
    
    @router.get("/supplier/{name}")
    def get_supplier_endpoint(name: str):
        return get_supplier(name)
    
    @router.get("/supplier/id/{supplier_id}")
    def get_supplier_by_id_endpoint(supplier_id: str):
        return get_supplier_by_id(supplier_id)
    
    @router.post("/supplier")
    def create_supplier_endpoint(name: str):
        return create_supplier(name)
    
    @router.get("/costcenter/{description}")
    def get_costcenter_endpoint(description: str):
        return get_costcenter(description)
    
    @router.get("/costcenter/id/{costcenter_id}")
    def get_costcenter_by_id_endpoint(costcenter_id: str):
        return get_costcenter_by_id(costcenter_id)
    
    @router.post("/costcenter")
    def create_costcenter_endpoint(description: str):
        return create_costcenter(description)
    
    app.include_router(router)