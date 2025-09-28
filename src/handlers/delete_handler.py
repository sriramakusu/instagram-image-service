"""
Lambda handler for deleting images
"""
import json
from typing import Dict, Any
from src.models.image import ImageModel
from src.services.s3_service import S3Service
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle image deletion requests"""
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
        
        # Get image metadata first
        image_metadata = image_model.get_image(image_id)
        if not image_metadata:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Image not found'
                })
            }
        
        # Delete from S3
        s3_deleted = s3_service.delete_image(image_metadata['s3_key'])
        
        # Delete from DynamoDB
        db_deleted = image_model.delete_image(image_id)
        
        if not (s3_deleted and db_deleted):
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to delete image completely',
                    's3_deleted': s3_deleted,
                    'db_deleted': db_deleted
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image deleted successfully',
                'image_id': image_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error in delete handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }