"""
Unit tests for models
"""
import pytest
from unittest.mock import MagicMock, patch
from src.models.image import ImageModel


class TestImageModel:
    
    @patch('src.models.image.boto3.resource')
    def test_save_image(self, mock_boto3_resource):
        """Test saving image metadata"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        # Create model instance
        image_model = ImageModel()
        
        # Test save_image
        result = image_model.save_image(
            user_id='test-user',
            filename='test.jpg',
            s3_key='images/test-user/test.jpg',
            tags=['nature', 'landscape'],
            description='Test description'
        )
        
        # Assertions
        assert result['user_id'] == 'test-user'
        assert result['filename'] == 'test.jpg'
        assert result['s3_key'] == 'images/test-user/test.jpg'
        assert result['tags'] == ['nature', 'landscape']
        assert result['description'] == 'Test description'
        assert 'image_id' in result
        assert 'upload_date' in result
        
        # Verify table.put_item was called
        mock_table.put_item.assert_called_once()
    
    @patch('src.models.image.boto3.resource')
    def test_get_image_success(self, mock_boto3_resource):
        """Test getting image metadata successfully"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'image_id': 'test-id',
                'user_id': 'test-user',
                'filename': 'test.jpg'
            }
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        # Create model instance
        image_model = ImageModel()
        
        # Test get_image
        result = image_model.get_image('test-id')
        
        # Assertions
        assert result['image_id'] == 'test-id'
        assert result['user_id'] == 'test-user'
        assert result['filename'] == 'test.jpg'
        
        # Verify table.get_item was called
        mock_table.get_item.assert_called_once_with(Key={'image_id': 'test-id'})
    
    @patch('src.models.image.boto3.resource')
    def test_get_image_not_found(self, mock_boto3_resource):
        """Test getting non-existent image"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item key
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        # Create model instance
        image_model = ImageModel()
        
        # Test get_image
        result = image_model.get_image('non-existent-id')
        
        # Assertions
        assert result is None
    
    @patch('src.models.image.boto3.resource')
    def test_delete_image(self, mock_boto3_resource):
        """Test deleting image metadata"""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        # Create model instance
        image_model = ImageModel()
        
        # Test delete_image
        result = image_model.delete_image('test-id')
        
        # Assertions
        assert result == True
        
        # Verify table.delete_item was called
        mock_table.delete_item.assert_called_once_with(Key={'image_id': 'test-id'})