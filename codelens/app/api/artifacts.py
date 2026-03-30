"""
Artifacts API router for CodeLens.
Serves generated documentation files for download.
GET /api/v1/jobs/{job_id}/artifacts/{filename}
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from codelens.app.core.job_store import job_store

router = APIRouter()

# Base output directory — matches CODELENS_OUTPUT_BASE env var default
OUTPUT_BASE = Path(os.getenv("CODELENS_OUTPUT_BASE", "./codelens-output"))


@router.get("/{job_id}/artifacts/{filename}")
async def download_artifact(job_id: str, filename: str):
    """
    Download a generated artifact file.
    Available filenames are listed in the job status response under 'artifacts'.

    Common artifacts:
      - FINAL_DOCUMENTATION.md
      - FINAL_DOCUMENTATION.pdf
      - module_{id}.md  (per-module analysis files)
      - orchestrator_report.md
    """
    status = job_store.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if status.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Job '{job_id}' is not completed yet (current status: {status.status})"
        )

    # Security: prevent path traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if filename not in status.artifacts:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{filename}' not found. Available: {status.artifacts}"
        )

    artifact_path = OUTPUT_BASE / job_id / filename
    if not artifact_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Artifact file missing from disk. The job output directory may have been cleaned up."
        )

    # Set correct content type based on file extension
    media_type = _get_media_type(filename)

    return FileResponse(
        path=str(artifact_path),
        media_type=media_type,
        filename=filename,
    )


def _get_media_type(filename: str) -> str:
    """Return appropriate MIME type for the artifact."""
    ext = Path(filename).suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".md": "text/markdown",
        ".html": "text/html",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    return media_types.get(ext, "application/octet-stream")