"""
Status API router for CodeLens.
Lightweight polling endpoint for job progress.
GET /api/v1/jobs/{job_id}/status
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from codelens.app.core.job_store import job_store

router = APIRouter()


class StatusResponse(BaseModel):
    """Lightweight status response — subset of full JobStatus."""
    job_id: str
    status: str
    progress_pct: float
    current_stage: str
    modules_total: int
    modules_completed: int
    active_agents: List[str]
    eta_seconds: Optional[int]
    error: Optional[str]


@router.get("/{job_id}/status", response_model=StatusResponse)
async def get_job_status(job_id: str):
    """
    Lightweight status polling endpoint.
    Returns progress_pct, current_stage, active agents, and ETA.
    Use the SSE /stream endpoint for real-time push updates instead of polling.
    """
    status = job_store.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return StatusResponse(
        job_id=status.job_id,
        status=status.status,
        progress_pct=status.progress_pct,
        current_stage=status.current_stage,
        modules_total=status.modules_total,
        modules_completed=status.modules_completed,
        active_agents=status.active_agents,
        eta_seconds=status.eta_seconds,
        error=status.error,
    )