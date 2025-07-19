"""
Storage management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.s3_service import S3Service
from app.core.config import settings
from app.core.storage_monitor import get_storage_info, get_uploads_size

router = APIRouter()


@router.get("/status")
async def get_storage_status(db: Session = Depends(get_db)):
    """
    Get comprehensive storage status
    
    Returns:
        Storage status information
    """
    # Local storage info
    local_storage = get_storage_info()
    local_uploads = get_uploads_size()
    
    # S3 storage info
    s3_service = S3Service()
    s3_info = {
        "configured": s3_service.is_available(),
        "enabled": settings.USE_S3_STORAGE,
        "bucket_name": settings.S3_BUCKET_NAME,
        "region": settings.AWS_DEFAULT_REGION
    }
    
    if s3_service.is_available():
        try:
            bucket_info = await s3_service.get_bucket_info()
            s3_info.update(bucket_info)
        except Exception as e:
            s3_info["error"] = str(e)
    
    return {
        "storage_mode": "s3" if settings.USE_S3_STORAGE and s3_service.is_available() else "local",
        "local": {
            "disk": local_storage,
            "uploads": local_uploads
        },
        "s3": s3_info
    }


@router.get("/s3/test")
async def test_s3_connection():
    """
    Test S3 connection and configuration
    
    Returns:
        S3 connection test results
    """
    s3_service = S3Service()
    
    if not s3_service.is_available():
        raise HTTPException(
            status_code=400,
            detail="S3 service is not configured. Check AWS credentials and bucket name."
        )
    
    try:
        bucket_info = await s3_service.get_bucket_info()
        return {
            "status": "connected",
            "message": "S3 connection successful",
            "bucket_info": bucket_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"S3 connection failed: {str(e)}"
        )


@router.post("/migrate-to-s3")
async def migrate_local_to_s3(db: Session = Depends(get_db)):
    """
    Migrate existing local files to S3
    
    Returns:
        Migration results
    """
    if not settings.USE_S3_STORAGE:
        raise HTTPException(
            status_code=400,
            detail="S3 storage is not enabled. Set USE_S3_STORAGE=true"
        )
    
    s3_service = S3Service()
    if not s3_service.is_available():
        raise HTTPException(
            status_code=400,
            detail="S3 service is not configured properly"
        )
    
    # This would be implemented to migrate existing files
    # For now, return a placeholder response
    return {
        "status": "not_implemented",
        "message": "Migration feature will be implemented in next version",
        "recommendation": "For now, new uploads will use S3 automatically"
    }


@router.get("/config")
async def get_storage_config():
    """
    Get current storage configuration
    
    Returns:
        Storage configuration details
    """
    return {
        "use_s3_storage": settings.USE_S3_STORAGE,
        "s3_configured": bool(settings.AWS_ACCESS_KEY_ID and 
                           settings.AWS_SECRET_ACCESS_KEY and 
                           settings.S3_BUCKET_NAME),
        "s3_region": settings.AWS_DEFAULT_REGION,
        "s3_bucket": settings.S3_BUCKET_NAME,
        "environment": settings.ENVIRONMENT
    }