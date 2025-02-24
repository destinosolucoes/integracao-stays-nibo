from datetime import datetime

from .utils import get_next_month_15
from .constants import CATEGORIES_IDS
from .index import find_stakeholder_id

def get_booking_categories(reservation_dto):
    categories = []

    if reservation_dto["owner_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BOOKING_COMISSION"],
            "value": reservation_dto["owner_fee"]
        })

    return categories

def get_comission_data(reservation_dto, transaction_dto):
    reference = transaction_dto["reference"]
    check_out_date = datetime.strptime(reservation_dto["check_out_date"], "%Y-%m-%d")
    dueDate = transaction_dto["dueDate"]
    scheduleDate = transaction_dto["scheduleDate"]
    categories = []

    if reservation_dto["partner_name"] == "API booking.com":
        dueDate = get_next_month_15(check_out_date)
        scheduleDate = get_next_month_15(check_out_date)
        categories = get_booking_categories(reservation_dto)
    
    transaction_dto["categories"] = categories
    transaction_dto["dueDate"] = dueDate
    transaction_dto["scheduleDate"] = scheduleDate
    transaction_dto["stakeholderId"] = find_stakeholder_id("BOOKING.COM BRASIL SERVICOS DE RESERVA DE HOTEIS LTDA.")
    transaction_dto["reference"] = f"{reference}_comissao"

    return transaction_dto