"""
FastAPI application entry point for CodeLens.
Initializes the app, includes routers, and sets up middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import jobs, status, stream, artifacts, health

app = FastAPI(
    title="CodeLens API",
    description="VB.net Codebase Documentation Generator API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(status.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(stream.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(artifacts.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

@app.get("/")
async def root():
    return {"message": "CodeLens API is running", "version": "0.1.0"}