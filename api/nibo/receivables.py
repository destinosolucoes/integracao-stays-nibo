from datetime import datetime, timedelta

from .utils import check_special_booking, get_next_month_15
from .constants import CATEGORIES_IDS

def get_airbnb_categories(reservation_dto):
    categories = []

    if reservation_dto["company_comission"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["COMPANY_COMISSION"],
            "value": reservation_dto["company_comission"]
        })

    if reservation_dto["cleaning_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["CLEANING_FEE"],
            "value": reservation_dto["cleaning_fee"]
        })

    if reservation_dto["listing_internal_name"] not in ["APTO 327 - BARRA BALI", "API booking.com"]:
        if reservation_dto["buy_price"] > 0:
            categories.append({
                "categoryId": CATEGORIES_IDS["BUY_PRICE"],
                "value": reservation_dto["buy_price"]
            })

        if reservation_dto["electricity_fee"] > 0:
            categories.append({
                "categoryId": CATEGORIES_IDS["ELECTRICITY_FEE"],
                "value": reservation_dto["electricity_fee"]
            })

    return categories

def get_decolar_categories(reservation_dto):
    categories = []

    if reservation_dto["company_comission"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["COMPANY_COMISSION"],
            "value": reservation_dto["company_comission"]
        })

    if reservation_dto["cleaning_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["CLEANING_FEE"],
            "value": reservation_dto["cleaning_fee"]
        })

    if reservation_dto["buy_price"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BUY_PRICE"],
            "value": reservation_dto["buy_price"]
        })

    if reservation_dto["electricity_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["ELECTRICITY_FEE"],
            "value": reservation_dto["electricity_fee"]
        })

    if reservation_dto["iss"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["ISS"],
            "value": reservation_dto["iss"]
        })

    return categories

def get_booking_categories(reservation_dto, special_booking):
    categories = []

    if reservation_dto["company_comission"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["COMPANY_COMISSION"],
            "value": reservation_dto["company_comission"]
        })

    if reservation_dto["cleaning_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["CLEANING_FEE"],
            "value": reservation_dto["cleaning_fee"]
        })

    if reservation_dto["buy_price"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BUY_PRICE"],
            "value": reservation_dto["buy_price"]
        })

    if reservation_dto["electricity_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["ELECTRICITY_FEE"],
            "value": reservation_dto["electricity_fee"]
        })

    if special_booking and reservation_dto["owner_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BOOKING_ADVANCE"],
            "value": reservation_dto["owner_fee"]
        })

    return categories

def get_expedia_categories(reservation_dto):
    categories = []

    if reservation_dto["company_comission"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["COMPANY_COMISSION"],
            "value": reservation_dto["company_comission"]
        })

    if reservation_dto["cleaning_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["CLEANING_FEE"],
            "value": reservation_dto["cleaning_fee"]
        })

    if reservation_dto["buy_price"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BUY_PRICE"],
            "value": reservation_dto["buy_price"]
        })

    if reservation_dto["electricity_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["ELECTRICITY_FEE"],
            "value": reservation_dto["electricity_fee"]
        })

    return categories

def get_website_categories(reservation_dto):
    categories = []

    if reservation_dto["company_comission"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["COMPANY_COMISSION"],
            "value": reservation_dto["company_comission"]
        })

    if reservation_dto["cleaning_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["CLEANING_FEE"],
            "value": reservation_dto["cleaning_fee"]
        })

    if reservation_dto["buy_price"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["BUY_PRICE"],
            "value": reservation_dto["buy_price"]
        })

    if reservation_dto["electricity_fee"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["ELECTRICITY_FEE"],
            "value": reservation_dto["electricity_fee"]
        })

    if reservation_dto["service_charge"] > 0:
        categories.append({
            "categoryId": CATEGORIES_IDS["SERVICE_CHARGE"],
            "value": reservation_dto["service_charge"]
        })

    return categories

def get_receivable_data(reservation_dto, transaction_dto):
    check_in_date = datetime.strptime(reservation_dto["check_in_date"], "%Y-%m-%d")
    check_out_date = datetime.strptime(reservation_dto["check_out_date"], "%Y-%m-%d")
    dueDate = transaction_dto["dueDate"]
    scheduleDate = transaction_dto["scheduleDate"]
    categories = []

    if reservation_dto["partner_name"] == "API airbnb":
        dueDate = check_in_date + timedelta(days=1)
        scheduleDate = check_in_date + timedelta(days=1)
        categories = get_airbnb_categories(reservation_dto)

    if reservation_dto["partner_name"] == "API decolar":
        dueDate = check_in_date + timedelta(days=30)
        scheduleDate = check_in_date + timedelta(days=30)
        categories = get_decolar_categories(reservation_dto)

    if reservation_dto["partner_name"] == "API booking.com":
        if reservation_dto["total_paid"] == 0:
            dueDate = check_in_date
            scheduleDate = check_in_date
            categories = get_booking_categories(reservation_dto, True)
        else:
            dueDate = get_next_month_15(check_out_date)
            scheduleDate = get_next_month_15(check_out_date)
            categories = get_booking_categories(reservation_dto, False)

    if reservation_dto["partner_name"] == "API expedia":
        dueDate = check_out_date + timedelta(days=32)
        scheduleDate = check_out_date + timedelta(days=32)
        categories = get_expedia_categories(reservation_dto)

    if reservation_dto["partner_name"] in ["website", "diretas"]:
        dueDate = check_in_date
        scheduleDate = check_in_date
        categories = get_website_categories(reservation_dto)


    transaction_dto["categories"] = categories
    transaction_dto["dueDate"] = dueDate
    transaction_dto["scheduleDate"] = scheduleDate

    return transaction_dto