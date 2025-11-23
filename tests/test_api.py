"""Tests for the FastAPI routes."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Test that health endpoint returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "wowasi_ya"


class TestProjectEndpoints:
    """Tests for project-related endpoints."""

    def test_create_project_requires_auth(self, client: TestClient) -> None:
        """Test that creating a project requires authentication."""
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "description": "A test project description that is long enough.",
            },
        )

        assert response.status_code == 401

    def test_create_project_with_auth(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that creating a project works with authentication."""
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "name": "Test Project",
                "description": "A test project description for healthcare in tribal communities.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "agent_discovery"

    def test_list_projects_requires_auth(self, client: TestClient) -> None:
        """Test that listing projects requires authentication."""
        response = client.get("/api/v1/projects")

        assert response.status_code == 401

    def test_list_projects_with_auth(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that listing projects works with authentication."""
        response = client.get("/api/v1/projects", headers=auth_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that getting a nonexistent project returns 404."""
        response = client.get(
            "/api/v1/projects/nonexistent-id/discovery",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestProjectWorkflow:
    """Tests for the full project workflow."""

    def test_create_and_discover(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating a project and running discovery."""
        # Create project
        create_response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "name": "Healthcare App",
                "description": "A telehealth application for tribal communities with HIPAA compliance.",
            },
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["project_id"]

        # Get discovery results
        discovery_response = client.get(
            f"/api/v1/projects/{project_id}/discovery",
            headers=auth_headers,
        )
        assert discovery_response.status_code == 200

        data = discovery_response.json()
        assert "domains" in data
        assert "agents" in data
        assert "privacy_scan" in data
        assert len(data["domains"]) > 0
        assert len(data["agents"]) > 0

    def test_get_status_after_create(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting project status after creation."""
        # Create project
        create_response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "name": "Status Test",
                "description": "Testing the status endpoint with a simple project.",
            },
        )
        project_id = create_response.json()["project_id"]

        # Get status
        status_response = client.get(
            f"/api/v1/projects/{project_id}/status",
            headers=auth_headers,
        )
        assert status_response.status_code == 200

        data = status_response.json()
        assert data["project_id"] == project_id
        assert "status" in data
        assert "phase" in data
