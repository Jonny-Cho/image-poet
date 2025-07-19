"""
Test configuration and settings
"""
import os
import pytest
from unittest.mock import patch

from app.core.config import Settings, settings


class TestSettings:
    """Test application settings and configuration"""
    
    def test_default_settings(self):
        """Test settings with code defaults (environment independent)"""
        # Clear environment and disable .env file loading
        with patch.dict(os.environ, {}, clear=True):
            # Create Settings without env_file to test pure code defaults
            class TestSettings(Settings):
                class Config:
                    env_file = None  # Disable .env file loading
                    case_sensitive = True
            
            test_settings = TestSettings()
        
            assert test_settings.APP_NAME == "Image Poet API"
            assert test_settings.VERSION == "0.1.0"
            assert test_settings.DEBUG is False  # Code default
            assert test_settings.ENVIRONMENT == "development"  # Code default
            assert test_settings.ALGORITHM == "HS256"
            assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
            assert test_settings.AWS_DEFAULT_REGION == "ap-northeast-2"  # Code default
            assert test_settings.USE_S3_STORAGE is False  # Code default
            assert test_settings.USE_LOCALSTACK is False  # Code default
            assert test_settings.LOCALSTACK_ENDPOINT == "http://localhost:4566"
    
    def test_settings_from_environment(self):
        """Test settings loaded from environment variables"""
        env_vars = {
            'APP_NAME': 'Test App',
            'DEBUG': 'true',
            'ENVIRONMENT': 'test',
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'sqlite:///test.db',
            'OPENAI_API_KEY': 'test-openai-key',
            'USE_S3_STORAGE': 'true',
            'USE_LOCALSTACK': 'true',
            'S3_BUCKET_NAME': 'test-bucket'
        }
        
        with patch.dict(os.environ, env_vars):
            test_settings = Settings()
            
            assert test_settings.APP_NAME == 'Test App'
            assert test_settings.DEBUG is True
            assert test_settings.ENVIRONMENT == 'test'
            assert test_settings.SECRET_KEY == 'test-secret'
            assert test_settings.DATABASE_URL == 'sqlite:///test.db'
            assert test_settings.OPENAI_API_KEY == 'test-openai-key'
            assert test_settings.USE_S3_STORAGE is True
            assert test_settings.USE_LOCALSTACK is True
            assert test_settings.S3_BUCKET_NAME == 'test-bucket'
    
    def test_cors_origins_validation(self):
        """Test CORS origins validation"""
        # Test with string
        with patch.dict(os.environ, {'BACKEND_CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'}, clear=True):
            test_settings = Settings()
            assert len(test_settings.BACKEND_CORS_ORIGINS) == 2
            assert 'http://localhost:3000' in test_settings.BACKEND_CORS_ORIGINS
            assert 'http://localhost:8080' in test_settings.BACKEND_CORS_ORIGINS
        
        # Test with defaults (clear any existing environment variables)
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith('BACKEND_CORS_ORIGINS')}
        with patch.dict(os.environ, clean_env, clear=True):
            test_settings = Settings()
            assert test_settings.BACKEND_CORS_ORIGINS == ['http://localhost:3000']
    
    def test_database_url_validation(self):
        """Test database URL validation"""
        # Test development environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            # Create Settings without env_file to test pure code defaults
            class TestSettings(Settings):
                class Config:
                    env_file = None  # Disable .env file loading
                    case_sensitive = True
            
            test_settings = TestSettings()
            assert test_settings.DATABASE_URL == "sqlite:///./image_poet.db"
        
        # Test production environment without DATABASE_URL
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}, clear=True):
            # Create Settings without env_file to test pure code defaults
            class TestSettings(Settings):
                class Config:
                    env_file = None  # Disable .env file loading
                    case_sensitive = True
            
            with pytest.raises(ValueError, match="DATABASE_URL must be set in production"):
                TestSettings()
        
        # Test production environment with DATABASE_URL
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }, clear=True):
            test_settings = Settings()
            assert test_settings.DATABASE_URL == 'postgresql://user:pass@localhost/db'
    
    def test_secret_key_validation(self):
        """Test secret key validation"""
        # Test development environment with code defaults
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            # Create Settings without env_file to test pure code defaults
            class TestSettings(Settings):
                class Config:
                    env_file = None  # Disable .env file loading
                    case_sensitive = True
            
            test_settings = TestSettings()
            assert test_settings.SECRET_KEY == "development-secret-key"  # Code default
        
        # Test production environment without SECRET_KEY (override .env)
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'SECRET_KEY': ''}, clear=True):
            with pytest.raises(ValueError, match="SECRET_KEY must be set in production"):
                Settings()
        
        # Test production environment with SECRET_KEY
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'super-secret-production-key'
        }, clear=True):
            test_settings = Settings()
            assert test_settings.SECRET_KEY == 'super-secret-production-key'
    
    def test_environment_properties(self):
        """Test environment helper properties"""
        # Test development
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            test_settings = Settings()
            assert test_settings.is_development is True
            assert test_settings.is_production is False
        
        # Test production
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://test',
            'SECRET_KEY': 'production-secret'
        }, clear=True):
            test_settings = Settings()
            assert test_settings.is_development is False
            assert test_settings.is_production is True
    
    def test_get_cors_origins(self):
        """Test CORS origins getter method"""
        # Test development environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            test_settings = Settings()
            cors_origins = test_settings.get_cors_origins()
            assert cors_origins == ["*"]
        
        # Test production environment
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://test',
            'SECRET_KEY': 'production-secret',
            'BACKEND_CORS_ORIGINS': 'https://myapp.com,https://api.myapp.com'
        }, clear=True):
            test_settings = Settings()
            cors_origins = test_settings.get_cors_origins()
            assert 'https://myapp.com' in cors_origins
            assert 'https://api.myapp.com' in cors_origins
    
    def test_aws_s3_settings(self):
        """Test AWS S3 related settings"""
        aws_env = {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
            'AWS_DEFAULT_REGION': 'us-west-2',
            'S3_BUCKET_NAME': 'my-test-bucket',
            'USE_S3_STORAGE': 'true'
        }
        
        with patch.dict(os.environ, aws_env):
            test_settings = Settings()
            
            assert test_settings.AWS_ACCESS_KEY_ID == 'test-access-key'
            assert test_settings.AWS_SECRET_ACCESS_KEY == 'test-secret-key'
            assert test_settings.AWS_DEFAULT_REGION == 'us-west-2'
            assert test_settings.S3_BUCKET_NAME == 'my-test-bucket'
            assert test_settings.USE_S3_STORAGE is True
    
    def test_localstack_settings(self):
        """Test LocalStack related settings"""
        localstack_env = {
            'USE_LOCALSTACK': 'true',
            'LOCALSTACK_ENDPOINT': 'http://localstack:4566',
            'S3_BUCKET_NAME': 'localstack-bucket'
        }
        
        with patch.dict(os.environ, localstack_env):
            test_settings = Settings()
            
            assert test_settings.USE_LOCALSTACK is True
            assert test_settings.LOCALSTACK_ENDPOINT == 'http://localstack:4566'
            assert test_settings.S3_BUCKET_NAME == 'localstack-bucket'
    
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing"""
        bool_vars = {
            'DEBUG': 'true',
            'DATABASE_ECHO': 'false',
            'USE_S3_STORAGE': '1',
            'USE_LOCALSTACK': '0'
        }
        
        with patch.dict(os.environ, bool_vars):
            test_settings = Settings()
            
            assert test_settings.DEBUG is True
            assert test_settings.DATABASE_ECHO is False
            assert test_settings.USE_S3_STORAGE is True
            assert test_settings.USE_LOCALSTACK is False
    
    def test_integer_environment_variables(self):
        """Test integer environment variable parsing"""
        int_vars = {
            'ACCESS_TOKEN_EXPIRE_MINUTES': '60'
        }
        
        with patch.dict(os.environ, int_vars):
            test_settings = Settings()
            
            assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
            assert isinstance(test_settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
    
    def test_settings_case_sensitivity(self):
        """Test that settings are case sensitive"""
        # The Config class has case_sensitive = True
        test_settings = Settings()
        
        # This should work (correct case)
        assert hasattr(test_settings, 'APP_NAME')
        
        # This should not exist (wrong case)
        assert not hasattr(test_settings, 'app_name')


class TestGlobalSettings:
    """Test the global settings instance"""
    
    def test_global_settings_instance(self):
        """Test that global settings instance is properly configured"""
        assert settings is not None
        assert isinstance(settings, Settings)
        assert settings.APP_NAME == "Image Poet API"
    
    def test_settings_singleton_behavior(self):
        """Test that settings behave consistently"""
        # Import settings in different ways
        from app.core.config import settings as settings1
        from app.core.config import Settings
        
        # Create new instance
        settings2 = Settings()
        
        # Should have same configuration (though not necessarily same instance)
        assert settings1.APP_NAME == settings2.APP_NAME
        assert settings1.VERSION == settings2.VERSION