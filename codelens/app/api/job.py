"""
Jobs API router for CodeLens.
Handles job creation, retrieval, and cancellation.
POST /api/v1/jobs        — submit a new documentation generation job
GET  /api/v1/jobs/{id}  — get full job details
DELETE /api/v1/jobs/{id} — cancel a job
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime

from codelens.app.models.job import CodeLensJobRequest, JobStatus, JobResult
from codelens.app.core.job_store import job_store

router = APIRouter()


@router.post("", response_model=JobStatus, status_code=202)
async def create_job(request: CodeLensJobRequest, background_tasks: BackgroundTasks):
    """
    Submit a new documentation generation job.
    Returns a job_id immediately; processing runs in the background.
    """
    job_id = str(uuid.uuid4())

    # Create initial job status
    status = JobStatus(
        job_id=job_id,
        status="queued",
        progress_pct=0.0,
        current_stage="Job queued, waiting to start",
        modules_total=0,
        modules_completed=0,
        active_agents=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    job_store.create(job_id, status, request)

    # Queue the pipeline to run in the background
    background_tasks.add_task(run_pipeline, job_id, request)

    return status


@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    """Retrieve full job details including status, module map, and artifact paths."""
    status = job_store.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return status


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """Cancel a running job and clean up its resources."""
    status = job_store.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if status.status in ("completed", "failed"):
        job_store.delete(job_id)
        return

    # Mark as failed so the background task knows to stop
    job_store.update(job_id, status="failed", error="Job cancelled by user")
    job_store.delete(job_id)


async def run_pipeline(job_id: str, request: CodeLensJobRequest):
    """
    Background task that runs the full CodeLens pipeline.
    Placeholder — will be wired to the real pipeline in Phase 2/3.
    """
    import asyncio

    try:
        job_store.update(job_id, status="reading", current_stage="Reading codebase files", progress_pct=5.0)
        await asyncio.sleep(0)  # yield to event loop

        # TODO Phase 2: wire in CodebaseReader + VBNet parsers here
        # TODO Phase 2: wire in OrchestratorAgent here
        # TODO Phase 3: wire in SpecialistAgents + SynthesizerAgent here
        # TODO Phase 3: wire in PDF converter here

        job_store.update(job_id, status="completed", current_stage="Done", progress_pct=100.0)

    except Exception as e:
        job_store.update(job_id, status="failed", error=str(e))