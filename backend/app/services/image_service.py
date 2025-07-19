"""
Image upload and processing service
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image as PILImage
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.image import Image
from app.schemas.image import ImageCreate
from app.services.s3_service import S3Service
from app.core.config import settings


class ImageService:
    """Service for handling image upload and processing"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 
        'image/webp', 'image/gif'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR = Path("uploads")
    
    def __init__(self):
        # Ensure upload directory exists (for local storage fallback)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        
        # Initialize S3 service
        self.s3_service = S3Service()
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        db: Session,
        upload_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Image:
        """
        Save uploaded file and create database record
        
        Args:
            file: Uploaded file
            db: Database session
            upload_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            Image database record
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate file
        self._validate_file(file)
        
        # Generate unique filename
        file_extension = self._get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.UPLOAD_DIR / unique_filename
        
        s3_key = None
        s3_url = None
        
        try:
            # Choose storage method based on configuration
            if settings.USE_S3_STORAGE and self.s3_service.is_available():
                # Upload to S3
                s3_key, s3_url = await self.s3_service.upload_file(file, f"images/{unique_filename}")
                # Also save locally for image dimension analysis
                await self._save_file_to_disk(file, file_path)
                storage_path = s3_url
            else:
                # Save locally
                await self._save_file_to_disk(file, file_path)
                storage_path = str(file_path)
            
            # Get image dimensions
            width, height = self._get_image_dimensions(file_path)
            
            # Create database record
            image_data = ImageCreate(
                filename=unique_filename,
                original_filename=file.filename or "unknown",
                file_path=storage_path,
                file_size=file.size or 0,
                mime_type=file.content_type or "application/octet-stream",
                width=width,
                height=height,
                upload_ip=upload_ip,
                user_agent=user_agent
            )
            
            db_image = Image(**image_data.dict())
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            # Clean up local file if using S3 (keep only for dimension analysis)
            if settings.USE_S3_STORAGE and file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass  # Don't fail if cleanup fails
            
            return db_image
            
        except Exception as e:
            # Clean up files if database operation fails
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass
            
            # Clean up S3 file if it was uploaded
            if s3_key and self.s3_service.is_available():
                try:
                    await self.s3_service.delete_file(s3_key)
                except Exception:
                    pass
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save image: {str(e)}"
            )
    
    def _validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file size
        if file.size and file.size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Check file extension
        if file.filename:
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in self.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File extension {file_extension} not allowed. "
                           f"Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
        
        # Check MIME type
        if file.content_type and file.content_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"MIME type {file.content_type} not allowed. "
                       f"Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix
    
    async def _save_file_to_disk(self, file: UploadFile, file_path: Path) -> None:
        """
        Save uploaded file to disk
        
        Args:
            file: Uploaded file
            file_path: Destination path
        """
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file to disk: {str(e)}"
            )
        finally:
            file.file.close()
    
    def _get_image_dimensions(self, file_path: Path) -> Tuple[Optional[int], Optional[int]]:
        """
        Get image dimensions using PIL
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (width, height) or (None, None) if unable to read
        """
        try:
            with PILImage.open(file_path) as img:
                return img.width, img.height
        except Exception:
            return None, None
    
    def get_image_by_id(self, db: Session, image_id: int) -> Optional[Image]:
        """
        Get image by ID
        
        Args:
            db: Database session
            image_id: Image ID
            
        Returns:
            Image record or None
        """
        return db.query(Image).filter(Image.id == image_id).first()
    
    def update_image_poetry(
        self, 
        db: Session, 
        image_id: int, 
        poetry_title: str, 
        poetry_content: str
    ) -> Optional[Image]:
        """
        Update image with generated poetry
        
        Args:
            db: Database session
            image_id: Image ID
            poetry_title: Generated poetry title
            poetry_content: Generated poetry content
            
        Returns:
            Updated image record or None
        """
        db_image = self.get_image_by_id(db, image_id)
        if not db_image:
            return None
        
        db_image.poetry_title = poetry_title
        db_image.poetry_content = poetry_content
        db_image.poetry_generated = True
        db_image.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_image)
        
        return db_image
    
    def delete_image(self, db: Session, image_id: int) -> bool:
        """
        Delete image and its file
        
        Args:
            db: Database session
            image_id: Image ID
            
        Returns:
            True if deleted successfully
        """
        db_image = self.get_image_by_id(db, image_id)
        if not db_image:
            return False
        
        # Delete file from disk
        file_path = Path(db_image.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass  # Continue with database deletion even if file deletion fails
        
        # Delete from database
        db.delete(db_image)
        db.commit()
        
        return True
    
    def get_images_list(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 20
    ) -> list[Image]:
        """
        Get list of images with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of image records
        """
        return (
            db.query(Image)
            .order_by(Image.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )