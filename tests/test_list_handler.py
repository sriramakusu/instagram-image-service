"""
Unit tests for list handler
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.handlers.list_handler import lambda_handler


class TestListHandler:
    
    @patch('src.handlers.list_handler.ImageModel')
    def test_successful_list_all_images(self, mock_image_model):
        """Test successful listing of all images"""
        # Mock service
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.list_images.return_value = [
            {
                'image_id': 'img-1',
                'user_id': 'user-1',
                'filename': 'test1.jpg',
                'upload_date': '2024-01-01T00:00:00',
                'tags': ['nature'],
                'description': 'Test image 1'
            },
            {
                'image_id': 'img-2',
                'user_id': 'user-2',
                'filename': 'test2.jpg',
                'upload_date': '2024-01-02T00:00:00',
                'tags': ['city'],
                'description': 'Test image 2'
            }
        ]
        
        # Prepare event
        event = {
            'queryStringParameters': {}
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['images']) == 2
        assert body['images'][0]['image_id'] == 'img-1'
        
        # Verify service call
        mock_image_instance.list_images.assert_called_once_with(
            user_id=None,
            tag_filter=None,
            date_from=None,
            date_to=None,
            limit=50
        )
    
    @patch('src.handlers.list_handler.ImageModel')
    def test_list_with_user_filter(self, mock_image_model):
        """Test listing images with user filter"""
        # Mock service
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.list_images.return_value = [
            {
                'image_id': 'img-1',
                'user_id': 'user-1',
                'filename': 'test1.jpg',
                'upload_date': '2024-01-01T00:00:00',
                'tags': ['nature'],
                'description': 'Test image 1'
            }
        ]
        
        # Prepare event
        event = {
            'queryStringParameters': {
                'user_id': 'user-1'
            }
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert body['images'][0]['user_id'] == 'user-1'
        
        # Verify service call
        mock_image_instance.list_images.assert_called_once_with(
            user_id='user-1',
            tag_filter=None,
            date_from=None,
            date_to=None,
            limit=50
        )
    
    @patch('src.handlers.list_handler.ImageModel')
    def test_list_with_tag_and_date_filters(self, mock_image_model):
        """Test listing images with tag and date filters"""
        # Mock service
        mock_image_instance = MagicMock()
        mock_image_model.return_value = mock_image_instance
        mock_image_instance.list_images.return_value = []
        
        # Prepare event
        event = {
            'queryStringParameters': {
                'tag': 'nature',
                'date_from': '2024-01-01T00:00:00',
                'date_to': '2024-01-31T23:59:59',
                'limit': '10'
            }
        }
        
        # Execute handler
        response = lambda_handler(event, {})
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        
        # Verify service call
        mock_image_instance.list_images.assert_called_once_with(
            user_id=None,
            tag_filter='nature',
            date_from='2024-01-01T00:00:00',
            date_to='2024-01-31T23:59:59',
            limit=10
        )
    
    def test_list_with_no_query_params(self):
        """Test listing images with no query parameters"""
        event = {}
        
        response = lambda_handler(event, {})
        
        # Should still work with default parameters
        assert response['statusCode'] == 200