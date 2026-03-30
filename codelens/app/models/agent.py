"""
Pydantic schemas for Agent-related data models.
Defines the input, output, and status models for CodeLens agents.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime

# Fix: AgentStatus must be a plain Literal type alias, not a class.
# You cannot subclass both str and Literal simultaneously in Python.
AgentStatus = Literal["initialized", "analyzing", "completed", "failed", "retrying"]


class AgentInput(BaseModel):
    """Input model for agents."""
    task_id: str = Field(..., description="Unique identifier for the generation run")
    agent_id: str = Field(..., description="The agent's unique identifier")
    agent_type: str = Field(..., description="The type of agent (orchestrator, specialist, synthesizer)")
    input_data: Dict[str, Any] = Field(..., description="The data payload specific to the agent's role")
    config: Dict[str, Any] = Field(default_factory=dict, description="Runtime configuration overrides")


class AgentOutput(BaseModel):
    """Output model for agents."""
    agent_id: str = Field(..., description="The agent's unique identifier")
    agent_type: str = Field(..., description="The type of agent")
    status: AgentStatus = Field(..., description="The status of the agent execution")
    output_data: Optional[Dict[str, Any]] = Field(
        default=None, description="The result data from the agent execution"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if agent failed"
    )
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(
        default=None, description="When the agent completed execution"
    )


class ModuleDefinition(BaseModel):
    """Definition of a module identified by the Orchestrator Agent."""
    module_id: str = Field(..., description="Unique identifier for the module")
    module_name: str = Field(..., description="Human-readable name for the module")
    description: str = Field(..., description="Brief description of the module's purpose")
    files: List[str] = Field(
        default_factory=list, description="List of file paths belonging to this module"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="List of other module_ids this module depends on"
    )
    priority: int = Field(
        default=0, description="Suggested analysis order (lower numbers first)"
    )
    agent_prompt_hints: Optional[str] = Field(
        default=None, description="Contextual hints for the specialist agent"
    )


class ModuleMap(BaseModel):
    """Output of the Orchestrator Agent containing all identified modules."""
    modules: List[ModuleDefinition] = Field(
        default_factory=list, description="List of all identified modules"
    )
    orchestrator_notes: Optional[str] = Field(
        default=None, description="Additional notes or warnings from the orchestrator"
    )


class AgentReport(BaseModel):
    """Output of a Specialist Agent containing analysis of a module."""
    module_id: str = Field(..., description="The module ID this report is for")
    module_name: str = Field(..., description="Human-readable name of the module")
    overview: str = Field(..., description="2-3 paragraph executive summary of the module")
    file_breakdown: Dict[str, str] = Field(
        default_factory=dict, description="File-by-file breakdown of purpose and key elements"
    )
    key_classes_functions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed documentation of key classes and functions"
    )
    data_models_schemas: List[Dict[str, Any]] = Field(
        default_factory=list, description="Documentation of data models and schemas"
    )
    api_endpoints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Documentation of API endpoints (if applicable)"
    )
    configuration_env_vars: List[Dict[str, Any]] = Field(
        default_factory=list, description="Configuration options and environment variables"
    )
    internal_dependencies: List[str] = Field(
        default_factory=list, description="How this module interacts with other modules"
    )
    external_dependencies: List[Dict[str, Any]] = Field(
        default_factory=list, description="Third-party libraries and packages used"
    )
    error_handling_patterns: List[str] = Field(
        default_factory=list, description="How the module handles errors"
    )
    testing_info: Dict[str, Any] = Field(
        default_factory=dict, description="Summary of test files and testing patterns"
    )
    known_issues_tech_debt: List[str] = Field(
        default_factory=list, description="TODO/FIXME/HACK markers and deprecated code"
    )