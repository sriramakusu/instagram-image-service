"""
S3 OPERATIONS: S3 service for image storage operations
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self, bucket_name: str, s3_endpoint: str = None):
        self.bucket_name = bucket_name
        if s3_endpoint:
            self.s3_client = boto3.client('s3', endpoint_url=s3_endpoint)
        else:
            self.s3_client = boto3.client('s3')
    
    def create_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            logger.info(f"Created bucket: {self.bucket_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'BucketAlreadyExists':
                logger.error(f"Error creating bucket: {e}")
                raise e
    
    def upload_image(self, image_data: bytes, s3_key: str, content_type: str = 'image/jpeg') -> bool:
        """Upload image to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType=content_type
            )
            return True
        except ClientError as e:
            logger.error(f"Error uploading image: {e}")
            return False
    
    def get_image(self, s3_key: str) -> Optional[bytes]:
        """Get image data from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error getting image: {e}")
            return None
    
    def delete_image(self, s3_key: str) -> bool:
        """Delete image from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"Error deleting image: {e}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for image download"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None