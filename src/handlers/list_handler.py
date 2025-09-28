"""
Lambda handler for listing images
"""
import json
from typing import Dict, Any
from src.models.image import ImageModel
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle image list requests"""
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        
        user_id = query_params.get('user_id')
        tag_filter = query_params.get('tag')
        date_from = query_params.get('date_from')
        date_to = query_params.get('date_to')
        limit = int(query_params.get('limit', 50))
        
        # Initialize service
        image_model = ImageModel(dynamodb_endpoint='http://localhost:4566')
        
        # List images with filters
        images = image_model.list_images(
            user_id=user_id,
            tag_filter=tag_filter,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        # Format response
        formatted_images = []
        for image in images:
            formatted_images.append({
                'image_id': image['image_id'],
                'user_id': image['user_id'],
                'filename': image['filename'],
                'upload_date': image['upload_date'],
                'tags': image['tags'],
                'description': image['description']
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'images': formatted_images,
                'count': len(formatted_images)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in list handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }