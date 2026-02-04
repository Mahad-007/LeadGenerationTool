"""Tests for WebSocket pipeline handler - TDD approach."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    def test_websocket_connects_successfully(self, client):
        """Should establish WebSocket connection."""
        with client.websocket_connect("/ws/pipeline") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_receives_connected_event_on_connect(self, client):
        """Should receive 'connected' event after connection."""
        with client.websocket_connect("/ws/pipeline") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "client_id" in data

    def test_client_id_is_uuid_format(self, client):
        """Client ID should be in UUID format."""
        with client.websocket_connect("/ws/pipeline") as websocket:
            data = websocket.receive_json()
            client_id = data["client_id"]
            # Should be valid UUID format (36 chars with hyphens)
            assert len(client_id) == 36
            assert client_id.count("-") == 4


class TestWebSocketEvents:
    """Tests for WebSocket event handling."""

    def test_receives_pipeline_started_event(self, client):
        """Should receive pipeline_started event when pipeline starts."""
        with client.websocket_connect("/ws/pipeline") as websocket:
            # Get connected event
            websocket.receive_json()

            # Start pipeline via API
            response = client.post("/api/pipeline/run")
            assert response.status_code == 200

            # Should receive pipeline_started event
            data = websocket.receive_json()
            assert data["type"] == "pipeline_started"
            assert "run_id" in data
            assert "steps" in data

    def test_can_send_ping_and_receive_pong(self, client):
        """Should respond to ping with pong."""
        with client.websocket_connect("/ws/pipeline") as websocket:
            # Get connected event
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"


class TestWebSocketManager:
    """Tests for WebSocket connection management."""

    def test_multiple_connections_allowed(self, client):
        """Should allow multiple WebSocket connections."""
        with client.websocket_connect("/ws/pipeline") as ws1:
            with client.websocket_connect("/ws/pipeline") as ws2:
                # Both connections should work
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["type"] == "connected"
                assert data2["type"] == "connected"
                # Different client IDs
                assert data1["client_id"] != data2["client_id"]

    def test_broadcasts_to_all_connections(self, client):
        """Should broadcast pipeline events to all connections."""
        with client.websocket_connect("/ws/pipeline") as ws1:
            with client.websocket_connect("/ws/pipeline") as ws2:
                # Clear connected events
                ws1.receive_json()
                ws2.receive_json()

                # Start pipeline
                client.post("/api/pipeline/run")

                # Both should receive pipeline_started
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["type"] == "pipeline_started"
                assert data2["type"] == "pipeline_started"


class TestWebSocketReconnection:
    """Tests for WebSocket reconnection handling."""

    def test_can_reconnect_after_disconnect(self, client):
        """Should allow reconnection after disconnect."""
        # First connection
        with client.websocket_connect("/ws/pipeline") as ws:
            data1 = ws.receive_json()
            client_id_1 = data1["client_id"]

        # Reconnect (should get new client ID)
        with client.websocket_connect("/ws/pipeline") as ws:
            data2 = ws.receive_json()
            client_id_2 = data2["client_id"]

        # Both should have been valid connections
        assert client_id_1 != client_id_2
