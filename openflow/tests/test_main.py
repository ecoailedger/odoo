"""
Tests for main application
"""
import pytest
from fastapi.testclient import TestClient
from openflow.server.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Welcome to OpenFlow"


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_404_handler(client):
    """Test 404 error handler"""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
