import json

from sqlmodel import Field, SQLModel
from api.nibo.constants import NIBO_ACCOUNT_ID
from api.nibo.index import find_costcenter_id, find_stakeholder_id
from .constants import STAYS_CLIENT_LOGIN

class Requests(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dt: str = Field(default=None)
    action: str = Field(default=None)
    payload: str = Field(default=None)

    def create(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)
        return self
    
class Logs(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dt: str = Field(default=None)
    action: str = Field(default=None)
    payload: str = Field(default=None)
    internal_payload: str = Field(default=None)

    def create(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)
        return self

def validate_header(headers):
    if "x-stays-client-id" not in headers or "x-stays-signature" not in headers:
        return False

    stays_login = headers["x-stays-client-id"]

    if stays_login != STAYS_CLIENT_LOGIN:
        return False

    return True

def create_request_log(dt,action,payload,session):
    Requests(
        dt=dt,
        action=action,
        payload=json.dumps(payload, ensure_ascii=False)
    ).create(session=session)

def create_log(dt,action,payload,internal_payload,session):
    Logs(
         dt=dt,
        action=action,
        payload=json.dumps(payload, ensure_ascii=False),
        internal_payload=json.dumps(internal_payload, ensure_ascii=False)
    ).create(session=session)

def create_reservation_dto(reservation_report, reservation):
    cleaning_fee = 0
    service_charge = 0
    electricity_fee = 0

    owner_fee = 0
    partner_name = reservation_report["partnerName"]

    for fee in reservation_report["fee"]:
        if fee["desc"].lower() == "taxa de limpeza":
            cleaning_fee = fee["val"]

        if fee["desc"].lower() == "taxa de eletricidade":
            electricity_fee = fee["val"]

        if fee["desc"].lower() == "taxa de serviço":
            service_charge = fee["val"]
    
    if partner_name == "API booking.com" and len(reservation_report["ownerFee"]) > 0:
        owner_fee = reservation_report["ownerFee"][0]["val"]

    listing_internal_name = reservation_report["listing"]["internalName"]
    guest_name = reservation["guestsDetails"]["list"][0]["name"]

    return {
        "account_id": NIBO_ACCOUNT_ID,
        "reservation_id": reservation_report["id"],
        "cost_center_id": find_costcenter_id(listing_internal_name),
        "stakeholder_id": find_stakeholder_id(guest_name),
        "guest_name": guest_name,
        "owner_name": reservation_report["client"]["name"],
        "check_in_date": reservation_report["checkInDate"],
        "check_out_date": reservation_report["checkOutDate"],
        "partner_name": partner_name,
        "listing_internal_name": listing_internal_name,
        "cleaning_fee": cleaning_fee,
        "electricity_fee": electricity_fee,
        "company_comission": reservation_report["companyCommision"],
        "buy_price": reservation_report["buyPrice"],
        "reserve_total": reservation_report["reserveTotal"],
        "total_paid": reservation["stats"]["_f_totalPaid"],
        "service_charge": service_charge,
        "creation_date": reservation_report["creationDate"],
        "iss": reservation_report["iss"] if "iss" in reservation_report else 0,
        "owner_fee": owner_fee,
    }

def calculate_expedia(reservation_dto):
    if reservation_dto["partner_name"] == "API expedia":
        reservation_dto["cleaning_fee"] = 190
        balance = reservation_dto["reserve_total"] - reservation_dto["cleaning_fee"]

        reservation_dto["iss"] = balance * 0.04762
        balance = balance - reservation_dto["iss"]

        reservation_dto["company_comission"] = balance * 0.25
        reservation_dto["buy_price"] = balance - reservation_dto["company_comission"]

    return reservation_dto
