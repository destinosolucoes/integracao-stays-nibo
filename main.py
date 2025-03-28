from fastapi import FastAPI, Request, HTTPException, Depends, Body
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Redirect to the health endpoint"""
    return RedirectResponse(url="/api/health")

# Health check endpoint
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    env_vars = {
        "DB_NAME": os.getenv("DB_NAME", "Not set"),
        "DB_HOST": os.getenv("DB_HOST", "Not set"),
        "WEBHOOK_SECRET": "✓" if os.getenv("WEBHOOK_SECRET") else "✗",
        "NIBO_CLIENT_SECRET": "✓" if os.getenv("NIBO_CLIENT_SECRET") else "✗",
        "STAYS_SECRET": "✓" if os.getenv("STAYS_SECRET") else "✗"
    }
    
    return {
        "status": "ready",
        "environment": env_vars
    }

# Import the API functionality
try:
    # Import key functionality from bundle
    from api.bundle import (
        # Core FastAPI components
        APIRouter, HTTPException, Depends, Body, Request,
        
        # Auth and validation
        validate_header, create_request_log, SessionDep,
        
        # Queue
        add_to_queue, queue_size,
        
        # Stays functions
        get_reservation, get_listing, get_client,
        
        # Nibo functions
        create_debit_schedule, get_debit_schedule, update_debit_schedule, delete_debit_schedule,
        create_credit_schedule, get_credit_schedule, get_transaction,
        create_operational_account, create_commission, create_receivable
    )
    
    # Webhook endpoint
    @app.post("/api/stays-webhook")
    async def webhook_reservation(request: Request, session: SessionDep):
        data = await request.json()
        
        # Log the incoming request
        create_request_log(data["_dt"], data["action"], data["payload"], session)
        
        # Validate the webhook header
        if not validate_header(request.headers):
            raise HTTPException(status_code=403)
        
        # Add the request to the queue for processing
        await add_to_queue(data)
        
        # Return immediately to acknowledge receipt
        return {"status": "queued"}
    
    # Queue status endpoint
    @app.get("/api/queue-status")
    def queue_status_endpoint():
        """Get the current status of the webhook processing queue"""
        return {
            "status": "ok",
            "queue_size": queue_size()
        }
    
    # Add stays routes
    stays_router = APIRouter(prefix="/api/stays", tags=["stays"])
    
    @stays_router.get("/reservation/{reservation_id}")
    def reservation_endpoint(reservation_id: str):
        return get_reservation(reservation_id)
    
    @stays_router.get("/listing/{listing_id}")
    def listing_endpoint(listing_id: str):
        return get_listing(listing_id)
    
    @stays_router.get("/client/{client_id}")
    def client_endpoint(client_id: str):
        return get_client(client_id)
    
    app.include_router(stays_router)
    
    # Add nibo routes
    nibo_router = APIRouter(prefix="/api/nibo", tags=["nibo"])
    
    @nibo_router.post("/debit-schedule")
    def create_debit_schedule_endpoint(payload: dict = Body(...)):
        return create_debit_schedule(payload)
    
    @nibo_router.get("/debit-schedule/{reservation_id}")
    def get_debit_schedule_endpoint(reservation_id: str):
        return get_debit_schedule(reservation_id)
    
    @nibo_router.put("/debit-schedule/{schedule_id}")
    def update_debit_schedule_endpoint(schedule_id: str, payload: dict = Body(...)):
        return update_debit_schedule(schedule_id, payload)
    
    @nibo_router.delete("/debit-schedule/{schedule_id}")
    def delete_debit_schedule_endpoint(schedule_id: str):
        return delete_debit_schedule(schedule_id)
    
    @nibo_router.post("/credit-schedule")
    def create_credit_schedule_endpoint(payload: dict = Body(...)):
        return create_credit_schedule(payload)
    
    @nibo_router.get("/transaction/{transaction_id}")
    def get_transaction_endpoint(transaction_id: str):
        return get_transaction(transaction_id)
    
    @nibo_router.post("/operational-account")
    def create_operational_account_endpoint(payload: dict = Body(...)):
        return create_operational_account(payload)
    
    @nibo_router.post("/commission")
    def create_commission_endpoint(payload: dict = Body(...)):
        return create_commission(payload)
    
    @nibo_router.post("/receivable")
    def create_receivable_endpoint(payload: dict = Body(...)):
        return create_receivable(payload)
    
    app.include_router(nibo_router)

except ImportError as e:
    # If there's an import error, provide a fallback for all API routes
    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def api_error_handler(path: str):
        """Handle missing API functionality"""
        return JSONResponse(
            status_code=500,
            content={"error": f"API functionality unavailable: {str(e)}"}
        ) 