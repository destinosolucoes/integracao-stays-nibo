from dateutil import relativedelta
from datetime import date

from .constants import SPECIAL_BOOKING_APARTMENTS

def get_next_month_15(date):
    new_date = date + relativedelta.relativedelta(months=1)
    return new_date.strftime("%Y-%m-15")

def check_special_booking(partner_name):
    return partner_name in SPECIAL_BOOKING_APARTMENTS

def sanitize_dates(transaction_dto):
    if isinstance(transaction_dto["scheduleDate"], date):
        transaction_dto["scheduleDate"] = transaction_dto["scheduleDate"].strftime("%Y-%m-%d")

    if isinstance(transaction_dto["dueDate"], date):
        transaction_dto["dueDate"] = transaction_dto["dueDate"].strftime("%Y-%m-%d")

    return transaction_dto
