import requests
import time
import logging

from .constants import STAYS_SECRET

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8  # seconds - must be under Vercel's 10s limit
MAX_RETRIES = 2


def _request_with_retry(method, url, headers, json=None, retries=MAX_RETRIES):
    """Make HTTP request with timeout and retry on transient failures"""
    for attempt in range(retries):
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=json, headers=headers, timeout=REQUEST_TIMEOUT)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                wait = 1 * (attempt + 1)
                logger.warning(f"Stays API retry {attempt+1}/{retries} for {url}: {e}")
                time.sleep(wait)
            else:
                logger.error(f"Stays API failed after {retries} attempts: {url}: {e}")
                raise


def get_reservation(reservation_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/reservations/{reservation_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = _request_with_retry("GET", url, headers)

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

    response = _request_with_retry("POST", url, headers, json=payload)
    response = response.json()

    for item in response:
        if item["_id"] == reservation["_id"]:
            return item
    
    return False

def get_listing(listing_id: str):
    url = f"https://adsa.stays.com.br/external/v1/content/listings/{listing_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = _request_with_retry("GET", url, headers)

    return response.json()

def get_client(client_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/clients/{client_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = _request_with_retry("GET", url, headers)

    return response.json()