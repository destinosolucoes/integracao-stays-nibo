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
        return create_debit_schedule(transaction_dto)

    return create_credit_schedule(transaction_dto)

def check_transaction_created(reservation_dto):
    debit_schedules = get_debit_schedule(reservation_dto["reservation_id"])
    credit_schedules = get_credit_schedule(reservation_dto["reservation_id"])

    if len(debit_schedules) > 0 or len(credit_schedules) > 0:
        return True
    
    return False

def update_transaction(reservation_report, reservation_dto):
    track_log = []
    debit_schedules = get_debit_schedule(reservation_dto["reservation_id"])
    credit_schedules = get_credit_schedule(reservation_dto["reservation_id"])
    track_log.append({"get_debit_schedule":debit_schedules})
    track_log.append({"get_credit_schedule":credit_schedules})

    for debit_schedule in debit_schedules:
        debit_schedule["categories"] = change_categories_value(reservation_dto, debit_schedule)
        debit_schedule["stakeholderId"] = debit_schedule["stakeholder"]["id"]
        
        if len(debit_schedule["costCenters"]) > 0:
            debit_schedule["costCenters"][0]["value"] = get_center_cost(debit_schedule)
        
        transaction = update_debit_schedule(debit_schedule["scheduleId"], debit_schedule)
        track_log.append({"update_debit_schedule":transaction})

    for credit_schedule in credit_schedules:
        credit_schedule["categories"] = change_categories_value(reservation_dto, credit_schedule)
        credit_schedule["stakeholderId"] = credit_schedule["stakeholder"]["id"]
        
        if len(credit_schedule["costCenters"]) > 0:
            credit_schedule["costCenters"][0]["value"] = get_center_cost(credit_schedule)

        transaction = update_credit_schedule(credit_schedule["scheduleId"], credit_schedule)
        track_log.append({"update_credit_schedule":transaction})

    return True, track_log

def _belongs_to_reservation(schedule, reservation_id):
    """True if this schedule belongs to the given reservation.

    Each logical schedule has a distinct reference:
      - receivable (credit):   "<reservation_id>"
      - operational (debit):   "<reservation_id>_operacional"
      - comission (debit):     "<reservation_id>_comissao"

    Matching on the reference (exact, or with a "_" suffix) avoids the
    substring false-positives that a contains(description) query can produce
    (e.g. reservation "MK06J" must not match "XMK06J").
    """
    reference = str(schedule.get("reference", ""))
    reservation_id = str(reservation_id)
    return reference == reservation_id or reference.startswith(reservation_id + "_")


def _dedupe_by_reference(schedules, reservation_id, delete_fn, kind):
    """Delete duplicate schedules that share the same reference.

    Duplicates are created when the same Stays event is processed twice
    concurrently and both runs pass the check-then-create guard. Grouping by
    reference and keeping a deterministic survivor (smallest scheduleId) makes
    this self-healing: concurrent runs all keep the same schedule and any
    double-delete of an already-removed extra is harmless.
    """
    track_log = []

    if not schedules:
        return track_log

    groups = {}
    for schedule in schedules:
        if not _belongs_to_reservation(schedule, reservation_id):
            continue
        if "scheduleId" not in schedule:
            continue
        reference = str(schedule.get("reference", ""))
        groups.setdefault(reference, []).append(schedule)

    for reference, items in groups.items():
        if len(items) <= 1:
            continue

        # Deterministic survivor: smallest scheduleId. Every concurrent run
        # keeps the same one, so the outcome converges to a single schedule.
        items_sorted = sorted(items, key=lambda s: str(s["scheduleId"]))
        keep = items_sorted[0]

        for extra in items_sorted[1:]:
            try:
                result = delete_fn(extra["scheduleId"])
            except Exception as e:
                result = f"error: {str(e)}"
            track_log.append({
                "dedupe_delete": {
                    "kind": kind,
                    "reference": reference,
                    "kept_scheduleId": keep["scheduleId"],
                    "deleted_scheduleId": extra["scheduleId"],
                    "result": result,
                }
            })

    return track_log


def deduplicate_reservation_schedules(reservation_dto):
    """Remove duplicate debit/credit schedules for a reservation.

    Idempotent reconciliation run at the end of every create/update so that no
    matter how many times the same reservation event is delivered, exactly one
    schedule per reference survives.
    """
    reservation_id = reservation_dto["reservation_id"]
    track_log = []

    debit_schedules = get_debit_schedule(reservation_id)
    credit_schedules = get_credit_schedule(reservation_id)

    track_log.extend(_dedupe_by_reference(debit_schedules, reservation_id, delete_debit_schedule, "debit"))
    track_log.extend(_dedupe_by_reference(credit_schedules, reservation_id, delete_credit_schedule, "credit"))

    return track_log


def delete_transaction(reservation_id: str):
    debit_schedules = get_debit_schedule(reservation_id)
    credit_schedules = get_credit_schedule(reservation_id)

    for debit_schedule in debit_schedules:
        transaction = delete_debit_schedule(debit_schedule["scheduleId"])

    for credit_schedule in credit_schedules:
        transaction = delete_credit_schedule(credit_schedule["scheduleId"])

    return True