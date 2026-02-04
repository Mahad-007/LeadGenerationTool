import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import pipeline


@pytest.fixture(autouse=True)
def reset_pipeline_state():
    """Reset pipeline state before each test."""
    pipeline._reset_state()
    yield
    pipeline._reset_state()


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)
