"""
Image model for DynamoDB operations
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError


class ImageModel:
    def __init__(self, dynamodb_endpoint: str = None):
        if dynamodb_endpoint:
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
        else:
            self.dynamodb = boto3.resource('dynamodb')
        
        self.table_name = 'images'
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_table(self):
        """Create the images table with GSI for filtering"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'image_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'image_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'upload_date',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user-upload-date-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'upload_date',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise e
            return self.table
    
    def save_image(self, user_id: str, filename: str, s3_key: str, 
                   tags: List[str] = None, description: str = None) -> Dict:
        """Save image metadata to DynamoDB"""
        image_id = str(uuid.uuid4())
        upload_date = datetime.utcnow().isoformat()
        
        item = {
            'image_id': image_id,
            'user_id': user_id,
            'filename': filename,
            's3_key': s3_key,
            'upload_date': upload_date,
            'tags': tags or [],
            'description': description or '',
            'created_at': upload_date,
            'updated_at': upload_date
        }
        
        self.table.put_item(Item=item)
        return item
    
    def get_image(self, image_id: str) -> Optional[Dict]:
        """Get image metadata by ID"""
        try:
            response = self.table.get_item(Key={'image_id': image_id})
            return response.get('Item')
        except ClientError:
            return None
    
    def list_images(self, user_id: str = None, tag_filter: str = None, 
                   date_from: str = None, date_to: str = None, 
                   limit: int = 50) -> List[Dict]:
        """List images with optional filters"""
        try:
            if user_id:
                # Use GSI for user-based queries
                if date_from or date_to:
                    key_condition = 'user_id = :user_id'
                    expression_values = {':user_id': user_id}
                    
                    if date_from and date_to:
                        key_condition += ' AND upload_date BETWEEN :date_from AND :date_to'
                        expression_values.update({
                            ':date_from': date_from,
                            ':date_to': date_to
                        })
                    elif date_from:
                        key_condition += ' AND upload_date >= :date_from'
                        expression_values[':date_from'] = date_from
                    elif date_to:
                        key_condition += ' AND upload_date <= :date_to'
                        expression_values[':date_to'] = date_to
                    
                    response = self.table.query(
                        IndexName='user-upload-date-index',
                        KeyConditionExpression=key_condition,
                        ExpressionAttributeValues=expression_values,
                        Limit=limit
                    )
                else:
                    response = self.table.query(
                        IndexName='user-upload-date-index',
                        KeyConditionExpression='user_id = :user_id',
                        ExpressionAttributeValues={':user_id': user_id},
                        Limit=limit
                    )
            else:
                # Scan all items (not recommended for production)
                response = self.table.scan(Limit=limit)
            
            items = response.get('Items', [])
            
            # Filter by tags if specified
            if tag_filter:
                items = [item for item in items if tag_filter in item.get('tags', [])]
            
            return items
        except ClientError as e:
            print(f"Error listing images: {e}")
            return []
    
    def delete_image(self, image_id: str) -> bool:
        """Delete image metadata from DynamoDB"""
        try:
            self.table.delete_item(Key={'image_id': image_id})
            return True
        except ClientError:
            return False