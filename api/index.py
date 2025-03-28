from typing import Annotated
from sqlmodel import Session, create_engine
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .utils import create_request_log, validate_header
from .constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from .queue import add_to_queue, start_queue_processor, stop_queue_processor, queue_size
from .webhook_processor import process_webhook_request

# Import all routes from submodules
from .stays import index as stays_module
from .nibo import index as nibo_module
from .nibo import transaction as nibo_transaction
from .nibo import operational as nibo_operational
from .nibo import comission as nibo_comission
from .nibo import receivables as nibo_receivables

db_url = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Create async session factory for the queue processor
async def get_async_session():
    with Session(engine) as session:
        return session

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

@app.get("/api/queue-status")
def queue_status_endpoint():
    """Get the current status of the webhook processing queue"""
    return {
        "status": "ok",
        "queue_size": queue_size()
    }

def is_checkin_date_older_than_one_month(check_in_date_str):
    """Check if the check-in date is older than 1 month from now"""
    check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    one_month_ago = datetime.now() - timedelta(days=30)
    return check_in_date < one_month_ago

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

# Include routes from other modules
stays_module.register_routes(app)
nibo_module.register_routes(app)

# Helper function to handle 404s
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    raise HTTPException(status_code=404, detail=f"Path '/{full_path}' not found")
