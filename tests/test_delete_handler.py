"""
Unit tests for delete handler
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.handlers.delete_handler import lambda_handler


class TestDeleteHandler:
    
    @patch('src.handlers.delete_handler.S3Service')
    @patch('src.handlers.delete_handler.ImageModel')
    def test_successful_delete(self, mock_image_model, mock_s3_service):
        """Test successful image deletion"""
        # Mock services
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.get_image.return_value = {
            'image_id': 'test-image-id',
            's3_key': 'images/test-user/test.jpg'
        }
        mock_image_instance.delete_image.return_value = True
        
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.delete_image.return_value = True
        
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
        assert body['message'] == 'Image deleted successfully'
        assert body['image_id'] == 'test-image-id'
        
        # Verify service calls
        mock_image_instance.get_image.assert_called_once_with('test-image-id')
        mock_s3_instance.delete_image.assert_called_once()
        mock_image_instance.delete_image.assert_called_once_with('test-image-id')
    
    def test_missing_image_id(self):
        """Test delete with missing image ID"""
        event = {
            'pathParameters': {}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id parameter' in body['error']
    
    @patch('src.handlers.delete_handler.ImageModel')
    def test_image_not_found(self, mock_image_model):
        """Test delete with non-existent image"""
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
    
    @patch('src.handlers.delete_handler.S3Service')
    @patch('src.handlers.delete_handler.ImageModel')
    def test_partial_delete_failure(self, mock_image_model, mock_s3_service):
        """Test partial deletion failure"""
        # Mock services
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.get_image.return_value = {
            'image_id': 'test-image-id',
            's3_key': 'images/test-user/test.jpg'
        }
        mock_image_instance.delete_image.return_value = True
        
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.delete_image.return_value = False  # S3 deletion fails
        
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
        assert 'Failed to delete image completely' in body['error']
        assert body['s3_deleted'] == False
        assert body['db_deleted'] == True