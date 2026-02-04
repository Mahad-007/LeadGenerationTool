"""Pipeline Executor - Runs CLI scripts as async subprocesses with streaming output."""

import asyncio
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from asyncio.subprocess import Process

from app.models.pipeline import PipelineStep, PipelineStatus, StepState
from app.websocket import manager

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Executes pipeline steps as async subprocesses with real-time progress streaming."""

    # Map PipelineStep to script and arguments
    STEP_SCRIPTS = {
        PipelineStep.DISCOVERY: {
            "script": "scripts/discover_sites.py",
            "args_builder": lambda config: ["--niche", config.get("niche", ""), "--use-database"],
        },
        PipelineStep.VERIFICATION: {
            "script": "scripts/verify_shopify.py",
            "args_builder": lambda config: [],
        },
        PipelineStep.AUDIT: {
            "script": "scripts/audit_homepage.py",
            "args_builder": lambda config: [],
        },
        PipelineStep.ANALYSIS: {
            "script": "scripts/analyze_with_gemini.py",
            "args_builder": lambda config: [],
        },
        PipelineStep.CONTACTS: {
            "script": "scripts/extract_contacts.py",
            "args_builder": lambda config: [],
        },
        PipelineStep.OUTREACH: {
            "script": "scripts/generate_outreach.py",
            "args_builder": lambda config: [],
        },
    }

    STEP_ORDER = [
        PipelineStep.DISCOVERY,
        PipelineStep.VERIFICATION,
        PipelineStep.AUDIT,
        PipelineStep.ANALYSIS,
        PipelineStep.CONTACTS,
        PipelineStep.OUTREACH,
    ]

    def __init__(self, project_root: Path):
        """Initialize executor with project root path."""
        self.project_root = project_root
        self._current_process: Optional[Process] = None
        self._should_stop = False
        self._is_running = False

    def request_stop(self) -> None:
        """Request graceful stop of current execution."""
        self._should_stop = True
        if self._current_process:
            self._current_process.terminate()

    async def execute_pipeline(
        self,
        run_id: str,
        config: dict,
        state_updater: Callable[[str, Any], None],
    ) -> bool:
        """
        Execute full pipeline with all steps.

        Args:
            run_id: Unique pipeline run identifier
            config: Pipeline configuration (niche, max_sites, etc.)
            state_updater: Callback to update global pipeline state

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        if self._is_running:
            logger.warning("Pipeline already running")
            return False

        self._is_running = True
        self._should_stop = False
        pipeline_start = time.time()
        steps_completed = 0
        total_items_processed = 0

        try:
            for step in self.STEP_ORDER:
                if self._should_stop:
                    logger.info(f"Pipeline stop requested at step {step.value}")
                    await self._broadcast_pipeline_stopped(run_id)
                    state_updater("status", PipelineStatus.IDLE)
                    state_updater("error", "Stopped by user")
                    return False

                # Execute step
                success, items = await self._execute_step(step, run_id, config, state_updater)

                if not success:
                    # Step failed - stop pipeline immediately
                    logger.error(f"Step {step.value} failed, stopping pipeline")
                    await self._broadcast_pipeline_failed(run_id, f"Step {step.value} failed")
                    state_updater("status", PipelineStatus.FAILED)
                    return False

                steps_completed += 1
                total_items_processed += items

            # All steps completed
            total_duration = int(time.time() - pipeline_start)
            await self._broadcast_pipeline_completed(run_id, total_duration, steps_completed, total_items_processed)
            state_updater("status", PipelineStatus.COMPLETED)
            state_updater("completed_at", datetime.now(timezone.utc).isoformat())
            return True

        except Exception as e:
            logger.exception(f"Pipeline execution error: {e}")
            await self._broadcast_pipeline_failed(run_id, str(e))
            state_updater("status", PipelineStatus.FAILED)
            state_updater("error", str(e))
            return False
        finally:
            self._is_running = False
            self._current_process = None

    async def _execute_step(
        self,
        step: PipelineStep,
        run_id: str,
        config: dict,
        state_updater: Callable[[str, Any], None],
    ) -> tuple[bool, int]:
        """
        Execute a single pipeline step.

        Returns:
            Tuple of (success, items_processed)
        """
        step_config = self.STEP_SCRIPTS.get(step)
        if not step_config:
            logger.error(f"No script configured for step: {step.value}")
            return False, 0

        script_path = self.project_root / step_config["script"]
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            # Skip missing scripts gracefully
            await self._skip_step(step, run_id, state_updater, f"Script not found: {script_path}")
            return True, 0

        # Build command - use the project's venv Python
        venv_python = self.project_root / "venv" / "bin" / "python3"
        python_cmd = str(venv_python) if venv_python.exists() else "python3"
        args = step_config["args_builder"](config)
        cmd = [python_cmd, str(script_path)] + args

        logger.info(f"Executing step {step.value}: {' '.join(cmd)}")

        # Update state to running
        state_updater("current_step", step)
        step_start = time.time()

        step_state = StepState(
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        state_updater(f"steps.{step.value}", step_state)

        # Broadcast step started
        await manager.broadcast({
            "type": "step_started",
            "step": step.value,
            "run_id": run_id,
        })

        items_processed = 0

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )
            self._current_process = process

            # Stream stdout for progress updates
            while True:
                if self._should_stop:
                    process.terminate()
                    break

                line = await process.stdout.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                if not line_str:
                    continue

                # Try to parse as JSON progress line
                if line_str.startswith("{"):
                    try:
                        progress_data = json.loads(line_str)
                        if progress_data.get("type") == "progress":
                            current = progress_data.get("current", 0)
                            total = progress_data.get("total", 0)
                            message = progress_data.get("message", "")
                            items_processed = current

                            # Calculate percentage
                            percentage = int((current / total) * 100) if total > 0 else 0

                            # Broadcast progress
                            await manager.broadcast({
                                "type": "step_progress",
                                "step": step.value,
                                "run_id": run_id,
                                "current": current,
                                "total": total,
                                "percentage": percentage,
                                "message": message,
                            })

                            # Update step state
                            step_state.progress = percentage
                            step_state.items_processed = current
                            step_state.items_total = total
                            step_state.message = message
                            state_updater(f"steps.{step.value}", step_state)
                    except json.JSONDecodeError:
                        # Not a JSON line, just log it
                        logger.debug(f"[{step.value}] {line_str}")
                else:
                    # Log non-JSON output
                    logger.debug(f"[{step.value}] {line_str}")

            # Wait for process to complete
            await process.wait()

            # Read any remaining stderr
            stderr_output = await process.stderr.read()
            if stderr_output:
                stderr_str = stderr_output.decode().strip()
                if stderr_str:
                    logger.warning(f"[{step.value}] stderr: {stderr_str}")

            # Check exit code
            if process.returncode != 0:
                error_msg = f"Exit code: {process.returncode}"
                logger.error(f"Step {step.value} failed with {error_msg}")

                step_state.status = "failed"
                step_state.error = error_msg
                step_state.completed_at = datetime.now(timezone.utc).isoformat()
                state_updater(f"steps.{step.value}", step_state)

                await manager.broadcast({
                    "type": "step_failed",
                    "step": step.value,
                    "run_id": run_id,
                    "error": error_msg,
                })
                return False, items_processed

            # Success
            duration = int(time.time() - step_start)

            step_state.status = "completed"
            step_state.progress = 100
            step_state.completed_at = datetime.now(timezone.utc).isoformat()
            state_updater(f"steps.{step.value}", step_state)

            await manager.broadcast({
                "type": "step_completed",
                "step": step.value,
                "run_id": run_id,
                "duration": duration,
                "items_processed": items_processed,
            })

            logger.info(f"Step {step.value} completed in {duration}s, processed {items_processed} items")
            return True, items_processed

        except Exception as e:
            logger.exception(f"Error executing step {step.value}: {e}")

            step_state.status = "failed"
            step_state.error = str(e)
            step_state.completed_at = datetime.now(timezone.utc).isoformat()
            state_updater(f"steps.{step.value}", step_state)

            await manager.broadcast({
                "type": "step_failed",
                "step": step.value,
                "run_id": run_id,
                "error": str(e),
            })
            return False, items_processed

    async def _skip_step(
        self,
        step: PipelineStep,
        run_id: str,
        state_updater: Callable[[str, Any], None],
        reason: str,
    ) -> None:
        """Mark a step as skipped."""
        step_state = StepState(
            status="skipped",
            message=reason,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        state_updater(f"steps.{step.value}", step_state)

        await manager.broadcast({
            "type": "step_skipped",
            "step": step.value,
            "run_id": run_id,
            "reason": reason,
        })

        logger.info(f"Step {step.value} skipped: {reason}")

    async def _broadcast_pipeline_completed(
        self, run_id: str, total_duration: int, steps_completed: int, sites_processed: int
    ) -> None:
        """Broadcast pipeline completion event."""
        await manager.broadcast({
            "type": "pipeline_completed",
            "run_id": run_id,
            "summary": {
                "total_duration": total_duration,
                "steps_completed": steps_completed,
                "total_steps": len(self.STEP_ORDER),
                "sites_processed": sites_processed,
            },
        })

    async def _broadcast_pipeline_failed(self, run_id: str, error: str) -> None:
        """Broadcast pipeline failure event."""
        await manager.broadcast({
            "type": "pipeline_failed",
            "run_id": run_id,
            "error": error,
        })

    async def _broadcast_pipeline_stopped(self, run_id: str) -> None:
        """Broadcast pipeline stopped event."""
        await manager.broadcast({
            "type": "pipeline_stopped",
            "run_id": run_id,
        })


# Global executor instance - initialized with project root
_project_root = Path(__file__).parent.parent.parent.parent
executor = PipelineExecutor(_project_root)
