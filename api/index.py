from typing import Annotated
from sqlmodel import Session, create_engine
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pydantic import BaseModel

from .stays.index import get_reservation_report, get_reservation
from .nibo.transaction import send_transaction, update_transaction, delete_transaction, check_transaction_created
from .utils import create_reservation_dto, calculate_expedia, create_request_log, create_log, validate_header
from .constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

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
async def create_reservation(request: CreateReservationRequest, session: SessionDep):
    """
    Create reservation transactions for a specific reservation ID.
    Processes the reservation creation flow similar to webhook reservation.modified.
    """
    try:
        track_log = []
        errors = []
        
        # Get reservation from Stays API
        try:
            reservation_data = get_reservation(request.reservation_id)
            track_log.append({"get_reservation": "success"})
        except Exception as e:
            track_log.append({"get_reservation": f"error: {str(e)}"})
            return CreateReservationResponse(
                status="error",
                message="Failed to fetch reservation from Stays API",
                reservation_id=request.reservation_id,
                details={"track_log": track_log},
                errors=[f"API Error: {str(e)}"]
            )
        
        # Create data structure for logging
        log_data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.created",
            "payload": reservation_data
        }
        
        # Log the request
        create_request_log(log_data["_dt"], log_data["action"], log_data["payload"], session)
        track_log.append({"create_request_log": "success"})
        
        # Process reservation creation
        result = process_reservation_creation(reservation_data, track_log, errors)
        
        # Create final log
        create_log(log_data["_dt"], log_data["action"], log_data["payload"], {"track_log": track_log}, session)
        
        # Determine final status
        if not errors and result is True:
            status = "success"
            message = "Reservation created successfully"
        elif errors and result is True:
            status = "partial_success"
            message = f"Reservation created with {len(errors)} errors"
        elif isinstance(result, dict) and result.get("status") == "ignored":
            status = "ignored"
            message = result.get("reason", "Reservation was ignored")
        else:
            status = "error"
            message = "Failed to create reservation"
        
        # Create final response details
        response_details = {
            "track_log": track_log,
            "processed": result,
            "total_errors": len(errors) if errors else 0
        }
        
        # Log final result (structured)
        final_log = {
            "endpoint": "create_reservation",
            "reservation_id": request.reservation_id,
            "status": status,
            "message": message,
            "error_count": len(errors) if errors else 0,
            "processing_steps": len(track_log)
        }
        print(f"[CREATE_RESERVATION_RESULT] {final_log}")
        
        if errors:
            print(f"[CREATE_RESERVATION_ERRORS] {errors}")

        return CreateReservationResponse(
            status=status,
            message=message,
            reservation_id=request.reservation_id,
            details=response_details,
            errors=errors if errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        # Log the unexpected error
        error_log = {
            "endpoint": "create_reservation",
            "reservation_id": request.reservation_id,
            "error_type": "unexpected_system_error",
            "error": str(e),
            "traceback": error_trace
        }
        print(f"[CREATE_RESERVATION_SYSTEM_ERROR] {error_log}")
        
        return CreateReservationResponse(
            status="error",
            message="Unexpected system error occurred",
            reservation_id=request.reservation_id,
            details={
                "track_log": track_log if 'track_log' in locals() else [],
                "error_trace": error_trace
            },
            errors=[f"System Error: {str(e)}"]
        )



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
        errors = []
        
        result = process_reservation_creation(reservation, track_log, errors)
        
        # Print errors for webhook debugging (keeping original behavior)
        for error in errors:
            print(f"Webhook error: {error}")
        
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
