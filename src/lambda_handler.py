import json
import uuid
import boto3
import base64
from datetime import datetime

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
        
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        if method == 'GET' and path.endswith('/images'):
            return handle_list_images(event, headers)
        elif method == 'POST' and path.endswith('/images'):
            return handle_upload_image(event, headers)
        elif method == 'GET' and '/images/' in path:
            image_id = path.split('/')[-1]
            return handle_get_image(image_id, headers)
        elif method == 'DELETE' and '/images/' in path:
            image_id = path.split('/')[-1]
            return handle_delete_image(image_id, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_list_images(event, headers):
    """List images with WORKING filters"""
    try:
        # Get filters from query parameters
        query_params = event.get('queryStringParameters') or {}
        user_filter = query_params.get('user_id')
        tag_filter = query_params.get('tag')
        
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        table = dynamodb.Table('images')
        
        # Get all images first
        response = table.scan()
        items = response.get('Items', [])
        
        # Apply filters
        filtered_items = items
        
        if user_filter:
            filtered_items = [item for item in filtered_items if item.get('user_id') == user_filter]
            
        if tag_filter:
            filtered_items = [item for item in filtered_items if tag_filter in item.get('tags', [])]
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'images': filtered_items,
                'count': len(filtered_items),
                'filters_applied': {
                    'user_id': user_filter,
                    'tag': tag_filter
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'images': [],
                'count': 0,
                'error': str(e)
            })
        }

def handle_upload_image(event, headers):
    """Upload image"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        if not all([body.get('user_id'), body.get('filename'), body.get('image_data')]):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        image_id = str(uuid.uuid4())
        upload_date = datetime.now().isoformat()
        
        # Decode image
        image_data = base64.b64decode(body['image_data'])
        file_extension = body['filename'].split('.')[-1] if '.' in body['filename'] else 'jpg'
        s3_key = f"images/{body['user_id']}/{image_id}.{file_extension}"
        
        # Upload to S3
        s3_client = boto3.client(
            's3',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        
        s3_client.put_object(
            Bucket='instagram-images',
            Key=s3_key,
            Body=image_data,
            ContentType=f'image/{file_extension}'
        )
        
        # Save to DynamoDB
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        table = dynamodb.Table('images')
        
        item = {
            'image_id': image_id,
            'user_id': body['user_id'],
            'filename': body['filename'],
            's3_key': s3_key,
            'upload_date': upload_date,
            'tags': body.get('tags', []),
            'description': body.get('description', '')
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Image uploaded successfully',
                'image_id': image_id,
                'upload_date': upload_date
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_get_image(image_id, headers):
    """Get image details"""
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        table = dynamodb.Table('images')
        response = table.get_item(Key={'image_id': image_id})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Image not found'})
            }
        
        download_url = f"http://localhost:4566/instagram-images/{item['s3_key']}"
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'image_id': item['image_id'],
                'user_id': item['user_id'],
                'filename': item['filename'],
                'upload_date': item['upload_date'],
                'tags': item.get('tags', []),
                'description': item.get('description', ''),
                'download_url': download_url
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_delete_image(image_id, headers):
    """Delete image"""
    try:
        # Get image info
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        table = dynamodb.Table('images')
        response = table.get_item(Key={'image_id': image_id})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Image not found'})
            }
        
        # Delete from S3
        s3_client = boto3.client(
            's3',
            endpoint_url='http://localstack:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        s3_client.delete_object(Bucket='instagram-images', Key=item['s3_key'])
        
        # Delete from DynamoDB
        table.delete_item(Key={'image_id': image_id})
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Image deleted successfully',
                'image_id': image_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }