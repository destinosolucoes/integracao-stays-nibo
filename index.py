from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import uvicorn
import os

app = FastAPI()

@app.get("/")
async def root():
    """Redirect root to the health endpoint"""
    return RedirectResponse(url="/api/health")

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ready"}

# Catch-all route to forward requests to the API
@app.get("/{path:path}")
@app.post("/{path:path}")
@app.put("/{path:path}")
@app.delete("/{path:path}")
async def catch_all(path: str, request: Request):
    """Forward all requests to the main API"""
    # Import inside the function to defer import errors until needed
    try:
        from api.bundle import app as api_app
        return await api_app(request.scope, request.receive, request.send)
    except ImportError as e:
        return {"error": f"API not properly initialized: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=True) 