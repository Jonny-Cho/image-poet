"""
Test S3 integration with LocalStack and real AWS
"""
import pytest
import asyncio
import io
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import UploadFile
import boto3
from botocore.exceptions import ClientError

from app.services.s3_service import S3Service
from app.core.config import settings


@pytest.mark.asyncio
class TestS3ServiceIntegration:
    """Test S3Service with real LocalStack integration"""
    
    @pytest.fixture
    def s3_service(self):
        """Create S3Service instance"""
        return S3Service()
    
    @pytest.fixture
    def mock_upload_file(self, sample_image_bytes):
        """Create mock UploadFile for testing"""
        from unittest.mock import MagicMock, AsyncMock
        file_obj = io.BytesIO(sample_image_bytes)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = file_obj
        upload_file.filename = "test_s3.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.size = len(sample_image_bytes)
        
        # Mock async methods properly
        upload_file.read = AsyncMock(return_value=sample_image_bytes)
        upload_file.seek = AsyncMock(return_value=None)
        
        return upload_file
    
    async def test_s3_service_availability(self, s3_service):
        """Test S3 service availability check"""
        # This will depend on whether LocalStack is configured
        if settings.USE_S3_STORAGE and settings.USE_LOCALSTACK:
            # If LocalStack is configured, service should be available
            assert s3_service.is_available()
        else:
            # If not configured for S3, should not be available
            assert not s3_service.is_available()
    
    async def test_upload_file_to_localstack(self, s3_service, mock_upload_file):
        """Test uploading file to LocalStack S3"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        # Test upload
        s3_key, s3_url = await s3_service.upload_file(mock_upload_file)
        
        assert s3_key is not None
        assert s3_url is not None
        assert s3_key.startswith("images/")
        assert s3_key.endswith(".jpg")
        
        # Verify file exists
        exists = await s3_service.check_file_exists(s3_key)
        assert exists is True
        
        # Clean up
        await s3_service.delete_file(s3_key)
    
    async def test_upload_with_custom_key(self, s3_service, mock_upload_file):
        """Test uploading file with custom S3 key"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        custom_key = "custom/test_key.jpg"
        s3_key, s3_url = await s3_service.upload_file(mock_upload_file, custom_key)
        
        assert s3_key == custom_key
        assert custom_key in s3_url
        
        # Verify file exists
        exists = await s3_service.check_file_exists(s3_key)
        assert exists is True
        
        # Clean up
        await s3_service.delete_file(s3_key)
    
    async def test_delete_file(self, s3_service, mock_upload_file):
        """Test deleting file from S3"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        # First upload a file
        s3_key, s3_url = await s3_service.upload_file(mock_upload_file)
        
        # Verify it exists
        exists = await s3_service.check_file_exists(s3_key)
        assert exists is True
        
        # Delete it
        deleted = await s3_service.delete_file(s3_key)
        assert deleted is True
        
        # Verify it's gone
        exists = await s3_service.check_file_exists(s3_key)
        assert exists is False
    
    async def test_generate_presigned_url(self, s3_service, mock_upload_file):
        """Test generating presigned URLs"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        # Upload a file
        s3_key, s3_url = await s3_service.upload_file(mock_upload_file)
        
        # Generate presigned URL
        presigned_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
        
        assert presigned_url is not None
        assert isinstance(presigned_url, str)
        assert s3_key in presigned_url
        
        # Clean up
        await s3_service.delete_file(s3_key)
    
    async def test_upload_local_file(self, s3_service, sample_image_file):
        """Test uploading local file to S3"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        s3_key = "local_upload/test.jpg"
        s3_url = await s3_service.upload_local_file(str(sample_image_file), s3_key)
        
        assert s3_url is not None
        assert s3_key in s3_url
        
        # Verify file exists
        exists = await s3_service.check_file_exists(s3_key)
        assert exists is True
        
        # Clean up
        await s3_service.delete_file(s3_key)
    
    async def test_get_bucket_info(self, s3_service):
        """Test getting bucket information"""
        if not s3_service.is_available():
            pytest.skip("S3 service not available for testing")
        
        bucket_info = await s3_service.get_bucket_info()
        
        assert isinstance(bucket_info, dict)
        assert "bucket_name" in bucket_info
        assert "region" in bucket_info
        assert "total_objects" in bucket_info
        assert "total_size_mb" in bucket_info
        
        # Should match configured bucket name
        assert bucket_info["bucket_name"] == s3_service.bucket_name


@pytest.mark.asyncio
class TestS3ServiceMocked:
    """Test S3Service with mocked AWS operations"""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client"""
        client = MagicMock()
        return client
    
    @pytest.fixture
    def s3_service_with_mock(self, mock_s3_client):
        """Create S3Service with mocked client"""
        service = S3Service()
        service.s3_client = mock_s3_client
        service.bucket_name = "test-bucket"
        return service
    
    @pytest.fixture
    def mock_upload_file(self, sample_image_bytes):
        """Create mock UploadFile for testing"""
        from unittest.mock import MagicMock, AsyncMock
        file_obj = io.BytesIO(sample_image_bytes)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = file_obj
        upload_file.filename = "test_s3.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.size = len(sample_image_bytes)
        
        # Mock async methods properly
        upload_file.read = AsyncMock(return_value=sample_image_bytes)
        upload_file.seek = AsyncMock(return_value=None)
        
        return upload_file
    
    async def test_upload_file_client_error(self, s3_service_with_mock, mock_upload_file):
        """Test upload with S3 client error"""
        # Mock put_object to raise ClientError
        error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}}
        s3_service_with_mock.s3_client.put_object.side_effect = ClientError(error_response, 'put_object')
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await s3_service_with_mock.upload_file(mock_upload_file)
    
    async def test_upload_file_access_denied(self, s3_service_with_mock, mock_upload_file):
        """Test upload with access denied error"""
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        s3_service_with_mock.s3_client.put_object.side_effect = ClientError(error_response, 'put_object')
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await s3_service_with_mock.upload_file(mock_upload_file)
    
    async def test_upload_file_generic_error(self, s3_service_with_mock, mock_upload_file):
        """Test upload with generic error"""
        s3_service_with_mock.s3_client.put_object.side_effect = Exception("Generic error")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await s3_service_with_mock.upload_file(mock_upload_file)
    
    async def test_check_file_exists_not_found(self, s3_service_with_mock):
        """Test checking file that doesn't exist"""
        error_response = {'Error': {'Code': '404', 'Message': 'Not found'}}
        s3_service_with_mock.s3_client.head_object.side_effect = ClientError(error_response, 'head_object')
        
        exists = await s3_service_with_mock.check_file_exists("nonexistent.jpg")
        assert exists is False
    
    async def test_check_file_exists_error(self, s3_service_with_mock):
        """Test checking file with S3 error"""
        error_response = {'Error': {'Code': 'InternalError', 'Message': 'Internal error'}}
        s3_service_with_mock.s3_client.head_object.side_effect = ClientError(error_response, 'head_object')
        
        exists = await s3_service_with_mock.check_file_exists("test.jpg")
        assert exists is False
    
    async def test_delete_file_error(self, s3_service_with_mock):
        """Test deleting file with S3 error"""
        s3_service_with_mock.s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'InternalError'}}, 'delete_object'
        )
        
        result = await s3_service_with_mock.delete_file("test.jpg")
        assert result is False
    
    async def test_generate_presigned_url_error(self, s3_service_with_mock):
        """Test generating presigned URL with error"""
        s3_service_with_mock.s3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InternalError'}}, 'generate_presigned_url'
        )
        
        url = await s3_service_with_mock.generate_presigned_url("test.jpg")
        assert url is None


