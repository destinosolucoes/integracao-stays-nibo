from typing import Annotated
from sqlmodel import Session, create_engine
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from .stays.index import get_reservation_report, get_reservation
from .nibo.transaction import send_transaction, update_transaction, delete_transaction, check_transaction_created
from .utils import create_reservation_dto, calculate_expedia, create_request_log, create_log, validate_header
from .constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

logger = logging.getLogger(__name__)

db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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

class CreateReservationRequest(BaseModel):
    reservation_id: str

class CreateReservationResponse(BaseModel):
    status: str
    message: str
    reservation_id: str
    details: dict | None = None
    errors: list | None = None

class DeleteReservationRequest(BaseModel):
    reservation_id: str

class DeleteReservationResponse(BaseModel):
    status: str
    message: str
    reservation_id: str
    details: dict | None = None
    errors: list | None = None

@app.get("/api/health")
def health():
    return { "status": "ready" }

def process_reservation_creation(reservation_data, track_log, errors):
    """Shared logic for processing reservation creation"""
    try:
        track_log.append({"step": "start_processing", "reservation_id": reservation_data.get("id", "unknown")})
        
        if reservation_data["type"] != "booked":
            track_log.append({"step": "type_check", "reservation_type": reservation_data["type"], "result": "ignored"})
            return {"status": "ignored", "reason": f"Reservation type '{reservation_data['type']}' not processed"}

        track_log.append({"step": "type_check", "reservation_type": reservation_data["type"], "result": "accepted"})

        try:
            reservation_report = get_reservation_report(reservation_data)
            track_log.append({"step": "get_reservation_report", "success": reservation_report is not False})
        except Exception as e:
            track_log.append({"step": "get_reservation_report", "error": str(e)})
            errors.append(f"Failed to get reservation report: {str(e)}")
            return False

        if not reservation_report:
            track_log.append({"step": "reservation_report_validation", "result": "empty_report"})
            errors.append("Failed to get reservation report - empty response")
            return False

        if "partnerName" not in reservation_report:
            reservation_report["partnerName"] = "website"
            track_log.append({"step": "partner_name_default", "set_to": "website"})

        if is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
            track_log.append({"step": "date_check", "checkin_date": reservation_report["checkInDate"], "result": "too_old"})
            return {"status": "ignored", "reason": "check-in date older than 1 month"}

        track_log.append({"step": "date_check", "checkin_date": reservation_report["checkInDate"], "result": "valid"})

        try:
            reservation_dto = create_reservation_dto(reservation_report, reservation_data)
            track_log.append({"step": "create_reservation_dto", "success": True})
        except Exception as e:
            track_log.append({"step": "create_reservation_dto", "error": str(e)})
            errors.append(f"Failed to create reservation DTO: {str(e)}")
            return False

        try:
            reservation_dto = calculate_expedia(reservation_dto)
            track_log.append({"step": "calculate_expedia", "success": True})
        except Exception as e:
            track_log.append({"step": "calculate_expedia", "error": str(e)})
            errors.append(f"Failed to calculate expedia: {str(e)}")
            return False

        try:
            transaction_exists = check_transaction_created(reservation_dto)
            track_log.append({"step": "check_transaction_exists", "exists": transaction_exists})
        except Exception as e:
            track_log.append({"step": "check_transaction_exists", "error": str(e)})
            errors.append(f"Failed to check if transaction exists: {str(e)}")
            return False

        if not transaction_exists:
            track_log.append({"step": "transaction_flow", "type": "create_new"})
            
            # Create receivable transaction
            try:
                receivable_transaction = send_transaction(reservation_dto, "receivable")
                track_log.append({"step": "send_transaction_receivable", "success": receivable_transaction is not False})
                
                if receivable_transaction is False:
                    errors.append("Failed to create receivable transaction")
            except Exception as e:
                track_log.append({"step": "send_transaction_receivable", "error": str(e)})
                errors.append(f"Error creating receivable transaction: {str(e)}")

            # Create operational transaction
            try:
                operational_transaction = send_transaction(reservation_dto, "operational")
                track_log.append({"step": "send_transaction_operational", "success": operational_transaction is not False})

                if operational_transaction is False:
                    errors.append("Failed to create operational transaction")
            except Exception as e:
                track_log.append({"step": "send_transaction_operational", "error": str(e)})
                errors.append(f"Error creating operational transaction: {str(e)}")
            
            # Create commission transaction if applicable
            if reservation_dto["partner_name"] == "API booking.com" and reservation_dto["total_paid"] == 0:
                try:
                    comission_transaction = send_transaction(reservation_dto, "comission")
                    track_log.append({"step": "send_transaction_comission", "success": comission_transaction is not False})

                    if comission_transaction is False:
                        errors.append("Failed to create commission transaction")
                except Exception as e:
                    track_log.append({"step": "send_transaction_comission", "error": str(e)})
                    errors.append(f"Error creating commission transaction: {str(e)}")
            else:
                track_log.append({"step": "commission_check", "partner": reservation_dto.get("partner_name"), "total_paid": reservation_dto.get("total_paid"), "result": "skipped"})
        else:
            track_log.append({"step": "transaction_flow", "type": "update_existing"})
            try:
                update_transactions, update_log = update_transaction(reservation_report, reservation_dto)
                track_log.append({"step": "update_transaction", "success": update_transactions is not False, "update_log": update_log})
                
                if update_transactions is False:
                    errors.append("Failed to update transaction")
            except Exception as e:
                track_log.append({"step": "update_transaction", "error": str(e)})
                errors.append(f"Error updating transaction: {str(e)}")

        track_log.append({"step": "processing_complete", "success": True})
        return True
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        track_log.append({"step": "unexpected_error", "error": str(e), "traceback": error_trace})
        errors.append(f"Error processing reservation creation: {str(e)}")
        return False

