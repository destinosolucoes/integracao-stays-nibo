from .index import create_credit_schedule, create_debit_schedule, get_credit_schedule, get_debit_schedule, update_credit_schedule, update_debit_schedule, delete_credit_schedule, delete_debit_schedule
from .receivables import get_receivable_data
from .operational import get_operational_data
from .comission import get_comission_data
from .constants import CATEGORIES_IDS

def format_description(reservation_dto):
    reservation_id = reservation_dto["reservation_id"]
    listing_internal_name = reservation_dto["listing_internal_name"]
    partner_name = reservation_dto["partner_name"]

    return f"Reserva #{reservation_id} - {listing_internal_name} - {partner_name}"

def change_categories_value(reservation_dto, schedule_dto):
    transaction_dto = {
        "stakeholderId": reservation_dto["stakeholder_id"],
        "description": format_description(reservation_dto),
        "reference": reservation_dto["reservation_id"],
        "dueDate": "",
        "scheduleDate": "",
        "costCenterValueType": "1",
        "costCenters": [
            {
                "costCenterId": reservation_dto["cost_center_id"],
                "percent": 100
            }
        ],
        "accrualDate": reservation_dto["check_in_date"],
        "categories": []
    }

    if "operacional" in schedule_dto["reference"]:
        transaction_dto = get_operational_data(reservation_dto, transaction_dto)
    
    elif "comissao" in schedule_dto["reference"]:
        transaction_dto = get_comission_data(reservation_dto, transaction_dto)

    else:
        transaction_dto = get_receivable_data(reservation_dto, transaction_dto)

    return transaction_dto["categories"]

def get_center_cost(schedule_dto):
    center_cost = 0

    for category in schedule_dto["categories"]:
        center_cost = center_cost + category["value"]

    return center_cost

def send_transaction(reservation_dto, type: str):
    transaction_dto = {
        "stakeholderId": reservation_dto["stakeholder_id"],
        "description": format_description(reservation_dto),
        "reference": reservation_dto["reservation_id"],
        "dueDate": "",
        "scheduleDate": "",
        "costCenterValueType": "1",
        "costCenters": [
            {
                "costCenterId": reservation_dto["cost_center_id"],
                "percent": 100
            }
        ],
        "accrualDate": reservation_dto["check_in_date"],
        "categories": []
    }

    if type == "operational":
        transaction_dto = get_operational_data(reservation_dto, transaction_dto)
        return create_debit_schedule(transaction_dto)
    
    elif type == "receivable":
        transaction_dto = get_receivable_data(reservation_dto, transaction_dto)
        return create_credit_schedule(transaction_dto)

    elif type == "comission":
        transaction_dto = get_comission_data(reservation_dto, transaction_dto)
        return create_credit_schedule(transaction_dto)

    return create_credit_schedule(transaction_dto)

def update_transaction(reservation_report, reservation_dto):
    debit_schedules = get_debit_schedule(reservation_dto["reservation_id"])
    credit_schedules = get_credit_schedule(reservation_dto["reservation_id"])

    for debit_schedule in debit_schedules:
        debit_schedule["categories"] = change_categories_value(reservation_dto, debit_schedule)
        debit_schedule["stakeholderId"] = debit_schedule["stakeholder"]["id"]
        
        if len(debit_schedule["costCenters"]) > 0:
            debit_schedule["costCenters"][0]["value"] = get_center_cost(debit_schedule)
        
        transaction = update_debit_schedule(debit_schedule["scheduleId"], debit_schedule)
        if transaction is False:
            print("Erro ao criar update_debit_schedule")
            print(transaction)

    for credit_schedule in credit_schedules:
        credit_schedule["categories"] = change_categories_value(reservation_dto, credit_schedule)
        credit_schedule["stakeholderId"] = credit_schedule["stakeholder"]["id"]
        
        if len(credit_schedule["costCenters"]) > 0:
            credit_schedule["costCenters"][0]["value"] = get_center_cost(credit_schedule)

        transaction = update_credit_schedule(credit_schedule["scheduleId"], credit_schedule)
        if transaction is False:
            print("Erro ao criar update_credit_schedule")
            print(transaction)

    return True

def delete_transaction(reservation_id: str):
    debit_schedules = get_debit_schedule(reservation_id)
    credit_schedules = get_credit_schedule(reservation_id)

    for debit_schedule in debit_schedules:
        transaction = delete_debit_schedule(debit_schedule["scheduleId"])
        if transaction is False:
            print("Erro ao deletar delete_debit_schedule")
            print(transaction)

    for credit_schedule in credit_schedules:
        transaction = delete_credit_schedule(credit_schedule["scheduleId"])
        if transaction is False:
            print("Erro ao deletar delete_credit_schedule")
            print(transaction)

    return True