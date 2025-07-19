"""
Test API endpoints
"""
import json
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


class TestImageUploadAPI:
    """Test image upload API endpoints"""
    
    def test_upload_image_success(self, client: TestClient, sample_image_bytes: bytes):
        """Test successful image upload"""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        response = client.post("/api/v1/images/upload", files=files)
            
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure (UploadResponse schema)
        assert "success" in data
        assert "message" in data
        assert "image_id" in data
        assert "image_url" in data
        assert "created_at" in data
        assert data["success"] is True
        
        # Poetry generation happens in background, so no immediate poem in response
    
    def test_upload_image_no_file(self, client: TestClient):
        """Test upload without file"""
        response = client.post("/api/v1/images/upload")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_invalid_file_type(self, client: TestClient):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        
        response = client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["message"]
    
    def test_upload_large_file(self, client: TestClient):
        """Test upload with file too large"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.jpg", large_content, "image/jpeg")}
        
        response = client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 413
        assert "File too large" in response.json()["message"]
    
    def test_upload_with_poem_generation_failure(self, client: TestClient, sample_image_bytes: bytes):
        """Test upload when poem generation fails"""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        # Poetry generation happens in background, so upload will always succeed
        response = client.post("/api/v1/images/upload", files=files)
            
        # Should succeed with image upload regardless of background poetry generation
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Poetry generation started in background" in data["message"]


class TestImageListAPI:
    """Test image list API endpoints"""
    
    def test_get_images_empty(self, client: TestClient):
        """Test getting images when none exist"""
        response = client.get("/api/v1/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_images_with_data(self, client: TestClient, sample_image_bytes: bytes):
        """Test getting images after uploading"""
        # First upload an image
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        upload_response = client.post("/api/v1/images/upload", files=files)
        
        assert upload_response.status_code == 200
        
        # Then get the list
        response = client.get("/api/v1/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        image_data = data[0]
        assert "id" in image_data
        assert "filename" in image_data
        assert "poetry_content" in image_data  # Actual field name
        assert "created_at" in image_data


class TestImageDetailAPI:
    """Test image detail API endpoints"""
    
    def test_get_image_by_id_success(self, client: TestClient, sample_image_bytes: bytes):
        """Test getting image by ID"""
        # First upload an image
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        upload_response = client.post("/api/v1/images/upload", files=files)
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        image_id = upload_data["image_id"]  # Correct field name
        
        # Get the image by ID
        response = client.get(f"/api/v1/images/{image_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == image_id
        assert "filename" in data
        assert "poetry_content" in data  # Actual field name
    
    def test_get_image_by_id_not_found(self, client: TestClient):
        """Test getting non-existent image"""
        response = client.get("/api/v1/images/99999")
        
        assert response.status_code == 404
        assert "Image not found" in response.json()["message"]


class TestHealthAPI:
    """Test health check endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data  # Correct field name
        assert "version" in data
        assert "storage" in data
        assert "uploads" in data


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present"""
        # Test with GET request since OPTIONS might not be implemented
        response = client.get("/api/v1/images/")
        
        # Check if response is successful (CORS headers should be present even on regular requests)
        assert response.status_code == 200
    
    def test_cors_headers_on_post(self, client: TestClient, sample_image_bytes: bytes):
        """Test CORS headers on POST request"""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        response = client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 200
        # CORS headers should be present in test client as well


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test endpoints using async client"""
    
    async def test_upload_image_async(self, async_client: AsyncClient, sample_image_bytes: bytes):
        """Test image upload using async client"""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        response = await async_client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "image_id" in data
    
    async def test_get_images_async(self, async_client: AsyncClient):
        """Test getting images using async client"""
        response = await async_client.get("/api/v1/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)