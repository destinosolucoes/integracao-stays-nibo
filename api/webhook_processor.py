import logging
from typing import Dict, Any, Callable, Awaitable
from sqlmodel import Session
from datetime import datetime, timedelta

from .utils import create_log
from .stays.index import get_reservation_report
from .utils import create_reservation_dto, calculate_expedia
from .nibo.transaction import send_transaction, update_transaction, delete_transaction, check_transaction_created

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_webhook_request(data: Dict[str, Any], session_factory: Callable[[], Awaitable[Session]]) -> Dict[str, Any]:
    """
    Process a webhook request from the queue
    
    Args:
        data: The webhook data to process
        session_factory: A callable that returns a database session
    
    Returns:
        Dict with processing result
    """
    # Start session
    session = await session_factory()
    track_log = []
    
    try:
        # Log that we're processing from the queue
        logger.info(f"Processing webhook request from queue: {data.get('action', 'unknown')}")
        
        # Process the webhook based on action
        if data["action"] == "reservation.modified":
            return await process_modified_reservation(data, session, track_log)
        
        elif data["action"] in ["reservation.deleted", "reservation.canceled"]:
            return await process_deleted_reservation(data, session, track_log)
        
        elif data["action"] == "reservation.created":
            # Just log it
            create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
            return {"status": "logged"}
        
        return {"status": "ignored", "reason": f"Unsupported action {data.get('action')}"}
    
    except Exception as e:
        logger.error(f"Error processing webhook request: {str(e)}")
        return {"status": "error", "error": str(e)}
    
    finally:
        # Close session
        session.close()

async def process_modified_reservation(data: Dict[str, Any], session: Session, track_log: list) -> Dict[str, Any]:
    """Process reservation.modified webhook"""
    reservation = data["payload"]
    track_log.append({"get_payload": reservation})
    
    if reservation["type"] == "booked":
        reservation_report = get_reservation_report(reservation)
        track_log.append({"get_reservation_report": reservation_report})
        
        if "partnerName" not in reservation_report:
            reservation_report["partnerName"] = "website"
        
        if is_checkin_date_older_than_one_month(reservation_report.get("checkInDate")):
            track_log.append({"ignored_old_reservation": reservation_report["checkInDate"]})
            create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
            return {"status": "ignored", "reason": "check-in date older than 1 month"}
        
        reservation_dto = create_reservation_dto(reservation_report, reservation)
        track_log.append({"create_reservation_dto": reservation_dto})
        
        reservation_dto = calculate_expedia(reservation_dto)
        track_log.append({"calculate_expedia": reservation_dto})
        
        if not check_transaction_created(reservation_dto):
            # Process transactions
            process_new_transactions(reservation_dto, track_log)
        else:
            # Update existing transactions
            update_transactions, update_log = update_transaction(reservation_report, reservation_dto)
            track_log.append({"update_transaction": update_log})
            
            if update_transactions is False:
                logger.error("Error updating transaction")
    
    create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
    return {"status": "processed"}

async def process_deleted_reservation(data: Dict[str, Any], session: Session, track_log: list) -> Dict[str, Any]:
    """Process reservation.deleted or reservation.canceled webhook"""
    reservation = data["payload"]
    track_log.append({"get_payload": reservation})
    
    reservation_report = get_reservation_report(reservation)
    track_log.append({"get_reservation_report": reservation_report})
    
    if reservation_report and "checkInDate" in reservation_report and is_checkin_date_older_than_one_month(reservation_report["checkInDate"]):
        track_log.append({"ignored_old_reservation": reservation_report["checkInDate"]})
        create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
        return {"status": "ignored", "reason": "check-in date older than 1 month"}
    
    delete_transactions = delete_transaction(reservation["id"])
    track_log.append({"delete_transaction": delete_transactions})
    
    if delete_transactions is False:
        logger.error("Error deleting transaction")
    
    create_log(data["_dt"], data["action"], data["payload"], {"track_log": track_log}, session)
    return {"status": "processed"}

def process_new_transactions(reservation_dto: Dict[str, Any], track_log: list) -> None:
    """Process new transactions for a reservation"""
    # Send receivable transaction
    receivable_transaction = send_transaction(reservation_dto, "receivable")
    track_log.append({"send_transaction_receivable": receivable_transaction})
    
    if receivable_transaction is False:
        logger.error("Error creating receivable_transaction")
    
    # Send operational transaction
    operational_transaction = send_transaction(reservation_dto, "operational")
    track_log.append({"send_transaction_operational": operational_transaction})
    
    if operational_transaction is False:
        logger.error("Error creating operational_transaction")
    
    # Send commission transaction if needed
    if reservation_dto["partner_name"] == "API booking.com" and reservation_dto["total_paid"] == 0:
        comission_transaction = send_transaction(reservation_dto, "comission")
        track_log.append({"send_transaction_comission": comission_transaction})
        
        if comission_transaction is False:
            logger.error("Error creating comission_transaction")

def is_checkin_date_older_than_one_month(check_in_date_str):
    """Check if the check-in date is older than 1 month from now"""
    if not check_in_date_str:
        return False
        
    check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    one_month_ago = datetime.now() - timedelta(days=30)
    return check_in_date < one_month_ago 