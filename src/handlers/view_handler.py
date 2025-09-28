"""
Lambda handler for viewing/downloading images
"""
import json
from typing import Dict, Any
from src.models.image import ImageModel
from src.services.s3_service import S3Service
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle image view/download requests"""
    try:
        # Extract image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id')
        
        if not image_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing image_id parameter'
                })
            }
        
        # Initialize services
        image_model = ImageModel(dynamodb_endpoint='http://localhost:4566')
        s3_service = S3Service(
            bucket_name='instagram-images',
            s3_endpoint='http://localhost:4566'
        )
        
        # Get image metadata
        image_metadata = image_model.get_image(image_id)
        if not image_metadata:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Image not found'
                })
            }
        
        # Generate presigned URL for download
        presigned_url = s3_service.generate_presigned_url(image_metadata['s3_key'])
        if not presigned_url:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to generate download URL'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'image_id': image_metadata['image_id'],
                'user_id': image_metadata['user_id'],
                'filename': image_metadata['filename'],
                'upload_date': image_metadata['upload_date'],
                'tags': image_metadata['tags'],
                'description': image_metadata['description'],
                'download_url': presigned_url
            })
        }
        
    except Exception as e:
        logger.error(f"Error in view handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }