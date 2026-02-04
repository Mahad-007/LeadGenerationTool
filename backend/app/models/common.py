"""Common models shared across API endpoints."""

from pydantic import BaseModel, Field


class StepRunResponse(BaseModel):
    """Generic response for running a pipeline step."""
    success: bool = Field(description="Whether the step was started successfully")
    message: str = Field(description="Status message")
