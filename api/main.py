"""
FastAPI application for video segmentation and editing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path

from .routes import router


# Create FastAPI app
app = FastAPI(
    title="FrameShift API",
    description="API for video segmentation and editing with AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["video"])


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend application"""
    from pathlib import Path
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if not frontend_path.exists():
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)
    with open(frontend_path, 'r') as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

