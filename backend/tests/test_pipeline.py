"""Tests for pipeline API endpoints - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestGetPipelineStatus:
    """Tests for GET /api/pipeline/status endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/pipeline/status")
        assert response.status_code == 200

    def test_returns_pipeline_state(self, client):
        """Should return pipeline state object."""
        response = client.get("/api/pipeline/status")
        data = response.json()

        assert "status" in data
        assert "current_step" in data
        assert "steps" in data

    def test_default_status_is_idle(self, client):
        """Should return idle status by default."""
        response = client.get("/api/pipeline/status")
        data = response.json()

        assert data["status"] == "idle"
        assert data["current_step"] is None

    def test_contains_all_steps(self, client):
        """Should contain state for all pipeline steps."""
        response = client.get("/api/pipeline/status")
        data = response.json()

        expected_steps = ["discovery", "verification", "audit", "analysis", "contacts", "outreach"]
        for step in expected_steps:
            assert step in data["steps"]

    def test_step_has_required_fields(self, client):
        """Each step should have required state fields."""
        response = client.get("/api/pipeline/status")
        data = response.json()

        step_state = data["steps"]["discovery"]
        assert "status" in step_state
        assert "progress" in step_state
        assert "items_processed" in step_state
        assert "items_total" in step_state


class TestRunPipeline:
    """Tests for POST /api/pipeline/run endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/pipeline/run")
        assert response.status_code == 200

    def test_returns_success_response(self, client):
        """Should return success response with run_id."""
        response = client.post("/api/pipeline/run")
        data = response.json()

        assert "success" in data
        assert "message" in data
        assert "run_id" in data

    def test_returns_run_id(self, client):
        """Should return a run_id when started successfully."""
        response = client.post("/api/pipeline/run")
        data = response.json()

        assert data["success"] is True
        assert data["run_id"] is not None

    def test_cannot_start_when_running(self, client):
        """Should return error if pipeline is already running."""
        # Start pipeline first
        client.post("/api/pipeline/run")

        # Try to start again
        response = client.post("/api/pipeline/run")
        data = response.json()

        # Should indicate pipeline is already running
        assert data["success"] is False
        assert "already running" in data["message"].lower()


class TestStopPipeline:
    """Tests for POST /api/pipeline/stop endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/pipeline/stop")
        assert response.status_code == 200

    def test_returns_stop_response(self, client):
        """Should return stop response."""
        response = client.post("/api/pipeline/stop")
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_stops_running_pipeline(self, client):
        """Should stop a running pipeline."""
        # Start pipeline
        client.post("/api/pipeline/run")

        # Stop it
        response = client.post("/api/pipeline/stop")
        data = response.json()

        assert data["success"] is True

    def test_returns_message_when_not_running(self, client):
        """Should indicate when no pipeline is running."""
        response = client.post("/api/pipeline/stop")
        data = response.json()

        # Should handle gracefully
        assert "message" in data


class TestPipelineStatusAfterRun:
    """Tests for pipeline status changes after run/stop."""

    def test_status_changes_to_running(self, client):
        """Status should change to running after starting."""
        client.post("/api/pipeline/run")

        response = client.get("/api/pipeline/status")
        data = response.json()

        assert data["status"] == "running"

    def test_has_run_id_when_running(self, client):
        """Should have run_id when running."""
        run_response = client.post("/api/pipeline/run")
        run_id = run_response.json()["run_id"]

        status_response = client.get("/api/pipeline/status")
        data = status_response.json()

        assert data["run_id"] == run_id

    def test_status_changes_to_idle_after_stop(self, client):
        """Status should change back to idle after stopping."""
        client.post("/api/pipeline/run")
        client.post("/api/pipeline/stop")

        response = client.get("/api/pipeline/status")
        data = response.json()

        assert data["status"] == "idle"


class TestPipelineValidation:
    """Tests for pipeline input validation."""

    def test_get_status_accepts_no_body(self, client):
        """GET status should work without request body."""
        response = client.get("/api/pipeline/status")
        assert response.status_code == 200

    def test_run_accepts_no_body(self, client):
        """POST run should work without request body."""
        response = client.post("/api/pipeline/run")
        assert response.status_code == 200

    def test_stop_accepts_no_body(self, client):
        """POST stop should work without request body."""
        response = client.post("/api/pipeline/stop")
        assert response.status_code == 200