class TestS3ServiceConfiguration:
    """Test S3Service configuration scenarios"""
    
    def test_s3_service_without_configuration(self):
        """Test S3Service when S3 is not configured"""
        with patch.object(settings, 'USE_S3_STORAGE', False):
            service = S3Service()
            assert service.s3_client is None
            assert not service.is_available()
    
    def test_s3_service_localstack_configuration(self):
        """Test S3Service with LocalStack configuration"""
        with patch.object(settings, 'USE_S3_STORAGE', True), \
             patch.object(settings, 'USE_LOCALSTACK', True), \
             patch.object(settings, 'LOCALSTACK_ENDPOINT', 'http://localhost:4566'), \
             patch.object(settings, 'S3_BUCKET_NAME', 'test-bucket'):
            
            service = S3Service()
            # Should have initialized client (though connection may fail in tests)
            assert service.bucket_name == 'test-bucket'
    
    def test_s3_service_aws_configuration_missing_credentials(self):
        """Test S3Service with missing AWS credentials"""
        with patch.object(settings, 'USE_S3_STORAGE', True), \
             patch.object(settings, 'USE_LOCALSTACK', False), \
             patch.object(settings, 'AWS_ACCESS_KEY_ID', None), \
             patch.object(settings, 'AWS_SECRET_ACCESS_KEY', None):
            
            with pytest.raises(ValueError, match="AWS credentials and bucket name are required"):
                S3Service()
    
    def test_s3_service_aws_configuration_valid(self):
        """Test S3Service with valid AWS configuration"""
        with patch.object(settings, 'USE_S3_STORAGE', True), \
             patch.object(settings, 'USE_LOCALSTACK', False), \
             patch.object(settings, 'AWS_ACCESS_KEY_ID', 'test-key'), \
             patch.object(settings, 'AWS_SECRET_ACCESS_KEY', 'test-secret'), \
             patch.object(settings, 'S3_BUCKET_NAME', 'test-bucket'), \
             patch.object(settings, 'AWS_DEFAULT_REGION', 'us-east-1'):
            
            service = S3Service()
            assert service.bucket_name == 'test-bucket'
            assert service.is_available()
    
    def test_content_type_detection(self):
        """Test content type detection"""
        service = S3Service()
        
        assert service._get_content_type('.jpg') == 'image/jpeg'
        assert service._get_content_type('.jpeg') == 'image/jpeg'
        assert service._get_content_type('.png') == 'image/png'
        assert service._get_content_type('.gif') == 'image/gif'
        assert service._get_content_type('.webp') == 'image/webp'
        assert service._get_content_type('.bmp') == 'image/bmp'
        assert service._get_content_type('.tiff') == 'image/tiff'
        assert service._get_content_type('.svg') == 'image/svg+xml'
        assert service._get_content_type('.unknown') == 'application/octet-stream'
        assert service._get_content_type('') == 'application/octet-stream'