@app.post("/api/create-reservation", response_model=CreateReservationResponse)
async def create_reservation(request: CreateReservationRequest, background_tasks: BackgroundTasks):
    """
    Create reservation transactions for a specific reservation ID.
    Returns immediately and processes in background to avoid Vercel 10s timeout.
    """
    background_tasks.add_task(process_create_reservation_async, request.reservation_id, db_url)
    
    return CreateReservationResponse(
        status="processing",
        message="Reservation sync started, processing in background",
        reservation_id=request.reservation_id,
        details=None,
        errors=None
    )


def process_create_reservation_async(reservation_id: str, db_connection_url: str):
    """Process reservation creation in background"""
    try:
        engine_bg = create_engine(db_connection_url)
        with Session(engine_bg) as session:
            track_log = []
            errors = []
            
            try:
                reservation_data = get_reservation(reservation_id)
                track_log.append({"get_reservation": "success"})
            except Exception as e:
                track_log.append({"get_reservation": f"error: {str(e)}"})
                logger.error(f"Failed to fetch reservation {reservation_id}: {e}")
                return
            
            log_data = {
                "_dt": datetime.now().isoformat(),
                "action": "reservation.created",
                "payload": reservation_data
            }
            
            create_request_log(log_data["_dt"], log_data["action"], log_data["payload"], session)
            
            result = process_reservation_creation(reservation_data, track_log, errors)
            
            create_log(log_data["_dt"], log_data["action"], log_data["payload"], {"track_log": track_log}, session)
            
            logger.info(f"Create reservation {reservation_id} completed: errors={len(errors)}")
    except Exception as e:
        logger.error(f"Background create-reservation failed for {reservation_id}: {e}", exc_info=True)

@app.post("/api/delete-reservation", response_model=DeleteReservationResponse)
async def delete_reservation(request: DeleteReservationRequest, background_tasks: BackgroundTasks):
    """
    Delete reservation transactions for a specific reservation ID.
    Returns immediately and processes in background to avoid Vercel 10s timeout.
    """
    background_tasks.add_task(process_delete_reservation_async, request.reservation_id, db_url)
    
    return DeleteReservationResponse(
        status="processing",
        message="Reservation deletion started, processing in background",
        reservation_id=request.reservation_id,
        details=None,
        errors=None
    )


