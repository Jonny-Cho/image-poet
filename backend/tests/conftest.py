"""
Test configuration and fixtures
"""
import asyncio
import os
import pytest
import pytest_asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Set up test database for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    from httpx import ASGITransport
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def temp_uploads_dir() -> Generator[Path, None, None]:
    """Create temporary uploads directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        uploads_dir = Path(temp_dir) / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        yield uploads_dir


@pytest.fixture
def sample_image_file() -> Generator[Path, None, None]:
    """Create a sample image file for testing"""
    import io
    from PIL import Image
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        img.save(temp_file, format='JPEG')
        temp_file_path = Path(temp_file.name)
    
    yield temp_file_path
    
    # Cleanup
    if temp_file_path.exists():
        temp_file_path.unlink()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes for testing"""
    import io
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='blue')
    byte_io = io.BytesIO()
    img.save(byte_io, format='JPEG')
    return byte_io.getvalue()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": "테스트 시입니다.\n\n붉은 장미가 피어나고\n새벽 이슬이 맺혀서\n아름다운 순간을 담고 있네"
                }
            }
        ]
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Store original values
    original_env = {}
    test_env_vars = {
        'ENVIRONMENT': 'test',
        'DEBUG': 'true',
        'DATABASE_URL': SQLALCHEMY_DATABASE_URL,
        'SECRET_KEY': 'test-secret-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'USE_S3_STORAGE': 'false',  # Use local storage for tests
        'USE_LOCALSTACK': 'false'
    }
    
    # Set test environment variables
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value