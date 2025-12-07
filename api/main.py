"""
FastAPI application for video segmentation and editing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "FrameShift API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

