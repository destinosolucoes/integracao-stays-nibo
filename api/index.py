from typing import Annotated
from sqlmodel import Session, create_engine
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from .stays.index import get_reservation_report
from .nibo.transaction import send_transaction, update_transaction, delete_transaction, check_transaction_created
from .utils import create_reservation_dto, calculate_expedia, create_request_log, create_log, validate_header
from .constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

db_url = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

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

@app.get("/api/health")
def health():
    return { "status": "ready" }

def is_checkin_date_older_than_one_month(check_in_date_str):
    """Check if the check-in date is older than 1 month from now"""
    check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    one_month_ago = datetime.now() - timedelta(days=30)
    return check_in_date < one_month_ago

@app.post("/api/stays-webhook")
async def webhook_reservation(request: Request, session: SessionDep):
    data = await request.json()
    track_log = []

    create_request_log(data["_dt"],data["action"],data["payload"],session)

    if not validate_header(request.headers):
        raise HTTPException(status_code=403)

    if data["action"] == "reservation.modified":
        reservation = data["payload"]
        track_log.append({"get_payload":reservation})

        if reservation["type"] == "booked":
            reservation_report = get_reservation_report(reservation)
            track_log.append({"get_reservation_report":reservation_report})

            if "partnerName" not in reservation_report:
                reservation_report["partnerName"] = "website"

            if is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
                track_log.append({"ignored_old_reservation": reservation_report["checkInDate"]})
                create_log(data["_dt"],data["action"],data["payload"],{"track_log":track_log},session)
                return {"status": "ignored", "reason": "check-in date older than 1 month"}

            reservation_dto = create_reservation_dto(reservation_report, reservation)
            track_log.append({"create_reservation_dto":reservation_dto})

            reservation_dto = calculate_expedia(reservation_dto)
            track_log.append({"calculate_expedia":reservation_dto})

            if not check_transaction_created(reservation_dto):
                receivable_transaction = send_transaction(reservation_dto, "receivable")
                track_log.append({"send_transaction_receivable":receivable_transaction})
                
                if receivable_transaction is False:
                    print("Erro ao criar receivable_transaction")
                    print(receivable_transaction)

                operational_transaction = send_transaction(reservation_dto, "operational")
                track_log.append({"send_transaction_operational":operational_transaction})

                if operational_transaction is False:
                    print("Erro ao criar operational_transaction")
                    print(operational_transaction)
                
                if reservation_dto["partner_name"] == "API booking.com" and reservation_dto["total_paid"] == 0:
                    comission_transaction = send_transaction(reservation_dto, "comission")
                    track_log.append({"send_transaction_comission":comission_transaction})

                    if comission_transaction is False:
                        print("Erro ao criar comission_transaction")
                        print(comission_transaction)
            else:
                update_transactions, track_log = update_transaction(reservation_report, reservation_dto)
                track_log.append({"update_transaction":track_log})
                
                if update_transactions is False:
                    print("Erro ao criar update_transaction")
                    print(update_transactions)
        
    if data["action"] == "reservation.deleted" or data["action"] == "reservation.canceled":
        reservation = data["payload"]
        track_log.append({"get_payload":reservation})

        reservation_report = get_reservation_report(reservation)
        track_log.append({"get_reservation_report":reservation_report})

        if reservation_report and "checkInDate" in reservation_report and is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
            track_log.append({"ignored_old_reservation": reservation_report["checkInDate"]})
            create_log(data["_dt"],data["action"],data["payload"],{"track_log":track_log},session)
            return {"status": "ignored", "reason": "check-in date older than 1 month"}

        delete_transactions = delete_transaction(reservation["id"])
        track_log.append({"delete_transaction":delete_transactions})

        if delete_transactions is False:
            print("Erro ao deletar delete_transaction")
            print(delete_transactions)

    
    if data["action"] in ["reservation.created", "reservation.modified", "reservation.deleted", "reservation.canceled"]:
        create_log(data["_dt"],data["action"],data["payload"],{"track_log":track_log},session)

    return {}
