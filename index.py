from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/")
async def root():
    return RedirectResponse(url="/api/health")

@app.get("/{path:path}")
async def catch_all(path: str, request: Request):
    """Forward all requests to the main API"""
    from api.bundle import app as api_app
    return await api_app(request.scope, request.receive, request.send) 