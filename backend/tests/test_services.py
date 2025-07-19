"""
Test service layer components
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import UploadFile
import io

from app.services.image_service import ImageService
from app.services.poetry_service import PoetryService
from app.services.s3_service import S3Service
from app.core.config import settings


class TestImageService:
    """Test ImageService functionality"""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance"""
        return ImageService()
    
    @pytest.fixture
    def mock_upload_file(self, sample_image_bytes):
        """Create mock UploadFile"""
        file_obj = io.BytesIO(sample_image_bytes)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = file_obj
        upload_file.filename = "test.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.size = len(sample_image_bytes)
        return upload_file
    
    def test_validate_file_success(self, image_service, mock_upload_file):
        """Test successful file validation"""
        # Should not raise exception
        image_service._validate_file(mock_upload_file)
    
    def test_validate_file_invalid_type(self, image_service):
        """Test file validation with invalid type"""
        file_obj = io.BytesIO(b"not an image")
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = file_obj
        upload_file.filename = "test.txt"
        upload_file.content_type = "text/plain"
        upload_file.size = 100
        
        with pytest.raises(Exception):  # HTTPException
            image_service._validate_file(upload_file)
    
    def test_validate_file_too_large(self, image_service):
        """Test file validation with file too large"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        file_obj = io.BytesIO(large_content)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = file_obj
        upload_file.filename = "large.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.size = len(large_content)
        
        with pytest.raises(Exception):  # HTTPException
            image_service._validate_file(upload_file)
    
    def test_get_file_extension(self, image_service):
        """Test file extension extraction"""
        ext1 = image_service._get_file_extension("test.jpg")
        ext2 = image_service._get_file_extension("image.png")
        
        assert ext1 == ".jpg"
        assert ext2 == ".png"
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_local_storage(self, image_service, mock_upload_file, setup_test_db):
        """Test saving image to local storage"""
        from sqlalchemy.orm import sessionmaker
        from app.core.database import engine
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()
        
        try:
            with patch.object(image_service.s3_service, 'is_available', return_value=False):
                # Reset file pointer
                mock_upload_file.file.seek(0)
                
                result = await image_service.save_uploaded_file(mock_upload_file, db)
                
                assert result.filename is not None
                assert result.file_path is not None
                assert result.filename.endswith(".jpg")
                assert result.original_filename == "test.jpg"
                
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_s3_storage(self, image_service, mock_upload_file, setup_test_db):
        """Test saving image to S3 storage"""
        from sqlalchemy.orm import sessionmaker
        from app.core.database import engine
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()
        
        try:
            with patch.object(image_service.s3_service, 'is_available', return_value=True), \
                 patch.object(image_service.s3_service, 'upload_file', 
                            return_value=("images/test.jpg", "https://s3.url/test.jpg")) as mock_upload, \
                 patch('app.services.image_service.settings') as mock_settings:
                
                # Mock settings to enable S3
                mock_settings.USE_S3_STORAGE = True
                
                # Reset file pointer
                mock_upload_file.file.seek(0)
                
                result = await image_service.save_uploaded_file(mock_upload_file, db)
                
                assert result.filename is not None
                assert result.file_path == "https://s3.url/test.jpg"
                
                # Verify S3 upload was called
                mock_upload.assert_called_once()
                
        finally:
            db.close()


class TestPoetryService:
    """Test PoetryService functionality"""
    
    @pytest.fixture
    def poetry_service(self):
        """Create PoetryService instance"""
        with patch.object(settings, 'OPENAI_API_KEY', 'test-api-key'):
            return PoetryService()
    
    @pytest.mark.asyncio
    async def test_generate_poem_success(self, poetry_service, mock_openai_response):
        """Test successful poem generation"""
        with patch.object(poetry_service, '_encode_image') as mock_encode, \
             patch.object(poetry_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "fake_base64_image"
            
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="제목: 아름다운 시\n\n꽃이 피어나고\n새가 노래하네"))
            ]
            mock_create.return_value = mock_response
            
            title, content = await poetry_service.generate_poetry_from_image("test_image.jpg")
            
            assert title is not None
            assert content is not None
            assert "꽃이 피어나고" in content
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_poem_no_api_key(self):
        """Test poem generation without API key"""
        with patch.object(settings, 'OPENAI_API_KEY', None):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                PoetryService()
    
    @pytest.mark.asyncio
    async def test_generate_poem_api_error(self, poetry_service):
        """Test poem generation with API error"""
        with patch.object(poetry_service, '_encode_image') as mock_encode, \
             patch.object(poetry_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "fake_base64_image"
            
            # Mock API error
            mock_create.side_effect = Exception("API Error")
            
            # Should raise exception
            with pytest.raises(Exception, match="Failed to generate poetry"):
                await poetry_service.generate_poetry_from_image("test_image.jpg")
    
    def test_parse_poetry_response(self, poetry_service):
        """Test poetry response parsing"""
        response = "제목: 아름다운 시\n\n꽃이 피어나고\n새가 노래하네"
        title, content = poetry_service._parse_poetry_response(response, "korean")
        
        assert title == "아름다운 시"
        assert "꽃이 피어나고" in content
        assert "새가 노래하네" in content
    
    def test_parse_poetry_response_without_title(self, poetry_service):
        """Test parsing poetry response without explicit title"""
        response = "꽃이 피어나고\n새가 노래하네\n바람이 불어온다"
        title, content = poetry_service._parse_poetry_response(response, "korean")
        
        assert title == "꽃이 피어나고"
        assert "새가 노래하네" in content


class TestS3Service:
    """Test S3Service functionality"""
    
    @pytest.fixture
    def s3_service(self):
        """Create S3Service instance"""
        return S3Service()
    
    def test_s3_service_initialization_localstack(self, s3_service):
        """Test S3Service initialization with LocalStack"""
        with patch.object(settings, 'USE_S3_STORAGE', True), \
             patch.object(settings, 'USE_LOCALSTACK', True):
            
            service = S3Service()
            # Should initialize without error
            assert service is not None
    
    def test_s3_service_initialization_no_s3(self, s3_service):
        """Test S3Service initialization without S3"""
        with patch.object(settings, 'USE_S3_STORAGE', False):
            service = S3Service()
            assert not service.is_available()
    
    def test_is_available_with_client(self, s3_service):
        """Test is_available method"""
        if s3_service.s3_client is not None:
            assert s3_service.is_available()
        else:
            assert not s3_service.is_available()
    
    @pytest.mark.asyncio
    async def test_upload_file_not_available(self, s3_service, sample_image_bytes):
        """Test upload when S3 is not available"""
        # Create mock upload file
        file_obj = io.BytesIO(sample_image_bytes)
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.file = file_obj
        mock_upload_file.filename = "test.jpg"
        mock_upload_file.content_type = "image/jpeg"
        mock_upload_file.size = len(sample_image_bytes)
        
        with patch.object(s3_service, 'is_available', return_value=False):
            with pytest.raises(Exception):  # Should raise HTTPException
                await s3_service.upload_file(mock_upload_file)
    
    def test_get_content_type(self, s3_service):
        """Test content type detection"""
        assert s3_service._get_content_type('.jpg') == 'image/jpeg'
        assert s3_service._get_content_type('.png') == 'image/png'
        assert s3_service._get_content_type('.unknown') == 'application/octet-stream'
    
    @pytest.mark.asyncio
    async def test_check_file_exists_not_available(self, s3_service):
        """Test file existence check when S3 not available"""
        with patch.object(s3_service, 'is_available', return_value=False):
            result = await s3_service.check_file_exists("test.jpg")
            assert result is False


class TestServiceIntegration:
    """Test integration between services"""
    
    @pytest.mark.asyncio
    async def test_image_service_with_poetry_service(self, sample_image_bytes, setup_test_db):
        """Test ImageService integration with PoetryService"""
        from sqlalchemy.orm import sessionmaker
        from app.core.database import engine
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()
        
        try:
            image_service = ImageService()
            
            # Create mock upload file
            file_obj = io.BytesIO(sample_image_bytes)
            upload_file = MagicMock(spec=UploadFile)
            upload_file.file = file_obj
            upload_file.filename = "test.jpg"
            upload_file.content_type = "image/jpeg"
            upload_file.size = len(sample_image_bytes)
            
            # Save image
            with patch.object(image_service.s3_service, 'is_available', return_value=False):
                result = await image_service.save_uploaded_file(upload_file, db)
                
                assert result.filename is not None
                assert result.file_path is not None
                
                # Now test with poetry service
                with patch.object(settings, 'OPENAI_API_KEY', 'test-api-key'):
                    poetry_service = PoetryService()
                    
                    with patch.object(poetry_service, 'generate_poetry_from_image') as mock_generate:
                        mock_generate.return_value = ("테스트 제목", "통합 테스트 시")
                        
                        title, poem = await poetry_service.generate_poetry_from_image(result.file_path)
                        assert title == "테스트 제목"
                        assert poem == "통합 테스트 시"
                        
        finally:
            db.close()