import requests
from fastapi import APIRouter, FastAPI

from .constants import STAYS_SECRET

def get_reservation(reservation_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/reservations/{reservation_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

def get_reservation_report(reservation):
    url = "https://adsa.stays.com.br/external/v1/booking/reservations-export"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    payload = {
        "from": reservation["checkInDate"],
        "to": reservation["checkOutDate"],
        "dateType": "arrival",
        "listingId": [reservation["_idlisting"]]
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if len(response) == 0:
        return False

    return response[0]

def get_listing(listing_id: str):
    url = f"https://adsa.stays.com.br/external/v1/content/listings/{listing_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

def get_client(client_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/clients/{client_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

# New function to register routes with the main app
def register_routes(app: FastAPI):
    router = APIRouter(prefix="/api/stays", tags=["stays"])
    
    @router.get("/reservation/{reservation_id}")
    def reservation_endpoint(reservation_id: str):
        return get_reservation(reservation_id)
    
    @router.get("/listing/{listing_id}")
    def listing_endpoint(listing_id: str):
        return get_listing(listing_id)
    
    @router.get("/client/{client_id}")
    def client_endpoint(client_id: str):
        return get_client(client_id)
    
    app.include_router(router)