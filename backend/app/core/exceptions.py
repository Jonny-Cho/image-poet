"""
Custom exception handlers for the Image Poet API
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class ImagePoetException(Exception):
    """Base exception for Image Poet application"""
    
    def __init__(self, message: str, code: str = "GENERAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ImageUploadError(ImagePoetException):
    """Exception for image upload errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "IMAGE_UPLOAD_ERROR")


class PoetryGenerationError(ImagePoetException):
    """Exception for poetry generation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "POETRY_GENERATION_ERROR")


class DatabaseError(ImagePoetException):
    """Exception for database errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unhandled exceptions
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "details": None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP exception handler for FastAPI HTTPExceptions
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {"status_code": exc.status_code}
        }
    )


async def image_poet_exception_handler(request: Request, exc: ImagePoetException):
    """
    Custom exception handler for ImagePoetException
    
    Args:
        request: FastAPI request object
        exc: ImagePoetException instance
        
    Returns:
        JSON error response
    """
    status_code = 400
    
    # Determine status code based on exception type
    if isinstance(exc, ImageUploadError):
        status_code = 400
    elif isinstance(exc, PoetryGenerationError):
        status_code = 500
    elif isinstance(exc, DatabaseError):
        status_code = 500
    
    logger.error(f"{exc.__class__.__name__}: {exc.message}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.code,
            "message": exc.message,
            "details": None
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    SQLAlchemy exception handler
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemyError instance
        
    Returns:
        JSON error response
    """
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "DATABASE_ERROR",
            "message": "Database operation failed",
            "details": None
        }
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """
    Pydantic validation exception handler
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": str(exc) if hasattr(exc, 'errors') else None
        }
    )