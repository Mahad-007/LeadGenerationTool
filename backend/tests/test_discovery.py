"""Tests for discovery API endpoints - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestGetDiscovery:
    """Tests for GET /api/discovery endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/discovery")
        assert response.status_code == 200

    def test_returns_discovery_response(self, client):
        """Should return discovery response structure."""
        response = client.get("/api/discovery")
        data = response.json()

        assert "metadata" in data
        assert "discoveries" in data

    def test_metadata_has_required_fields(self, client):
        """Metadata should have required fields."""
        response = client.get("/api/discovery")
        data = response.json()

        metadata = data["metadata"]
        assert "generated_at" in metadata
        assert "total_niches" in metadata
        assert "total_urls" in metadata

    def test_discoveries_is_list(self, client):
        """Discoveries should be a list."""
        response = client.get("/api/discovery")
        data = response.json()

        assert isinstance(data["discoveries"], list)


class TestRunDiscovery:
    """Tests for POST /api/discovery/run endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/discovery/run")
        assert response.status_code == 200

    def test_returns_success_response(self, client):
        """Should return success response."""
        response = client.post("/api/discovery/run")
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_starts_discovery_step(self, client):
        """Should start discovery step."""
        response = client.post("/api/discovery/run")
        data = response.json()

        assert data["success"] is True
