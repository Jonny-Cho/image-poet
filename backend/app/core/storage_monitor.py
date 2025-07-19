"""
Storage monitoring utilities
"""
import shutil
import os
from pathlib import Path


def get_storage_info(path: str = ".") -> dict:
    """
    Get storage information for given path
    
    Args:
        path: Directory path to check
        
    Returns:
        Storage information dictionary
    """
    try:
        total, used, free = shutil.disk_usage(path)
        
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2), 
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2),
            "status": "healthy" if free > 1_000_000_000 else "warning"  # 1GB threshold
        }
    except Exception as e:
        return {"error": str(e)}


def get_uploads_size(uploads_dir: str = "uploads") -> dict:
    """
    Get total size of uploads directory
    
    Args:
        uploads_dir: Uploads directory path
        
    Returns:
        Upload directory size information
    """
    try:
        uploads_path = Path(uploads_dir)
        if not uploads_path.exists():
            return {"total_mb": 0, "file_count": 0}
        
        total_size = 0
        file_count = 0
        
        for file_path in uploads_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_mb": round(total_size / (1024**2), 2),
            "total_gb": round(total_size / (1024**3), 2),
            "file_count": file_count,
            "avg_file_mb": round((total_size / file_count) / (1024**2), 2) if file_count > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}