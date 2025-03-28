"""
Sample data for webhook tests
"""
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to sys.path to allow for importing the API modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def get_sample_reservation_data():
    """
    Return a sample reservation payload
    """
    today = datetime.now()
    checkin = (today + timedelta(days=10)).strftime("%Y-%m-%d")
    checkout = (today + timedelta(days=15)).strftime("%Y-%m-%d")
    
    return {
        "_dt": today.isoformat(),
        "action": "reservation.modified",
        "payload": {
            "id": "12345",
            "type": "booked",
            "checkInDate": checkin,
            "checkOutDate": checkout,
            "_idlisting": "listing123",
            "guestsDetails": {
                "list": [{"name": "Test Guest"}]
            },
            "stats": {"_f_totalPaid": 1000}
        }
    }

def get_sample_reservation_report():
    """
    Return a sample reservation report
    """
    today = datetime.now()
    checkin = (today + timedelta(days=10)).strftime("%Y-%m-%d")
    checkout = (today + timedelta(days=15)).strftime("%Y-%m-%d")
    
    return {
        "id": "12345",
        "partnerName": "website",
        "checkInDate": checkin,
        "checkOutDate": checkout,
        "fee": [
            {"desc": "Taxa de Limpeza", "val": 150},
            {"desc": "Taxa de Serviço", "val": 50},
            {"desc": "Taxa de Eletricidade", "val": 25}
        ],
        "companyCommision": 250,
        "buyPrice": 750,
        "reserveTotal": 1000,
        "creationDate": today.strftime("%Y-%m-%d"),
        "listing": {"internalName": "Test Apartment"},
        "client": {"name": "Test Owner"},
        "ownerFee": []
    }

def get_sample_reservation_dto():
    """
    Return a sample reservation DTO
    """
    today = datetime.now()
    checkin = (today + timedelta(days=10)).strftime("%Y-%m-%d")
    checkout = (today + timedelta(days=15)).strftime("%Y-%m-%d")
    
    return {
        "account_id": "account123",
        "reservation_id": "12345",
        "cost_center_id": "costcenter123",
        "stakeholder_id": "stakeholder123",
        "guest_name": "Test Guest",
        "owner_name": "Test Owner",
        "check_in_date": checkin,
        "check_out_date": checkout,
        "partner_name": "website",
        "listing_internal_name": "Test Apartment",
        "cleaning_fee": 150,
        "electricity_fee": 25,
        "company_comission": 250,
        "buy_price": 750,
        "reserve_total": 1000,
        "total_paid": 1000,
        "service_charge": 50,
        "creation_date": today.strftime("%Y-%m-%d"),
        "iss": 0,
        "owner_fee": 0,
    } 