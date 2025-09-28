"""
Unit tests for upload handler
"""
import pytest
import json
import base64
from unittest.mock import patch, MagicMock
from src.handlers.upload_handler import lambda_handler


class TestUploadHandler:
    
    @patch('src.handlers.upload_handler.S3Service')
    @patch('src.handlers.upload_handler.ImageModel')
    def test_successful_upload(self, mock_image_model, mock_s3_service):
        """Test successful image upload"""
        # Mock services
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.upload_image.return_value = True
        
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.save_image.return_value = {
            'image_id': 'test-image-id',
            'upload_date': '2024-01-01T00:00:00'
        }
        
        # Prepare test data
        test_image_data = b"fake image data"
        event = {
            'body': json.dumps({
                'user_id': 'test-user',
                'filename': 'test.jpg',
                'image_data': base64.b64encode(test_image_data).decode('utf-8'),
                'tags': ['nature', 'landscape'],
                'description': 'Test image'
            })
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Image uploaded successfully'
        assert body['image_id'] == 'test-image-id'
        
        # Verify service calls
        mock_s3_instance.create_bucket.assert_called_once()
        mock_s3_instance.upload_image.assert_called_once()
        mock_image_instance.save_image.assert_called_once()
    
    def test_missing_required_fields(self):
        """Test upload with missing required fields"""
        event = {
            'body': json.dumps({
                'user_id': 'test-user'
                # Missing filename and image_data
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required fields' in body['error']
    
    def test_invalid_base64_data(self):
        """Test upload with invalid base64 data"""
        event = {
            'body': json.dumps({
                'user_id': 'test-user',
                'filename': 'test.jpg',
                'image_data': 'invalid-base64-data'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid base64 image data' in body['error']
    
    @patch('src.handlers.upload_handler.S3Service')
    @patch('src.handlers.upload_handler.ImageModel')
    def test_s3_upload_failure(self, mock_image_model, mock_s3_service):
        """Test S3 upload failure"""
        # Mock services
        mock_s3_instance = MagicMock()
        mock_s3_service.return_value = mock_s3_instance
        mock_s3_instance.upload_image.return_value = False
        
        # Prepare test data
        test_image_data = b"fake image data"
        event = {
            'body': json.dumps({
                'user_id': 'test-user',
                'filename': 'test.jpg',
                'image_data': base64.b64encode(test_image_data).decode('utf-8')
            })
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to upload image to S3' in body['error']