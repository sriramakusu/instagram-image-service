"""
Unit tests for Instagram Image Service Lambda handler
"""
import json
import pytest
import boto3
import os
from unittest.mock import patch, MagicMock
from src.lambda_handler import lambda_handler

# Mock AWS credentials
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'

class TestLambdaHandler:
    
    @patch('boto3.resource')
    def test_list_images_empty(self, mock_resource):
        """Test listing images when none exist"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.scan.return_value = {'Items': []}
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images',
            'queryStringParameters': None
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        assert body['images'] == []
        assert 'filters_applied' in body
    
    @patch('boto3.resource')
    def test_list_images_with_user_filter(self, mock_resource):
        """Test listing images filtered by user_id"""
        # Mock DynamoDB table with test data
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'image_id': 'test-1',
                    'user_id': 'user1',
                    'filename': 'test1.jpg',
                    'upload_date': '2024-01-01T00:00:00',
                    'tags': ['test'],
                    's3_key': 'images/user1/test-1.jpg',
                    'description': 'Test image 1'
                },
                {
                    'image_id': 'test-2',
                    'user_id': 'user2',
                    'filename': 'test2.jpg',
                    'upload_date': '2024-01-02T00:00:00',
                    'tags': ['demo'],
                    's3_key': 'images/user2/test-2.jpg',
                    'description': 'Test image 2'
                }
            ]
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images',
            'queryStringParameters': {'user_id': 'user1'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert body['images'][0]['user_id'] == 'user1'
        assert body['filters_applied']['user_id'] == 'user1'
        assert body['filters_applied']['tag'] is None
    
    @patch('boto3.resource')
    def test_list_images_with_tag_filter(self, mock_resource):
        """Test listing images filtered by tag"""
        # Mock DynamoDB table with test data
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'image_id': 'test-1',
                    'user_id': 'user1',
                    'filename': 'test1.jpg',
                    'upload_date': '2024-01-01T00:00:00',
                    'tags': ['test', 'demo'],
                    's3_key': 'images/user1/test-1.jpg',
                    'description': 'Test image 1'
                },
                {
                    'image_id': 'test-2',
                    'user_id': 'user2',
                    'filename': 'test2.jpg',
                    'upload_date': '2024-01-02T00:00:00',
                    'tags': ['production'],
                    's3_key': 'images/user2/test-2.jpg',
                    'description': 'Test image 2'
                }
            ]
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images',
            'queryStringParameters': {'tag': 'demo'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert 'demo' in body['images'][0]['tags']
        assert body['filters_applied']['tag'] == 'demo'
        assert body['filters_applied']['user_id'] is None
    
    @patch('boto3.resource')
    def test_list_images_with_both_filters(self, mock_resource):
        """Test listing images with both user_id and tag filters"""
        # Mock DynamoDB table with test data
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'image_id': 'test-1',
                    'user_id': 'alice',
                    'filename': 'vacation1.jpg',
                    'upload_date': '2024-01-01T00:00:00',
                    'tags': ['vacation', 'beach'],
                    's3_key': 'images/alice/test-1.jpg',
                    'description': 'Beach vacation'
                },
                {
                    'image_id': 'test-2',
                    'user_id': 'alice',
                    'filename': 'work1.jpg',
                    'upload_date': '2024-01-02T00:00:00',
                    'tags': ['work'],
                    's3_key': 'images/alice/test-2.jpg',
                    'description': 'Work photo'
                },
                {
                    'image_id': 'test-3',
                    'user_id': 'bob',
                    'filename': 'vacation2.jpg',
                    'upload_date': '2024-01-03T00:00:00',
                    'tags': ['vacation'],
                    's3_key': 'images/bob/test-3.jpg',
                    'description': 'Bob vacation'
                }
            ]
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images',
            'queryStringParameters': {'user_id': 'alice', 'tag': 'vacation'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert body['images'][0]['user_id'] == 'alice'
        assert 'vacation' in body['images'][0]['tags']
        assert body['filters_applied']['user_id'] == 'alice'
        assert body['filters_applied']['tag'] == 'vacation'
    
    @patch('boto3.client')
    @patch('boto3.resource')
    @patch('uuid.uuid4')
    @patch('datetime.datetime')
    def test_upload_image_success(self, mock_datetime, mock_uuid, mock_resource, mock_client):
        """Test successful image upload"""
        # Mock dependencies
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: 'test-image-id'
        mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00'
        
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client
        
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'POST',
            'path': '/images',
            'body': json.dumps({
                'user_id': 'test-user',
                'filename': 'test.jpg',
                'image_data': 'dGVzdA==',  # base64 for "test"
                'tags': ['test'],
                'description': 'Test image'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'image_id' in body
        assert body['message'] == 'Image uploaded successfully'
        assert 'upload_date' in body
    
    def test_upload_image_missing_fields(self):
        """Test upload with missing required fields"""
        event = {
            'httpMethod': 'POST',
            'path': '/images',
            'body': json.dumps({
                'user_id': 'test-user'
                # Missing filename and image_data
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required fields' in body['error']
    
    @patch('boto3.resource')
    def test_get_image_success(self, mock_resource):
        """Test getting existing image"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'image_id': 'test-image',
                'user_id': 'test-user',
                'filename': 'test.jpg',
                's3_key': 'images/test-user/test-image.jpg',
                'upload_date': '2024-01-01T00:00:00',
                'tags': ['test'],
                'description': 'Test image'
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images/test-image'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['image_id'] == 'test-image'
        assert body['user_id'] == 'test-user'
        assert 'download_url' in body
    
    @patch('boto3.resource')
    def test_get_image_not_found(self, mock_resource):
        """Test getting non-existent image"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_resource.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/images/non-existent'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Image not found'
    
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_delete_image_success(self, mock_resource, mock_client):
        """Test deleting existing image"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'image_id': 'test-image',
                'user_id': 'test-user',
                'filename': 'test.jpg',
                's3_key': 'images/test-user/test-image.jpg',
                'upload_date': '2024-01-01T00:00:00',
                'tags': ['test'],
                'description': 'Test image'
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/images/test-image'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Image deleted successfully'
        assert body['image_id'] == 'test-image'
    
    def test_options_request(self):
        """Test CORS preflight request"""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/images'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    def test_invalid_path(self):
        """Test invalid API path"""
        event = {
            'httpMethod': 'GET',
            'path': '/invalid'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Not found'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])