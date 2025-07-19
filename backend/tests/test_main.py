import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Image Poet API Server"
    assert data["docs"] == "/docs"

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Image Poet API"
    assert data["version"] == "0.1.0"
    assert "storage" in data
    assert "uploads" in data

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS headers should be present due to middleware
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"

def test_cors_preflight():
    """Test CORS preflight request"""
    response = client.options(
        "/", 
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers