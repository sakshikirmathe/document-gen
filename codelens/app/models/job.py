"""
Pydantic schemas for Job-related data models.
Defines the request, status, and result models for CodeLens jobs.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class VBNetOptions(BaseModel):
    """VB.net-specific options for CodeLens processing."""
    parse_solution_file: bool = Field(
        default=True,
        description="Read .sln file for project graph"
    )
    include_designer_files: bool = Field(
        default=False,
        description="Exclude *.Designer.vb by default"
    )
    include_resource_files: bool = Field(
        default=False,
        description="Exclude *.resx by default"
    )
    nuget_packages_path: Optional[str] = Field(
        default=None,
        description="packages/ or .nuget/ path"
    )
    target_framework: Optional[str] = Field(
        default=None,
        description="e.g. 'net48', 'net6.0-windows'"
    )


class CodeLensJobRequest(BaseModel):
    """Request model for creating a new documentation generation job."""
    source_path: str = Field(
        ...,
        description="Absolute path to VB.net project root"
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Defaults to ./codelens-output/{job_id}"
    )
    provider: str = Field(
        default="anthropic",
        description="anthropic | openai | gemini | ollama"
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="LLM model to use for analysis"
    )
    max_parallel_agents: int = Field(
        default=4,
        description="Maximum number of specialist agents to run concurrently"
    )
    output_format: str = Field(
        default="both",
        description="md | pdf | both"
    )
    dry_run: bool = Field(
        default=False,
        description="Run only Reader + Orchestrator to preview module map"
    )
    config_file: Optional[str] = Field(
        default=None,
        description="Path to codelens.config.yaml"
    )
    vbnet_options: VBNetOptions = Field(
        default_factory=VBNetOptions
    )


class JobStatus(BaseModel):
    """Status model for tracking job progress."""
    job_id: str
    status: Literal[
        "queued",
        "reading",
        "orchestrating",
        "analyzing",
        "synthesizing",
        "converting",
        "completed",
        "failed"
    ]
    progress_pct: float = Field(
        default=0.0,
        description="Progress percentage (0.0 - 100.0)"
    )
    current_stage: str = Field(
        default="",
        description="Current processing stage"
    )
    modules_total: int = Field(
        default=0,
        description="Total number of modules to process"
    )
    modules_completed: int = Field(
        default=0,
        description="Number of modules completed"
    )
    active_agents: List[str] = Field(
        default_factory=list,
        description="Module IDs currently being analyzed"
    )
    eta_seconds: Optional[int] = Field(
        default=None,
        description="Estimated time to completion in seconds"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="List of available artifact filenames"
    )
    created_at: datetime = Field(
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        default_factory=datetime.now
    )


class JobResult(BaseModel):
    """Result model for completed jobs."""
    job_id: str
    status: Literal["completed", "failed"]
    module_map: Optional[dict] = Field(
        default=None,
        description="Orchestrator's module identification results"
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="Generated artifact filenames"
    )
    output_dir: str = Field(
        ...,
        description="Directory containing all job outputs"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    started_at: datetime
    completed_at: datetime