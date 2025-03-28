"""
This file bundles all the necessary imports and functions into a single file
to work around Vercel's 12 serverless function limit on the Hobby plan.
"""

# Import necessary libraries
import requests
import pymysql
from typing import Annotated, Dict, Any, List, Optional, Callable, AsyncGenerator
from sqlmodel import Session, create_engine, SQLModel, Field, Column, TIMESTAMP, text
from fastapi import FastAPI, Request, HTTPException, Depends, Body, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants from .constants
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
NIBO_CLIENT_SECRET = os.getenv("NIBO_CLIENT_SECRET")
STAYS_SECRET = os.getenv("STAYS_SECRET")

# Database connection
db_url = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

# Database session dependency
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Create async session factory
async def get_async_session():
    with Session(engine) as session:
        return session

# Import functionality from utils.py
class WebhookRequest(SQLModel, table=True):
    __tablename__ = "webhook_requests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str
    action: str
    payload: str
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP, 
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        )
    )

def validate_header(headers):
    """Validate the webhook request header"""
    return headers.get("x-stays-signature") == WEBHOOK_SECRET

def create_request_log(timestamp, action, payload, session):
    """Create a log entry for a webhook request"""
    webhook_request = WebhookRequest(
        timestamp=timestamp,
        action=action,
        payload=json.dumps(payload)
    )
    session.add(webhook_request)
    session.commit()
    session.refresh(webhook_request)
    return webhook_request

# Queue implementation from queue.py
_queue = asyncio.Queue()
_queue_processor_task = None

async def add_to_queue(data):
    """Add a webhook request to the processing queue"""
    await _queue.put(data)

def queue_size():
    """Get the current size of the webhook processing queue"""
    return _queue.qsize()

async def _process_queue(callback):
    """Process the webhook queue"""
    while True:
        data = await _queue.get()
        try:
            await callback(data)
        except Exception as e:
            print(f"Error processing webhook: {e}")
        finally:
            _queue.task_done()

def start_queue_processor(callback):
    """Start the webhook queue processor"""
    global _queue_processor_task
    if _queue_processor_task is None:
        _queue_processor_task = asyncio.create_task(_process_queue(callback))

def stop_queue_processor():
    """Stop the webhook queue processor"""
    global _queue_processor_task
    if _queue_processor_task is not None:
        _queue_processor_task.cancel()
        _queue_processor_task = None

# Webhook processor implementation
async def process_webhook_request(data, get_session_func):
    """Process a webhook request from the queue"""
    # Processing logic would be implemented here
    # This is a placeholder for the actual implementation
    pass

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start queue processor
    start_queue_processor(
        lambda data: process_webhook_request(data, get_async_session)
    )
    yield
    # Shutdown: stop queue processor
    stop_queue_processor()

app = FastAPI(
    docs_url="/api/docs", 
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/api/health")
def health():
    return {"status": "ready"}

# Queue status endpoint
@app.get("/api/queue-status")
def queue_status_endpoint():
    """Get the current status of the webhook processing queue"""
    return {
        "status": "ok",
        "queue_size": queue_size()
    }

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

# Helper functions from stays.index
def get_reservation(reservation_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/reservations/{reservation_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()

def get_listing(listing_id: str):
    url = f"https://adsa.stays.com.br/external/v1/content/listings/{listing_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()

def get_client(client_id: str):
    url = f"https://adsa.stays.com.br/external/v1/booking/clients/{client_id}"

    headers = {
        "Authorization": f"Basic {STAYS_SECRET}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()

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

# Helper functions from nibo

# Add essential Nibo functions - adding just a few as examples
def create_debit_schedule(payload):
    url = "https://api.nibo.com.br/empresas/v1/schedules/debit"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if "error" in response:
        print("create_debit_schedule error", response["error_description"], payload)
        return False

    return response

def get_debit_schedule(reservation_id: str):
    url = f"https://api.nibo.com.br/empresas/v1/schedules/debit?$filter=contains(description,'{reservation_id}')"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apitoken": NIBO_CLIENT_SECRET
    }

    response = requests.get(url, headers=headers)
    response = response.json()

    if "statusCode" in response and response["statusCode"] == 404:
        return False

    return response["items"]

# Add nibo routes
nibo_router = APIRouter(prefix="/api/nibo", tags=["nibo"])

@nibo_router.post("/debit-schedule")
def create_debit_schedule_endpoint(payload: dict = Body(...)):
    return create_debit_schedule(payload)

@nibo_router.get("/debit-schedule/{reservation_id}")
def get_debit_schedule_endpoint(reservation_id: str):
    return get_debit_schedule(reservation_id)

app.include_router(nibo_router)

# Catch-all for 404s
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    raise HTTPException(status_code=404, detail=f"Path '/{full_path}' not found") 