"""
Test database models and schemas
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.image import Image
from app.schemas.image import ImageCreate, ImageResponse


class TestImageModel:
    """Test Image database model"""
    
    def test_create_image_model(self, setup_test_db):
        """Test creating Image model instance"""
        from datetime import datetime
        now = datetime.utcnow()
        
        image = Image(
            filename="test.jpg",
            original_filename="original_test.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            poetry_content="테스트 시입니다",
            created_at=now,
            updated_at=now
        )
        
        assert image.filename == "test.jpg"
        assert image.original_filename == "original_test.jpg"
        assert image.file_path == "/uploads/test.jpg"
        assert image.poetry_content == "테스트 시입니다"
        assert image.file_size == 1024
        assert image.mime_type == "image/jpeg"
        assert image.created_at == now
        assert isinstance(image.created_at, datetime)
    
    def test_image_model_defaults(self, setup_test_db):
        """Test Image model default values"""
        image = Image(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024,
            mime_type="image/jpeg"
        )
        
        # Test that optional fields can be None
        assert image.poetry_content is None
        assert image.poetry_title is None
        assert image.width is None
        assert image.height is None
        assert image.upload_ip is None
        assert image.user_agent is None
        
        # Note: SQLAlchemy defaults are set when inserting to DB, not on object creation
    
    def test_image_model_repr(self, setup_test_db):
        """Test Image model string representation"""
        image = Image(
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024,
            mime_type="image/jpeg"
        )
        
        repr_str = repr(image)
        assert "Image" in repr_str
        assert "test.jpg" in repr_str
        assert "poetry_generated" in repr_str


class TestImageSchemas:
    """Test Image Pydantic schemas"""
    
    def test_image_create_schema(self):
        """Test ImageCreate schema"""
        image_data = {
            "filename": "test.jpg",
            "original_filename": "original.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg"
        }
        
        image_create = ImageCreate(**image_data)
        
        assert image_create.filename == "test.jpg"
        assert image_create.original_filename == "original.jpg"
        assert image_create.file_path == "/uploads/test.jpg"
        assert image_create.file_size == 1024
        assert image_create.mime_type == "image/jpeg"
    
    def test_image_create_schema_optional_fields(self):
        """Test ImageCreate schema with optional fields"""
        image_data = {
            "filename": "test.jpg",
            "original_filename": "test.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg"
        }
        
        image_create = ImageCreate(**image_data)
        
        assert image_create.filename == "test.jpg"
        assert image_create.file_path == "/uploads/test.jpg"
        assert image_create.width is None
        assert image_create.height is None
        assert image_create.upload_ip is None
        assert image_create.user_agent is None
    
    def test_image_response_schema(self):
        """Test ImageResponse schema"""
        now = datetime.now()
        image_data = {
            "id": 1,
            "filename": "test.jpg",
            "original_filename": "original.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg",
            "poetry_content": "테스트 시",
            "poetry_generated": True,
            "created_at": now,
            "updated_at": now
        }
        
        image_response = ImageResponse(**image_data)
        
        assert image_response.id == 1
        assert image_response.filename == "test.jpg"
        assert image_response.original_filename == "original.jpg"
        assert image_response.file_path == "/uploads/test.jpg"
        assert image_response.poetry_content == "테스트 시"
        assert image_response.file_size == 1024
        assert image_response.mime_type == "image/jpeg"
        assert image_response.poetry_generated is True
        assert isinstance(image_response.created_at, datetime)
    
    def test_image_response_schema_validation(self):
        """Test ImageResponse schema validation"""
        # Test with invalid data
        with pytest.raises(Exception):  # Pydantic ValidationError
            ImageResponse(
                id="not_an_integer",
                filename="test.jpg",
                original_filename="test.jpg",
                file_path="/uploads/test.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_image_response_json_serialization(self):
        """Test ImageResponse JSON serialization"""
        now = datetime.now()
        image_data = {
            "id": 1,
            "filename": "test.jpg",
            "original_filename": "test.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg",
            "created_at": now,
            "updated_at": now
        }
        
        image_response = ImageResponse(**image_data)
        json_data = image_response.model_dump()
        
        assert isinstance(json_data, dict)
        assert json_data["id"] == 1
        assert json_data["filename"] == "test.jpg"
        assert json_data["file_path"] == "/uploads/test.jpg"
        assert json_data["file_size"] == 1024
        assert "created_at" in json_data
    
    def test_image_response_json_serialization_with_datetime(self):
        """Test ImageResponse JSON serialization with datetime formatting"""
        now = datetime.now()
        image_data = {
            "id": 1,
            "filename": "test.jpg",
            "original_filename": "test.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg",
            "created_at": now,
            "updated_at": now
        }
        
        image_response = ImageResponse(**image_data)
        json_str = image_response.model_dump_json()
        
        assert isinstance(json_str, str)
        # Should contain the datetime in some format
        assert str(now.year) in json_str


class TestModelSchemaIntegration:
    """Test integration between models and schemas"""
    
    def test_model_to_schema_conversion(self, setup_test_db):
        """Test converting model instance to schema"""
        from datetime import datetime
        now = datetime.utcnow()
        
        # Create model instance with all required fields
        image_model = Image(
            id=1,
            filename="test.jpg",
            original_filename="original.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            poetry_content="테스트 시",
            poetry_generated=True,
            created_at=now,
            updated_at=now
        )
        
        # Convert to schema
        image_schema = ImageResponse.model_validate(image_model)
        
        assert image_schema.id == image_model.id
        assert image_schema.filename == image_model.filename
        assert image_schema.original_filename == image_model.original_filename
        assert image_schema.file_path == image_model.file_path
        assert image_schema.poetry_content == image_model.poetry_content
        assert image_schema.file_size == image_model.file_size
        assert image_schema.mime_type == image_model.mime_type
        assert image_schema.poetry_generated == image_model.poetry_generated
        assert image_schema.created_at == image_model.created_at
    
    def test_schema_to_model_conversion(self, setup_test_db):
        """Test converting schema to model instance"""
        # Create schema instance
        image_create = ImageCreate(
            filename="test.jpg",
            original_filename="original.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024,
            mime_type="image/jpeg"
        )
        
        # Convert to model
        image_model = Image(**image_create.model_dump())
        
        assert image_model.filename == image_create.filename
        assert image_model.original_filename == image_create.original_filename
        assert image_model.file_path == image_create.file_path
        assert image_model.file_size == image_create.file_size
        assert image_model.mime_type == image_create.mime_type
    
    def test_model_validation_constraints(self, setup_test_db):
        """Test model validation and constraints"""
        # Test that required fields are enforced by SQLAlchemy
        # These tests would fail when trying to commit to database
        
        # Valid model should not raise exception
        try:
            image = Image(
                filename="test.jpg",
                original_filename="test.jpg",
                file_path="/uploads/test.jpg",
                file_size=1024,
                mime_type="image/jpeg"
            )
            # Should create successfully
            assert image.filename == "test.jpg"
        except Exception:
            pytest.fail("Valid image model creation should not raise exception")