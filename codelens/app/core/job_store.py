"""
In-memory job state store for CodeLens.
Tracks job status, requests, and results across API requests.
Thread-safe for use with FastAPI's async background tasks.

Can be swapped for a Redis-backed implementation in Phase 4
without changing any of the router code — just replace this module.
"""

import threading
from typing import Dict, Optional
from datetime import datetime

from codelens.app.models.job import JobStatus, CodeLensJobRequest


class InMemoryJobStore:
    """
    Thread-safe in-memory store for job state.
    Stores JobStatus objects keyed by job_id.
    """

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._requests: Dict[str, CodeLensJobRequest] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str, status: JobStatus, request: CodeLensJobRequest) -> None:
        """Register a new job."""
        with self._lock:
            self._jobs[job_id] = status
            self._requests[job_id] = request

    def get(self, job_id: str) -> Optional[JobStatus]:
        """Return the current JobStatus for a job, or None if not found."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_request(self, job_id: str) -> Optional[CodeLensJobRequest]:
        """Return the original job request, or None if not found."""
        with self._lock:
            return self._requests.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        """
        Update one or more fields on a JobStatus.
        Automatically updates the updated_at timestamp.

        Example:
            job_store.update(job_id, status="analyzing", progress_pct=35.0)
        """
        with self._lock:
            status = self._jobs.get(job_id)
            if status is None:
                return
            for key, value in kwargs.items():
                if hasattr(status, key):
                    setattr(status, key, value)
            status.updated_at = datetime.now()

    def add_artifact(self, job_id: str, filename: str) -> None:
        """Append an artifact filename to the job's artifact list."""
        with self._lock:
            status = self._jobs.get(job_id)
            if status and filename not in status.artifacts:
                status.artifacts.append(filename)
                status.updated_at = datetime.now()

    def set_active_agents(self, job_id: str, agent_ids: list) -> None:
        """Replace the list of currently active agent module IDs."""
        with self._lock:
            status = self._jobs.get(job_id)
            if status:
                status.active_agents = agent_ids
                status.updated_at = datetime.now()

    def increment_modules_completed(self, job_id: str) -> None:
        """Increment the modules_completed counter by 1."""
        with self._lock:
            status = self._jobs.get(job_id)
            if status:
                status.modules_completed += 1
                status.updated_at = datetime.now()

    def delete(self, job_id: str) -> None:
        """Remove a job from the store."""
        with self._lock:
            self._jobs.pop(job_id, None)
            self._requests.pop(job_id, None)

    def list_jobs(self) -> Dict[str, JobStatus]:
        """Return a snapshot of all jobs."""
        with self._lock:
            return dict(self._jobs)


# Module-level singleton — imported by all routers
job_store = InMemoryJobStore()