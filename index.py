from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse

# Use simple FastAPI app without additional imports that might cause issues
app = FastAPI()

@app.get("/")
async def root():
    """Redirect root to the health endpoint"""
    return RedirectResponse(url="/api/health")

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ready"}

# Simplified catch-all route to forward requests to the API
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path: str, request: Request):
    """Forward all requests to the main API"""
    try:
        # Explicitly try to import from api.bundle
        from api.bundle import app as api_app
        return await api_app(request.scope, request.receive, request.send)
    except ImportError as e:
        # Return a proper error response with status code
        return JSONResponse(
            status_code=500,
            content={"error": f"API not properly initialized: {str(e)}"}
        ) 