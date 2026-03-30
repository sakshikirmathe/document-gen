"""
SSE Streaming API router for CodeLens.
Pushes real-time job progress to web clients via Server-Sent Events.
GET /api/v1/jobs/{job_id}/stream
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from codelens.app.core.job_store import job_store

router = APIRouter()

POLL_INTERVAL = 1.0   # seconds between SSE pushes
TERMINAL_STATUSES = {"completed", "failed"}


async def event_generator(job_id: str) -> AsyncIterator[str]:
    """
    Async generator that yields SSE-formatted events until the job finishes.
    Each event is a JSON blob with the current job status.
    """
    last_progress = -1.0

    while True:
        status = job_store.get(job_id)

        if status is None:
            # Job was deleted mid-stream
            yield _sse_event("error", {"message": f"Job '{job_id}' not found"})
            break

        current_progress = status.progress_pct

        # Only emit an event when something actually changed
        if current_progress != last_progress:
            payload = {
                "job_id": status.job_id,
                "status": status.status,
                "progress_pct": status.progress_pct,
                "current_stage": status.current_stage,
                "modules_total": status.modules_total,
                "modules_completed": status.modules_completed,
                "active_agents": status.active_agents,
                "artifacts": status.artifacts,
                "error": status.error,
                "timestamp": datetime.utcnow().isoformat(),
            }
            yield _sse_event("progress", payload)
            last_progress = current_progress

        if status.status in TERMINAL_STATUSES:
            # Send a final 'done' event then close the stream
            yield _sse_event("done", {"job_id": job_id, "status": status.status})
            break

        await asyncio.sleep(POLL_INTERVAL)


def _sse_event(event_type: str, data: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events endpoint for real-time progress streaming.
    Connect from a browser with:
        const es = new EventSource('/api/v1/jobs/{job_id}/stream');
        es.addEventListener('progress', e => console.log(JSON.parse(e.data)));
        es.addEventListener('done', e => es.close());
    """
    status = job_store.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return StreamingResponse(
        event_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )