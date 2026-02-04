"""Tests for outreach API endpoints - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestGetOutreach:
    """Tests for GET /api/outreach endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/outreach")
        assert response.status_code == 200

    def test_returns_outreach_response(self, client):
        """Should return outreach response structure."""
        response = client.get("/api/outreach")
        data = response.json()

        assert "metadata" in data
        assert "drafts" in data

    def test_metadata_has_required_fields(self, client):
        """Metadata should have required fields."""
        response = client.get("/api/outreach")
        data = response.json()

        metadata = data["metadata"]
        assert "generated_at" in metadata
        assert "total_drafts" in metadata
        assert "with_emails" in metadata
        assert "without_emails" in metadata

    def test_drafts_is_list(self, client):
        """Drafts should be a list."""
        response = client.get("/api/outreach")
        data = response.json()

        assert isinstance(data["drafts"], list)


class TestRunOutreach:
    """Tests for POST /api/outreach/run endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/outreach/run")
        assert response.status_code == 200

    def test_returns_success_response(self, client):
        """Should return success response."""
        response = client.post("/api/outreach/run")
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_starts_outreach_step(self, client):
        """Should start outreach step."""
        response = client.post("/api/outreach/run")
        data = response.json()

        assert data["success"] is True


class TestUpdateOutreach:
    """Tests for PUT /api/outreach/{url} endpoint."""

    def test_returns_404_for_unknown_url(self, client):
        """Should return 404 for unknown store URL."""
        response = client.put(
            "/api/outreach/https://unknown-store.com",
            json={"subject": "Updated subject"}
        )
        assert response.status_code == 404

    def test_accepts_subject_update(self, client):
        """Should accept subject update in body."""
        # This will return 404 since store doesn't exist
        response = client.put(
            "/api/outreach/https://test-store.com",
            json={"subject": "New subject line"}
        )
        # Just verify it accepts the JSON body structure
        assert response.status_code in [200, 404]

    def test_accepts_body_update(self, client):
        """Should accept body update in body."""
        response = client.put(
            "/api/outreach/https://test-store.com",
            json={"body": "New email body"}
        )
        assert response.status_code in [200, 404]

    def test_accepts_status_update(self, client):
        """Should accept status update in body."""
        response = client.put(
            "/api/outreach/https://test-store.com",
            json={"status": "sent"}
        )
        assert response.status_code in [200, 404]
