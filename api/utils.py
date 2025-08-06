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
    try:
        
        # Initialize variables
        cleaning_fee = 0
        service_charge = 0
        electricity_fee = 0
        owner_fee = 0
        
        # Get partner name
        try:
            partner_name = reservation_report["partnerName"]
        except Exception as e:
            raise Exception(f"Error getting partnerName: {str(e)}")

        # Process fees
        try:
            for fee in reservation_report["fee"]:
                if fee["desc"].lower() == "taxa de limpeza":
                    cleaning_fee = fee["val"]
                elif fee["desc"].lower() == "taxa de eletricidade":
                    electricity_fee = fee["val"]
                elif fee["desc"].lower() == "taxa de serviço":
                    service_charge = fee["val"]
        except Exception as e:
            raise Exception(f"Error processing fees: {str(e)}")
        
        # Process owner fee for booking.com
        try:
            if partner_name == "API booking.com" and len(reservation_report["ownerFee"]) > 0:
                owner_fee = reservation_report["ownerFee"][0]["val"]
        except Exception as e:
            raise Exception(f"Error processing owner fee: {str(e)}")

        # Get listing internal name
        try:
            listing_internal_name = reservation_report["listing"]["internalName"]
        except Exception as e:
            raise Exception(f"Error getting listing internal name: {str(e)}")
        
        # Get guest name
        try:
            guests_details = reservation.get("guestsDetails", {})
            if "list" in guests_details and len(guests_details["list"]) > 0:
                guest_name = guests_details["list"][0]["name"]
            elif "items" in guests_details and len(guests_details["items"]) > 0:
                guest_name = guests_details["items"][0]["name"]
            elif isinstance(guests_details, list) and len(guests_details) > 0:
                guest_name = guests_details[0]["name"]
            else:
                guest_name = "Unknown Guest"
        except Exception as e:
            raise Exception(f"Error getting guest name: {str(e)}")

        # Get other required fields step by step
        try:
            reservation_id = reservation_report["id"]
        except Exception as e:
            raise Exception(f"Error getting reservation ID: {str(e)}")

        try:
            cost_center_id = find_costcenter_id(listing_internal_name)
        except Exception as e:
            raise Exception(f"Error finding cost center ID: {str(e)}")

        try:
            stakeholder_id = find_stakeholder_id(guest_name)
        except Exception as e:
            raise Exception(f"Error finding stakeholder ID: {str(e)}")

        try:
            owner_name = reservation_report["client"]["name"]
        except Exception as e:
            raise Exception(f"Error getting owner name: {str(e)}")

        try:
            check_in_date = reservation_report["checkInDate"]
            check_out_date = reservation_report["checkOutDate"]
        except Exception as e:
            raise Exception(f"Error getting check-in/check-out dates: {str(e)}")

        try:
            company_comission = reservation_report["companyCommision"]
            buy_price = reservation_report["buyPrice"]
            reserve_total = reservation_report["reserveTotal"]
        except Exception as e:
            raise Exception(f"Error getting financial data: {str(e)}")

        try:
            total_paid = reservation["stats"]["_f_totalPaid"]
        except Exception as e:
            raise Exception(f"Error getting total paid from stats: {str(e)}")

        try:
            creation_date = reservation_report["creationDate"]
        except Exception as e:
            raise Exception(f"Error getting creation date: {str(e)}")

        try:
            iss = reservation_report["iss"] if "iss" in reservation_report else 0
        except Exception as e:
            raise Exception(f"Error getting ISS: {str(e)}")

        # Build the final DTO
        try:
            dto = {
                "account_id": NIBO_ACCOUNT_ID,
                "reservation_id": reservation_id,
                "cost_center_id": cost_center_id,
                "stakeholder_id": stakeholder_id,
                "guest_name": guest_name,
                "owner_name": owner_name,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "partner_name": partner_name,
                "listing_internal_name": listing_internal_name,
                "cleaning_fee": cleaning_fee,
                "electricity_fee": electricity_fee,
                "company_comission": company_comission,
                "buy_price": buy_price,
                "reserve_total": reserve_total,
                "total_paid": total_paid,
                "service_charge": service_charge,
                "creation_date": creation_date,
                "iss": iss,
                "owner_fee": owner_fee,
            }
            return dto
        except Exception as e:
            raise Exception(f"Error building final DTO: {str(e)}")
            
    except Exception as e:
        raise e

def calculate_expedia(reservation_dto):
    if reservation_dto["partner_name"] == "API expedia":
        reservation_dto["cleaning_fee"] = 190
        balance = reservation_dto["reserve_total"] - reservation_dto["cleaning_fee"]

        reservation_dto["iss"] = balance * 0.04762
        balance = balance - reservation_dto["iss"]

        reservation_dto["company_comission"] = balance * 0.25
        reservation_dto["buy_price"] = balance - reservation_dto["company_comission"]

    return reservation_dto
