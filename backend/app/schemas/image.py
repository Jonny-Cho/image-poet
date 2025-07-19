"""
Pydantic schemas for image API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ImageBase(BaseModel):
    """Base image schema"""
    filename: str = Field(..., description="Image filename")
    original_filename: str = Field(..., description="Original filename from upload")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the image")
    width: Optional[int] = Field(None, ge=1, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Image height in pixels")


class ImageCreate(ImageBase):
    """Schema for creating image"""
    file_path: str = Field(..., description="File path on server")
    upload_ip: Optional[str] = Field(None, description="Upload IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ImageUpdate(BaseModel):
    """Schema for updating image"""
    poetry_title: Optional[str] = Field(None, max_length=200, description="Poetry title")
    poetry_content: Optional[str] = Field(None, description="Generated poetry content")
    poetry_generated: Optional[bool] = Field(None, description="Poetry generation status")


class ImageResponse(ImageBase):
    """Schema for image response"""
    id: int = Field(..., description="Image ID")
    file_path: str = Field(..., description="File path on server")
    poetry_title: Optional[str] = Field(None, description="Poetry title")
    poetry_content: Optional[str] = Field(None, description="Generated poetry content")
    poetry_generated: bool = Field(False, description="Poetry generation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)


class UploadResponse(BaseModel):
    """Schema for upload response"""
    success: bool = Field(..., description="Upload success status")
    message: str = Field(..., description="Response message")
    image_id: Optional[int] = Field(None, description="Generated image ID")
    image_url: Optional[str] = Field(None, description="Image URL")
    poetry: Optional[str] = Field(None, description="Generated poetry")
    title: Optional[str] = Field(None, description="Poetry title")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class PoetryGenerationRequest(BaseModel):
    """Schema for poetry generation request"""
    image_id: int = Field(..., description="Image ID to generate poetry for")
    style: Optional[str] = Field("classic", description="Poetry style preference")
    language: Optional[str] = Field("korean", description="Poetry language")
    
    @field_validator("style")
    @classmethod
    def validate_style(cls, v):
        allowed_styles = ["classic", "modern", "haiku", "free_verse"]
        if v not in allowed_styles:
            raise ValueError(f"Style must be one of {allowed_styles}")
        return v
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        allowed_languages = ["korean", "english", "japanese"]
        if v not in allowed_languages:
            raise ValueError(f"Language must be one of {allowed_languages}")
        return v


class ErrorResponse(BaseModel):
    """Schema for error response"""
    success: bool = Field(False, description="Success status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")