import requests
import time
import logging

from .utils import sanitize_dates
from .constants import NIBO_CLIENT_SECRET

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8  # seconds
MAX_RETRIES = 2


def _nibo_request(method, url, headers, json=None, retries=MAX_RETRIES):
    """Make HTTP request to Nibo API with timeout and retry"""
    for attempt in range(retries):
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=json, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == "PUT":
                response = requests.put(url, json=json, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                wait = 1 * (attempt + 1)
                logger.warning(f"Nibo API retry {attempt+1}/{retries} for {url}: {e}")
                time.sleep(wait)
            else:
                logger.error(f"Nibo API failed after {retries} attempts: {url}: {e}")
                raise

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
    costcenters = get_costcenter(description)

    if costcenters is False:
        costcenters_id = create_costcenter(description)
        costcenters = get_costcenter_by_id(costcenters_id)

    return costcenters["costCenterId"]