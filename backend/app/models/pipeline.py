"""Pipeline models for API responses."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    """Pipeline step identifiers."""
    DISCOVERY = "discovery"
    VERIFICATION = "verification"
    AUDIT = "audit"
    ANALYSIS = "analysis"
    CONTACTS = "contacts"
    OUTREACH = "outreach"


class StepState(BaseModel):
    """State of a pipeline step."""
    status: str = Field(default="pending", description="Step status: pending, running, completed, failed, skipped")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(default=None, description="Current step message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    items_processed: int = Field(default=0, ge=0, description="Number of items processed")
    items_total: int = Field(default=0, ge=0, description="Total items to process")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp when step started")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp when step completed")


class PipelineState(BaseModel):
    """Current state of the pipeline."""
    status: PipelineStatus = Field(default=PipelineStatus.IDLE, description="Overall pipeline status")
    current_step: Optional[PipelineStep] = Field(default=None, description="Currently executing step")
    run_id: Optional[str] = Field(default=None, description="Unique run identifier")
    steps: dict[PipelineStep, StepState] = Field(
        default_factory=lambda: {step: StepState() for step in PipelineStep},
        description="State of each pipeline step"
    )
    started_at: Optional[str] = Field(default=None, description="ISO timestamp when pipeline started")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp when pipeline completed")
    error: Optional[str] = Field(default=None, description="Error message if pipeline failed")

    model_config = ConfigDict(use_enum_values=True)


class PipelineRunRequest(BaseModel):
    """Request body for starting the pipeline."""
    niche: str = Field(
        min_length=1,
        max_length=100,
        description="Target niche for discovery (e.g., 'fitness', 'fashion')"
    )
    max_sites: int = Field(default=10, ge=1, le=100, description="Maximum number of sites to process")


class PipelineRunResponse(BaseModel):
    """Response from starting the pipeline."""
    success: bool = Field(description="Whether the pipeline was started successfully")
    message: str = Field(description="Status message")
    run_id: Optional[str] = Field(default=None, description="Unique run identifier")


class PipelineStopResponse(BaseModel):
    """Response from stopping the pipeline."""
    success: bool = Field(description="Whether the pipeline was stopped successfully")
    message: str = Field(description="Status message")
