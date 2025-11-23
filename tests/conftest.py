"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from wowasi_ya.config import Settings
from wowasi_ya.main import app
from wowasi_ya.models.project import ProjectInput


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with mock API key."""
    return Settings(
        environment="development",
        anthropic_api_key="test-api-key",  # type: ignore
        secret_key="test-secret-key",  # type: ignore
        admin_username="testuser",
        admin_password="testpass",  # type: ignore
    )


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create basic auth headers for test requests."""
    import base64

    credentials = base64.b64encode(b"admin:changeme").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def sample_project() -> ProjectInput:
    """Create a sample project input for testing."""
    return ProjectInput(
        name="Test Healthcare Project",
        description="A telehealth application for rural tribal communities providing "
        "medical consultations and wellness tracking. Must comply with HIPAA and "
        "IHS regulations while respecting tribal data sovereignty.",
        additional_context="Budget is limited. Single developer team.",
        output_format="filesystem",
    )


@pytest.fixture
def sample_project_minimal() -> ProjectInput:
    """Create a minimal project input for testing."""
    return ProjectInput(
        name="Simple App",
        description="A simple web application for tracking tasks.",
    )
