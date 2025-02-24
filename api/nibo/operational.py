from datetime import datetime, timedelta

from .utils import get_next_month_15
from .index import find_supplier_id
from .constants import CATEGORIES_IDS

def get_regular_categories(reservation_dto):
    categories = []

    if reservation_dto["buy_price"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["OWNER_FEE"],
            "value": reservation_dto["buy_price"]
        })

    if reservation_dto["electricity_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["OWNER_FEE"],
            "value": reservation_dto["electricity_fee"]
        })

    return categories

def get_operational_data(reservation_dto, transaction_dto):
    reference = transaction_dto["reference"]
    check_out_date = datetime.strptime(reservation_dto["check_out_date"], "%Y-%m-%d")
    dueDate = transaction_dto["dueDate"]
    scheduleDate = transaction_dto["scheduleDate"]
    categories = []

    if reservation_dto["partner_name"] == "API airbnb":
        dueDate = get_next_month_15(check_out_date)
        scheduleDate = get_next_month_15(check_out_date)
        categories = get_regular_categories(reservation_dto)

    if reservation_dto["partner_name"] == "API decolar":
        dueDate = get_next_month_15(check_out_date)
        scheduleDate = get_next_month_15(check_out_date)
        categories = get_regular_categories(reservation_dto)

    if reservation_dto["partner_name"] == "API booking.com":
        dueDate = get_next_month_15(check_out_date)
        scheduleDate = get_next_month_15(check_out_date)
        categories = get_regular_categories(reservation_dto)

    if reservation_dto["partner_name"] == "API expedia":
        dueDate = check_out_date + timedelta(days=32)
        scheduleDate = check_out_date + timedelta(days=32)
        categories = get_regular_categories(reservation_dto)

    if reservation_dto["partner_name"] in ["website", "diretas"]:
        dueDate = get_next_month_15(check_out_date)
        scheduleDate = get_next_month_15(check_out_date)
        categories = get_regular_categories(reservation_dto)


    transaction_dto["categories"] = categories
    transaction_dto["dueDate"] = dueDate
    transaction_dto["scheduleDate"] = scheduleDate
    transaction_dto["stakeholderId"] = find_supplier_id(reservation_dto["owner_name"])
    transaction_dto["reference"] = f"{reference}_operacional"

    return transaction_dto