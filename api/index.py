from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .stays.index import get_reservation_report
from .nibo.utils import check_special_booking
from .nibo.transaction import send_transaction, update_transaction, delete_transaction
from .utils import create_reservation_dto, calculate_expedia, create_log, validate_header

app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/stays-webhook")
async def webhook_reservation(request: Request):
    data = await request.json()

    if validate_header(request.headers):
        # if data["action"] in ["reservation.created", "reservation.modified", "reservation.deleted", "reservation.canceled"]:
        #     create_log(data)

        if data["action"] == "reservation.created":
            reservation = data["payload"]

            if reservation["type"] == "booked":
                reservation_report = get_reservation_report(reservation)

                if "partnerName" not in reservation_report:
                    reservation_report["partnerName"] = "website"

                reservation_dto = create_reservation_dto(reservation_report, reservation)
                reservation_dto = calculate_expedia(reservation_dto)

                receivable_transaction = send_transaction(reservation_dto, "receivable")
                if receivable_transaction is False:
                    print("Erro ao criar receivable_transaction")
                    print(receivable_transaction)

                operational_transaction = send_transaction(reservation_dto, "operational")
                if operational_transaction is False:
                    print("Erro ao criar operational_transaction")
                    print(operational_transaction)
                
                if reservation_dto["partner_name"] == "API booking.com" and check_special_booking(reservation_dto["partner_name"]):
                    comission_transaction = send_transaction(reservation_dto, "comission")
                    if comission_transaction is False:
                        print("Erro ao criar comission_transaction")
                        print(comission_transaction)
            
        if data["action"] == "reservation.modified":
            reservation = data["payload"]

            if reservation["type"] == "booked":
                reservation_report = get_reservation_report(reservation)

                if "partnerName" not in reservation_report:
                    reservation_report["partnerName"] = "website"
                
                reservation_dto = create_reservation_dto(reservation_report, reservation)
                reservation_dto = calculate_expedia(reservation_dto)

                update_transactions = update_transaction(reservation_report, reservation_dto)
                if update_transactions is False:
                    print("Erro ao criar update_transaction")
                    print(update_transactions)

            
        if data["action"] == "reservation.deleted" or data["action"] == "reservation.canceled":
            reservation = data["payload"]

            reservation_report = get_reservation_report(reservation)
            delete_transactions = delete_transaction(reservation["id"])
            if delete_transactions is False:
                print("Erro ao deletar delete_transaction")
                print(delete_transactions)

    return {}
