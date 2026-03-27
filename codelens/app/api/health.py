"""
Health check endpoint for CodeLens API.
Returns system status, LLM provider connectivity, and queue depth.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal, Optional
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    version: str = "0.1.0"
    llm_providers: dict[str, bool]
    queue_depth: int
    uptime_seconds: Optional[float] = None

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the overall health of the service and its dependencies.
    """
    # In a real implementation, we would check:
    # - LLM provider connectivity (Anthropic, OpenAI, etc.)
    # - Queue depth (if using Redis/Celery)
    # - Other dependencies (database, etc.)

    # For now, we return a static response indicating healthy status.
    # This will be updated in later phases as we implement the actual checks.

    return HealthResponse(
        status="healthy",
        llm_providers={
            "anthropic": False,  # To be set based on actual API key presence/connectivity
            "openai": False,
            "gemini": False,
            "ollama": False,
        },
        queue_depth=0,
        uptime_seconds=None,
    )