"""Pipeline Runner service for executing pipeline steps."""

from app.models.pipeline import PipelineStep
from app.websocket import manager


class PipelineRunner:
    """Runs the pipeline steps and broadcasts progress events."""

    def __init__(self):
        self.steps = [
            PipelineStep.DISCOVERY,
            PipelineStep.VERIFICATION,
            PipelineStep.AUDIT,
            PipelineStep.ANALYSIS,
            PipelineStep.CONTACTS,
            PipelineStep.OUTREACH,
        ]
        self.is_running = False
        self._should_stop = False

    def start(self) -> None:
        """Start the pipeline runner."""
        self.is_running = True
        self._should_stop = False

    def stop(self) -> None:
        """Stop the pipeline runner."""
        self.is_running = False
        self._should_stop = True

    @staticmethod
    def calculate_percentage(current: int, total: int) -> int:
        """Calculate progress percentage."""
        if total == 0:
            return 0
        percentage = int((current / total) * 100)
        return min(percentage, 100)

    async def broadcast_step_started(self, step: PipelineStep) -> None:
        """Broadcast step_started event."""
        await manager.broadcast({
            "type": "step_started",
            "step": step.value,
        })

    async def broadcast_step_progress(
        self,
        step: PipelineStep,
        current: int,
        total: int,
        message: str,
    ) -> None:
        """Broadcast step_progress event."""
        percentage = self.calculate_percentage(current, total)
        await manager.broadcast({
            "type": "step_progress",
            "step": step.value,
            "current": current,
            "total": total,
            "percentage": percentage,
            "message": message,
        })

    async def broadcast_step_completed(
        self,
        step: PipelineStep,
        duration: int,
        items_processed: int,
    ) -> None:
        """Broadcast step_completed event."""
        await manager.broadcast({
            "type": "step_completed",
            "step": step.value,
            "duration": duration,
            "items_processed": items_processed,
        })

    async def broadcast_step_failed(
        self,
        step: PipelineStep,
        error: str,
    ) -> None:
        """Broadcast step_failed event."""
        await manager.broadcast({
            "type": "step_failed",
            "step": step.value,
            "error": error,
        })

    async def broadcast_pipeline_completed(
        self,
        total_duration: int,
        steps_completed: int,
        sites_processed: int,
    ) -> None:
        """Broadcast pipeline_completed event."""
        await manager.broadcast({
            "type": "pipeline_completed",
            "summary": {
                "total_duration": total_duration,
                "steps_completed": steps_completed,
                "total_steps": len(self.steps),
                "sites_processed": sites_processed,
            },
        })

    async def broadcast_pipeline_failed(self, error: str) -> None:
        """Broadcast pipeline_failed event."""
        await manager.broadcast({
            "type": "pipeline_failed",
            "error": error,
        })
