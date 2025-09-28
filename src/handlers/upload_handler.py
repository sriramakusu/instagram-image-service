"""
Lambda handler for image upload
"""
import json
import base64
import uuid
from typing import Dict, Any
from src.models.image import ImageModel
from src.services.s3_service import S3Service
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle image upload requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract required fields
        user_id = body.get('user_id')
        filename = body.get('filename')
        image_data_base64 = body.get('image_data')
        tags = body.get('tags', [])
        description = body.get('description', '')
        
        # Validate required fields
        if not all([user_id, filename, image_data_base64]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: user_id, filename, image_data'
                })
            }
        
        # Decode image data
        try:
            image_data = base64.b64decode(image_data_base64)
        except Exception as e:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid base64 image data'
                })
            }
        
        # Generate S3 key
        file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
        s3_key = f"images/{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Initialize services
        s3_service = S3Service(
            bucket_name='instagram-images',
            s3_endpoint='http://localhost:4566'
        )
        image_model = ImageModel(dynamodb_endpoint='http://localhost:4566')
        
        # Create bucket if it doesn't exist
        s3_service.create_bucket()
        
        # Upload image to S3
        content_type = f"image/{file_extension}"
        if not s3_service.upload_image(image_data, s3_key, content_type):
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to upload image to S3'
                })
            }
        
        # Save metadata to DynamoDB
        image_metadata = image_model.save_image(
            user_id=user_id,
            filename=filename,
            s3_key=s3_key,
            tags=tags,
            description=description
        )
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Image uploaded successfully',
                'image_id': image_metadata['image_id'],
                'upload_date': image_metadata['upload_date']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in upload handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }