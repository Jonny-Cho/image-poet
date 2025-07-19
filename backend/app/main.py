from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import os

from app.core.config import settings
from app.core.database import create_tables
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    image_poet_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
    ImagePoetException
)
from app.api.v1.router import router as api_v1_router

app = FastAPI(
    title=settings.APP_NAME,
    description="AI API for generating poetry from images",
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    api_v1_router,
    prefix="/api/v1"
)

# Create upload directory and mount static files
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/static", StaticFiles(directory=uploads_dir), name="static")

# Add exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ImagePoetException, image_poet_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    # Create database tables
    create_tables()
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION} started")
    print(f"📄 API Documentation: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("👋 Application shutting down...")


@app.get("/")
async def root():
    return {"message": "Image Poet API Server", "docs": "/docs"}

@app.get("/health")
async def health_check():
    from app.core.storage_monitor import get_storage_info, get_uploads_size
    
    storage_info = get_storage_info()
    uploads_info = get_uploads_size()
    
    return {
        "status": "healthy", 
        "app": settings.APP_NAME, 
        "version": settings.VERSION,
        "storage": storage_info,
        "uploads": uploads_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)