def process_delete_reservation_async(reservation_id: str, db_connection_url: str):
    """Process reservation deletion in background"""
    try:
        engine_bg = create_engine(db_connection_url)
        with Session(engine_bg) as session:
            track_log = []
            
            try:
                reservation_data = get_reservation(reservation_id)
                track_log.append({"get_reservation": "success"})
            except Exception as e:
                track_log.append({"get_reservation": f"error: {str(e)}"})
                logger.error(f"Failed to fetch reservation {reservation_id} for deletion: {e}")
                return
            
            try:
                reservation_report = get_reservation_report(reservation_data)
                track_log.append({"get_reservation_report": "success"})
            except Exception as e:
                track_log.append({"get_reservation_report": f"error: {str(e)}"})
                reservation_report = None
            
            if reservation_report and "checkInDate" in reservation_report:
                if is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
                    track_log.append({"date_check": "ignored_old_reservation"})
                    log_data = {"_dt": datetime.now().isoformat(), "action": "reservation.deleted", "payload": reservation_data}
                    create_request_log(log_data["_dt"], log_data["action"], log_data["payload"], session)
                    create_log(log_data["_dt"], log_data["action"], log_data["payload"], {"track_log": track_log}, session)
                    return
            
            log_data = {"_dt": datetime.now().isoformat(), "action": "reservation.deleted", "payload": reservation_data}
            create_request_log(log_data["_dt"], log_data["action"], log_data["payload"], session)
            
            try:
                delete_result = delete_transaction(reservation_id)
                track_log.append({"delete_transaction": delete_result})
            except Exception as e:
                track_log.append({"delete_transaction": f"error: {str(e)}"})
            
            create_log(log_data["_dt"], log_data["action"], log_data["payload"], {"track_log": track_log}, session)
            logger.info(f"Delete reservation {reservation_id} completed")
    except Exception as e:
        logger.error(f"Background delete-reservation failed for {reservation_id}: {e}", exc_info=True)



def is_checkin_date_older_than_one_month(check_in_date_str):
    """Check if the check-in date is older than 1 month from now"""
    check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    one_month_ago = datetime.now() - timedelta(days=30)
    return check_in_date < one_month_ago

@app.post("/api/stays-webhook")
async def webhook_reservation(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    if not validate_header(request.headers):
        raise HTTPException(status_code=403)

    # Return immediately to Stays to avoid ETIMEDOUT
    # ALL processing (including DB logging) happens in background
    background_tasks.add_task(process_webhook_async, data, db_url)

    return {}


def process_webhook_async(data: dict, db_connection_url: str):
    """Process webhook data in background to avoid Stays timeout"""
    try:
        engine_bg = create_engine(db_connection_url)
        with Session(engine_bg) as session:
            # Log the incoming request first
            create_request_log(data["_dt"], data["action"], data["payload"], session)

            track_log = []

            if data["action"] in ["reservation.modified", "reservation.created"]:
                reservation = data["payload"]
                track_log.append({"get_payload": reservation})
                errors = []
                
                result = process_reservation_creation(reservation, track_log, errors)

            elif data["action"] in ["reservation.deleted", "reservation.canceled"]:
                reservation = data["payload"]
                track_log.append({"get_payload": reservation})

                try:
                    reservation_report = get_reservation_report(reservation)
                    track_log.append({"get_reservation_report": reservation_report})

                    if reservation_report and "checkInDate" in reservation_report and is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
                        track_log.append({"ignored_old_reservation": reservation_report["checkInDate"]})
                        create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
                        return
                except Exception as e:
                    track_log.append({"get_reservation_report_error": str(e)})

                delete_transactions = delete_transaction(reservation["id"])
                track_log.append({"delete_transaction": delete_transactions})

            if data["action"] in ["reservation.created", "reservation.modified", "reservation.deleted", "reservation.canceled"]:
                create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)

    except Exception as e:
        logger.error(f"Background webhook processing failed: {str(e)}", exc_info=True)
