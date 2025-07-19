"""
AWS S3 service for file upload and management
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, BinaryIO
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import UploadFile, HTTPException
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations"""
    
    def __init__(self):
        self.s3_client = None
        self.bucket_name = settings.S3_BUCKET_NAME
        
        if settings.USE_S3_STORAGE:
            if settings.USE_LOCALSTACK:
                # LocalStack configuration
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.LOCALSTACK_ENDPOINT,
                    aws_access_key_id='test',  # LocalStack accepts any credentials
                    aws_secret_access_key='test',
                    region_name='us-east-1'  # LocalStack default region
                )
                logger.info(f"Initialized S3 client with LocalStack endpoint: {settings.LOCALSTACK_ENDPOINT}")
            else:
                # Real AWS S3 configuration
                if not all([
                    settings.AWS_ACCESS_KEY_ID,
                    settings.AWS_SECRET_ACCESS_KEY,
                    settings.S3_BUCKET_NAME
                ]):
                    raise ValueError("AWS credentials and bucket name are required for S3 storage")
                
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_DEFAULT_REGION
                )
                logger.info(f"Initialized S3 client with real AWS in region: {settings.AWS_DEFAULT_REGION}")
    
    def is_available(self) -> bool:
        """Check if S3 service is available and configured"""
        return self.s3_client is not None and self.bucket_name is not None
    
    async def upload_file(
        self, 
        file: UploadFile, 
        file_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Upload file to S3
        
        Args:
            file: Upload file object
            file_key: Custom S3 key (optional)
            
        Returns:
            Tuple of (s3_key, s3_url)
            
        Raises:
            HTTPException: If upload fails
        """
        if not self.is_available():
            raise HTTPException(
                status_code=500,
                detail="S3 service is not configured"
            )
        
        try:
            # Generate unique file key if not provided
            if not file_key:
                file_extension = Path(file.filename or "").suffix
                file_key = f"images/{uuid.uuid4()}{file_extension}"
            
            # Get file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Upload to S3
            extra_args = {
                'ContentType': file.content_type or 'application/octet-stream',
                'Metadata': {
                    'original_filename': file.filename or 'unknown',
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                **extra_args
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_DEFAULT_REGION}.amazonaws.com/{file_key}"
            
            logger.info(f"Successfully uploaded file to S3: {file_key}")
            return file_key, s3_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload failed with ClientError: {error_code} - {str(e)}")
            
            if error_code == 'NoSuchBucket':
                raise HTTPException(
                    status_code=500,
                    detail=f"S3 bucket '{self.bucket_name}' does not exist"
                )
            elif error_code == 'AccessDenied':
                raise HTTPException(
                    status_code=500,
                    detail="Access denied to S3 bucket"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"S3 upload failed: {str(e)}"
                )
        
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to S3: {str(e)}"
            )
    
    async def upload_local_file(self, local_path: str, s3_key: str) -> str:
        """
        Upload local file to S3
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key
            
        Returns:
            S3 URL
        """
        if not self.is_available():
            raise HTTPException(
                status_code=500,
                detail="S3 service is not configured"
            )
        
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Local file not found: {local_path}"
                )
            
            # Determine content type based on file extension
            content_type = self._get_content_type(local_file.suffix)
            
            extra_args = {
                'ContentType': content_type,
                'Metadata': {
                    'original_path': str(local_file),
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            await asyncio.to_thread(
                self.s3_client.upload_file,
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded local file to S3: {s3_key}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 local file upload failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload local file to S3: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during local file upload: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload local file: {str(e)}"
            )
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete S3 file {s3_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {str(e)}")
            return False
    
    async def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            url = await asyncio.to_thread(
                self.s3_client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            return None
    
    async def check_file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists
        """
        if not self.is_available():
            return False
        
        try:
            await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking S3 file existence {s3_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {str(e)}")
            return False
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.svg': 'image/svg+xml'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    async def get_bucket_info(self) -> dict:
        """
        Get S3 bucket information
        
        Returns:
            Bucket information dictionary
        """
        if not self.is_available():
            return {"error": "S3 service not configured"}
        
        try:
            # Get bucket location
            location = await asyncio.to_thread(
                self.s3_client.get_bucket_location,
                Bucket=self.bucket_name
            )
            
            # List objects to get count and total size
            total_objects = 0
            total_size = 0
            
            try:
                # Use list_objects_v2 directly for simplicity
                response = await asyncio.to_thread(
                    self.s3_client.list_objects_v2,
                    Bucket=self.bucket_name
                )
                
                if 'Contents' in response:
                    total_objects = len(response['Contents'])
                    total_size = sum(obj['Size'] for obj in response['Contents'])
            except Exception as list_error:
                logger.warning(f"Could not list bucket contents: {str(list_error)}")
                # Continue without object count
            
            return {
                "bucket_name": self.bucket_name,
                "region": location.get('LocationConstraint') or 'us-east-1',
                "total_objects": total_objects,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get bucket info: {str(e)}")
            return {"error": str(e)}