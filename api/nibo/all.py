# Consolidated Nibo module with all functionality
import requests

# Constants
NIBO_CLIENT_SECRET = "YOUR_SECRET_HERE"  # Will be replaced by environment variable in bundle.py

# Import utilities
def sanitize_dates(payload):
    """Sanitize dates in the payload to be compatible with Nibo API"""
    # Implementation would go here
    return payload

# Core functionality from index.py
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

# Credit schedules
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

# Transaction functions from transaction.py
def get_transaction(transaction_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/transactions/{transaction_id}"

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

def get_receivables_by_customer(customer_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/receivables?$filter=customerId eq '{customer_id}'"

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

# Operational functions from operational.py
def create_operational_account(payload):
    url = "https://api.nibo.com.br/empresas/v1/operational-accounts"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_operational_account error", response["error_description"], payload)
        return False

    return response

# Commission functions from comission.py
def create_commission(payload):
    url = "https://api.nibo.com.br/empresas/v1/commissions"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_commission error", response["error_description"], payload)
        return False

    return response

# Receivables functions from receivables.py
def create_receivable(payload):
    url = "https://api.nibo.com.br/empresas/v1/receivables"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_receivable error", response["error_description"], payload)
        return False

    return response 