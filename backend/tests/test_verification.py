"""Tests for verification API endpoints - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestGetVerification:
    """Tests for GET /api/verification endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/verification")
        assert response.status_code == 200

    def test_returns_verification_response(self, client):
        """Should return verification response structure."""
        response = client.get("/api/verification")
        data = response.json()

        assert "metadata" in data
        assert "shopify_sites" in data
        assert "verification_log" in data

    def test_metadata_has_required_fields(self, client):
        """Metadata should have required fields."""
        response = client.get("/api/verification")
        data = response.json()

        metadata = data["metadata"]
        assert "generated_at" in metadata
        assert "total_verified" in metadata
        assert "shopify_count" in metadata
        assert "non_shopify_count" in metadata

    def test_shopify_sites_is_list(self, client):
        """Shopify sites should be a list."""
        response = client.get("/api/verification")
        data = response.json()

        assert isinstance(data["shopify_sites"], list)


class TestRunVerification:
    """Tests for POST /api/verification/run endpoint."""

    def test_returns_200(self, client):
        """Should return 200 OK."""
        response = client.post("/api/verification/run")
        assert response.status_code == 200

    def test_returns_success_response(self, client):
        """Should return success response."""
        response = client.post("/api/verification/run")
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_starts_verification_step(self, client):
        """Should start verification step."""
        response = client.post("/api/verification/run")
        data = response.json()

        assert data["success"] is True
