"""
API v1 router configuration
"""
from fastapi import APIRouter

from app.api.v1.images import router as images_router
from app.api.v1.storage import router as storage_router

# Create API v1 router
router = APIRouter()

# Include sub-routers with prefixes
router.include_router(
    images_router,
    prefix="/images",
    tags=["images"]
)

router.include_router(
    storage_router,
    prefix="/storage",
    tags=["storage"]
)