"""Tests for audit API endpoints - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestGetAudit:
    """Tests for GET /api/audit endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/audit")
        assert response.status_code == 200

    def test_returns_audit_response(self, client):
        """Should return audit response structure."""
        response = client.get("/api/audit")
        data = response.json()

        assert "metadata" in data
        assert "audits" in data

    def test_metadata_has_required_fields(self, client):
        """Metadata should have required fields."""
        response = client.get("/api/audit")
        data = response.json()

        metadata = data["metadata"]
        assert "generated_at" in metadata
        assert "total_sites" in metadata
        assert "successful" in metadata
        assert "failed" in metadata

    def test_audits_is_list(self, client):
        """Audits should be a list."""
        response = client.get("/api/audit")
        data = response.json()

        assert isinstance(data["audits"], list)


class TestRunAudit:
    """Tests for POST /api/audit/run endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/audit/run")
        assert response.status_code == 200

    def test_returns_success_response(self, client):
        """Should return success response."""
        response = client.post("/api/audit/run")
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_starts_audit_step(self, client):
        """Should start audit step."""
        response = client.post("/api/audit/run")
        data = response.json()

        assert data["success"] is True


class TestGetScreenshot:
    """Tests for GET /api/audit/screenshot/{filename} endpoint."""

    def test_returns_404_for_missing_file(self, client):
        """Should return 404 for non-existent screenshot."""
        response = client.get("/api/audit/screenshot/nonexistent.png")
        assert response.status_code == 404

    def test_returns_error_message_for_missing_file(self, client):
        """Should return error message for missing file."""
        response = client.get("/api/audit/screenshot/nonexistent.png")
        data = response.json()

        assert "detail" in data
