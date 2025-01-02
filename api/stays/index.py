import requests

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