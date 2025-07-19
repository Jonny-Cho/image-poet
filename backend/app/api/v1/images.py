"""
Image API endpoints
"""
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.image_service import ImageService
from app.services.poetry_service import PoetryService
from app.schemas.image import (
    ImageResponse, 
    UploadResponse, 
    PoetryGenerationRequest,
    ErrorResponse
)

router = APIRouter()
image_service = ImageService()

# Initialize poetry service only when needed to avoid API key requirement at startup
def get_poetry_service():
    return PoetryService()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    auto_generate_poetry: bool = True,
    style: str = "classic",
    language: str = "korean",
    db: Session = Depends(get_db)
):
    """
    Upload image and optionally generate poetry
    
    Args:
        background_tasks: FastAPI background tasks
        request: FastAPI request object
        file: Uploaded image file
        auto_generate_poetry: Whether to automatically generate poetry
        style: Poetry style (classic, modern, haiku, free_verse)
        language: Poetry language (korean, english, japanese)
        db: Database session
        
    Returns:
        Upload response with image info and optional poetry
    """
    try:
        # Get client info
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Save uploaded file
        db_image = await image_service.save_uploaded_file(
            file=file,
            db=db,
            upload_ip=client_ip,
            user_agent=user_agent
        )
        
        response_data = {
            "success": True,
            "message": "Image uploaded successfully",
            "image_id": db_image.id,
            "image_url": f"/api/v1/images/{db_image.id}/file",
            "created_at": db_image.created_at,
            "metadata": {
                "filename": db_image.filename,
                "original_filename": db_image.original_filename,
                "file_size": db_image.file_size,
                "width": db_image.width,
                "height": db_image.height,
                "mime_type": db_image.mime_type
            }
        }
        
        # Generate poetry in background if requested
        if auto_generate_poetry:
            background_tasks.add_task(
                generate_poetry_background,
                db_image.id,
                style,
                language
            )
            response_data["message"] += ". Poetry generation started in background."
        
        return UploadResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )


async def generate_poetry_background(image_id: int, style: str, language: str):
    """
    Background task for poetry generation with retry logic
    
    Args:
        image_id: Image database ID
        style: Poetry style
        language: Poetry language
    """
    import asyncio
    
    try:
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Get image record
            db_image = image_service.get_image_by_id(db, image_id)
            if not db_image:
                return
            
            # Wait a bit for S3 upload to be fully propagated
            await asyncio.sleep(2)
            
            # Retry logic for S3 file availability
            max_retries = 3
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Generate poetry
                    poetry_service = get_poetry_service()
                    title, content = await poetry_service.generate_poetry_from_image(
                        image_path=db_image.file_path,
                        style=style,
                        language=language
                    )
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Poetry generation attempt {attempt + 1} failed: {str(e)}")
                        print(f"Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Final attempt failed
                        raise e
            
            # Update database
            image_service.update_image_poetry(
                db=db,
                image_id=image_id,
                poetry_title=title,
                poetry_content=content
            )
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Background poetry generation failed for image {image_id}: {str(e)}")


@router.post("/generate-poetry", response_model=UploadResponse)
async def generate_poetry(
    request: PoetryGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate poetry for existing image
    
    Args:
        request: Poetry generation request
        db: Database session
        
    Returns:
        Updated response with generated poetry
    """
    try:
        # Get image record
        db_image = image_service.get_image_by_id(db, request.image_id)
        if not db_image:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )
        
        # Generate poetry
        poetry_service = get_poetry_service()
        title, content = await poetry_service.generate_poetry_from_image(
            image_path=db_image.file_path,
            style=request.style,
            language=request.language
        )
        
        # Update database
        updated_image = image_service.update_image_poetry(
            db=db,
            image_id=request.image_id,
            poetry_title=title,
            poetry_content=content
        )
        
        if not updated_image:
            raise HTTPException(
                status_code=500,
                detail="Failed to update image with poetry"
            )
        
        return UploadResponse(
            success=True,
            message="Poetry generated successfully",
            image_id=updated_image.id,
            poetry=content,
            title=title,
            created_at=updated_image.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate poetry: {str(e)}"
        )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get image by ID
    
    Args:
        image_id: Image ID
        db: Database session
        
    Returns:
        Image record with poetry if available
    """
    db_image = image_service.get_image_by_id(db, image_id)
    if not db_image:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )
    
    return ImageResponse.model_validate(db_image)


@router.get("/{image_id}/file")
async def get_image_file(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get image file by ID
    
    Args:
        image_id: Image ID
        db: Database session
        
    Returns:
        Image file response
    """
    from fastapi.responses import FileResponse
    import os
    
    db_image = image_service.get_image_by_id(db, image_id)
    if not db_image:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )
    
    if not os.path.exists(db_image.file_path):
        raise HTTPException(
            status_code=404,
            detail="Image file not found on disk"
        )
    
    return FileResponse(
        path=db_image.file_path,
        media_type=db_image.mime_type,
        filename=db_image.original_filename
    )


@router.get("/", response_model=List[ImageResponse])
async def list_images(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List images with pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of image records
    """
    if limit > 100:
        limit = 100  # Prevent excessive loads
    
    images = image_service.get_images_list(db, skip=skip, limit=limit)
    return [ImageResponse.model_validate(image) for image in images]


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete image by ID
    
    Args:
        image_id: Image ID
        db: Database session
        
    Returns:
        Success response
    """
    success = image_service.delete_image(db, image_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )
    
    return {"success": True, "message": "Image deleted successfully"}


@router.get("/{image_id}/status")
async def get_poetry_status(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get poetry generation status for image
    
    Args:
        image_id: Image ID
        db: Database session
        
    Returns:
        Poetry status information
    """
    db_image = image_service.get_image_by_id(db, image_id)
    if not db_image:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )
    
    return {
        "image_id": image_id,
        "poetry_generated": db_image.poetry_generated,
        "has_poetry": bool(db_image.poetry_content),
        "poetry_title": db_image.poetry_title,
        "updated_at": db_image.updated_at
    }