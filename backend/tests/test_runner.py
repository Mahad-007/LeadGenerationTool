"""Tests for Pipeline Runner service - TDD approach."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.pipeline_runner import PipelineRunner
from app.models.pipeline import PipelineStep


@pytest.fixture
def runner():
    """Create a PipelineRunner instance."""
    return PipelineRunner()


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager."""
    with patch("app.services.pipeline_runner.manager") as mock:
        mock.broadcast = AsyncMock()
        yield mock


class TestPipelineRunnerInit:
    """Tests for PipelineRunner initialization."""

    def test_creates_runner_instance(self, runner):
        """Should create a PipelineRunner instance."""
        assert runner is not None

    def test_runner_has_steps_list(self, runner):
        """Runner should have a list of steps."""
        assert hasattr(runner, "steps")
        assert len(runner.steps) == 6

    def test_runner_steps_in_order(self, runner):
        """Runner steps should be in correct order."""
        expected_order = [
            PipelineStep.DISCOVERY,
            PipelineStep.VERIFICATION,
            PipelineStep.AUDIT,
            PipelineStep.ANALYSIS,
            PipelineStep.CONTACTS,
            PipelineStep.OUTREACH,
        ]
        assert runner.steps == expected_order


class TestPipelineRunnerState:
    """Tests for PipelineRunner state management."""

    def test_initial_state_is_idle(self, runner):
        """Initial state should be idle."""
        assert runner.is_running is False

    def test_can_start_runner(self, runner):
        """Should be able to start the runner."""
        runner.start()
        assert runner.is_running is True

    def test_can_stop_runner(self, runner):
        """Should be able to stop the runner."""
        runner.start()
        runner.stop()
        assert runner.is_running is False


class TestPipelineRunnerEvents:
    """Tests for PipelineRunner event broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcasts_step_started_event(self, runner, mock_websocket_manager):
        """Should broadcast step_started event when step begins."""
        await runner.broadcast_step_started(PipelineStep.DISCOVERY)

        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "step_started"
        assert call_args["step"] == "discovery"

    @pytest.mark.asyncio
    async def test_broadcasts_step_progress_event(self, runner, mock_websocket_manager):
        """Should broadcast step_progress event."""
        await runner.broadcast_step_progress(
            step=PipelineStep.DISCOVERY,
            current=5,
            total=10,
            message="Processing..."
        )

        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "step_progress"
        assert call_args["step"] == "discovery"
        assert call_args["current"] == 5
        assert call_args["total"] == 10
        assert call_args["percentage"] == 50
        assert call_args["message"] == "Processing..."

    @pytest.mark.asyncio
    async def test_broadcasts_step_completed_event(self, runner, mock_websocket_manager):
        """Should broadcast step_completed event when step finishes."""
        await runner.broadcast_step_completed(
            step=PipelineStep.DISCOVERY,
            duration=1500,
            items_processed=10
        )

        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "step_completed"
        assert call_args["step"] == "discovery"
        assert call_args["duration"] == 1500
        assert call_args["items_processed"] == 10

    @pytest.mark.asyncio
    async def test_broadcasts_step_failed_event(self, runner, mock_websocket_manager):
        """Should broadcast step_failed event when step fails."""
        await runner.broadcast_step_failed(
            step=PipelineStep.DISCOVERY,
            error="Connection failed"
        )

        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "step_failed"
        assert call_args["step"] == "discovery"
        assert call_args["error"] == "Connection failed"

    @pytest.mark.asyncio
    async def test_broadcasts_pipeline_completed_event(self, runner, mock_websocket_manager):
        """Should broadcast pipeline_completed event."""
        await runner.broadcast_pipeline_completed(
            total_duration=10000,
            steps_completed=6,
            sites_processed=25
        )

        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "pipeline_completed"
        assert "summary" in call_args
        assert call_args["summary"]["total_duration"] == 10000
        assert call_args["summary"]["steps_completed"] == 6
        assert call_args["summary"]["sites_processed"] == 25


class TestPipelineRunnerProgress:
    """Tests for progress calculation."""

    def test_calculates_percentage_correctly(self, runner):
        """Should calculate percentage correctly."""
        assert runner.calculate_percentage(0, 10) == 0
        assert runner.calculate_percentage(5, 10) == 50
        assert runner.calculate_percentage(10, 10) == 100

    def test_handles_zero_total(self, runner):
        """Should handle zero total gracefully."""
        assert runner.calculate_percentage(0, 0) == 0

    def test_clamps_percentage_to_100(self, runner):
        """Should clamp percentage to 100."""
        assert runner.calculate_percentage(15, 10) == 100
