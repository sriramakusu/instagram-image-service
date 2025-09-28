"""
Unit tests for view handler
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.handlers.view_handler import lambda_handler


class TestViewHandler:
    
    @patch('src.handlers.view_handler.S3Service')
    @patch('src.handlers.view_handler.ImageModel')
    def test_successful_view_image(self, mock_image_model, mock_s3_service):
        """Test successful image view"""
        # Mock services
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.get_image.return_value = {
            'image_id': 'test-image-id',
            'user_id': 'test-user',
            'filename': 'test.jpg',
            'upload_date': '2024-01-01T00:00:00',
            'tags': ['nature'],
            'description': 'Test image',
            's3_key': 'images/test-user/test.jpg'
        }
        
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.generate_presigned_url.return_value = 'https://test-url.com'
        
        # Prepare event
        event = {
            'pathParameters': {
                'image_id': 'test-image-id'
            }
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['image_id'] == 'test-image-id'
        assert body['download_url'] == 'https://test-url.com'
        
        # Verify service calls
        mock_image_instance.get_image.assert_called_once_with('test-image-id')
        mock_s3_instance.generate_presigned_url.assert_called_once()
    
    def test_missing_image_id(self):
        """Test view with missing image ID"""
        event = {
            'pathParameters': {}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id parameter' in body['error']
    
    @patch('src.handlers.view_handler.ImageModel')
    def test_image_not_found(self, mock_image_model):
        """Test view with non-existent image"""
        # Mock service
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.get_image.return_value = None
        
        # Prepare event
        event = {
            'pathParameters': {
                'image_id': 'non-existent-id'
            }
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Image not found' in body['error']
    
    @patch('src.handlers.view_handler.S3Service')
    @patch('src.handlers.view_handler.ImageModel')
    def test_presigned_url_generation_failure(self, mock_image_model, mock_s3_service):
        """Test presigned URL generation failure"""
        # Mock services
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.get_image.return_value = {
            'image_id': 'test-image-id',
            's3_key': 'images/test-user/test.jpg'
        }
        
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.generate_presigned_url.return_value = None
        
        # Prepare event
        event = {
            'pathParameters': {
                'image_id': 'test-image-id'
            }
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to generate download URL' in body['error']