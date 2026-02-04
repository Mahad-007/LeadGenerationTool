"""Pipeline API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, BackgroundTasks

from app.models.pipeline import (
    PipelineStatus,
    PipelineStep,
    StepState,
    PipelineState,
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStopResponse,
)
from app.websocket import manager
from app.services.pipeline_executor import executor

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# In-memory state storage (will be replaced with proper state management)
_pipeline_state = PipelineState()


def _reset_state() -> None:
    """Reset pipeline state to initial values."""
    global _pipeline_state
    _pipeline_state = PipelineState()


def _get_state() -> PipelineState:
    """Get current pipeline state."""
    return _pipeline_state


def _update_state(key: str, value: Any) -> None:
    """
    Update pipeline state by key path.

    Supports keys like:
    - "status" -> _pipeline_state.status
    - "current_step" -> _pipeline_state.current_step
    - "steps.discovery" -> _pipeline_state.steps[PipelineStep.DISCOVERY]
    """
    global _pipeline_state

    if key == "status":
        _pipeline_state.status = value
    elif key == "current_step":
        _pipeline_state.current_step = value
    elif key == "completed_at":
        _pipeline_state.completed_at = value
    elif key == "error":
        _pipeline_state.error = value
    elif key.startswith("steps."):
        step_name = key.split(".")[1]
        for step in PipelineStep:
            if step.value == step_name:
                _pipeline_state.steps[step] = value
                break


async def _run_pipeline_background(run_id: str, config: dict) -> None:
    """Background task to execute the full pipeline."""
    await executor.execute_pipeline(run_id, config, _update_state)


@router.get("/status", response_model=PipelineState)
async def get_pipeline_status() -> PipelineState:
    """Get current pipeline status and step states."""
    return _get_state()


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    config: PipelineRunRequest,
    background_tasks: BackgroundTasks,
) -> PipelineRunResponse:
    """Start the full pipeline execution."""
    global _pipeline_state

    # Check if pipeline is already running
    if _pipeline_state.status == PipelineStatus.RUNNING:
        return PipelineRunResponse(
            success=False,
            message="Pipeline is already running",
            run_id=_pipeline_state.run_id,
        )

    # Generate new run_id and start pipeline
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    _pipeline_state = PipelineState(
        status=PipelineStatus.RUNNING,
        current_step=PipelineStep.DISCOVERY,
        run_id=run_id,
        steps={step: StepState() for step in PipelineStep},
        started_at=now,
        completed_at=None,
        error=None,
    )

    # Broadcast pipeline_started event with config
    await manager.broadcast({
        "type": "pipeline_started",
        "run_id": run_id,
        "steps": [step.value for step in PipelineStep],
        "config": {
            "niche": config.niche,
            "max_sites": config.max_sites,
        },
    })

    # Add background task to execute the pipeline
    background_tasks.add_task(
        _run_pipeline_background,
        run_id,
        {"niche": config.niche, "max_sites": config.max_sites},
    )

    return PipelineRunResponse(
        success=True,
        message=f"Pipeline started for niche '{config.niche}' with max {config.max_sites} sites",
        run_id=run_id,
    )


@router.post("/stop", response_model=PipelineStopResponse)
async def stop_pipeline() -> PipelineStopResponse:
    """Stop the running pipeline."""
    global _pipeline_state

    # Check if pipeline is running
    if _pipeline_state.status != PipelineStatus.RUNNING:
        return PipelineStopResponse(
            success=True,
            message="No pipeline is currently running",
        )

    # Request executor to stop
    executor.request_stop()

    # Update state
    _pipeline_state.status = PipelineStatus.IDLE
    _pipeline_state.error = "Stopped by user"

    return PipelineStopResponse(
        success=True,
        message="Pipeline stop requested",
    )
