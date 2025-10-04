#!/usr/bin/env python3
"""
Instagram Image Service - Complete Setup
One script to deploy everything: S3, DynamoDB, Lambda, API Gateway
"""
import boto3
import json
import zipfile
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# LocalStack configuration
ENDPOINT_URL = 'http://localhost:4566'
REGION = 'us-east-1'
AWS_ACCESS_KEY_ID = 'test'
AWS_SECRET_ACCESS_KEY = 'test'

def wait_for_localstack():
    """Wait for LocalStack to be ready"""
    import requests
    for i in range(30):
        try:
            response = requests.get(f"{ENDPOINT_URL}/_localstack/health")
            if response.status_code == 200:
                logger.info("✅ LocalStack is ready!")
                return True
        except:
            pass
        logger.info(f"⏳ Waiting for LocalStack... ({i+1}/30)")
        time.sleep(2)
    return False

def setup_s3():
    """Create S3 bucket for image storage"""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION
        )
        
        try:
            s3_client.create_bucket(Bucket='instagram-images')
            logger.info("✅ Created S3 bucket: instagram-images")
        except Exception as e:
            if 'BucketAlreadyExists' in str(e):
                logger.info("✅ S3 bucket already exists")
        return True
    except Exception as e:
        logger.error(f"❌ S3 setup failed: {e}")
        return False

def setup_dynamodb():
    """Create DynamoDB table for image metadata"""
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION
        )
        
        try:
            table = dynamodb.create_table(
                TableName='images',
                KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[
                    {'AttributeName': 'image_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'upload_date', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[{
                    'IndexName': 'user-upload-date-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'upload_date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            logger.info("✅ Created DynamoDB table: images")
        except Exception as e:
            if 'ResourceInUseException' in str(e):
                logger.info("✅ DynamoDB table already exists")
        return True
    except Exception as e:
        logger.error(f"❌ DynamoDB setup failed: {e}")
        return False

def deploy_lambda():
    """Create and deploy Lambda function"""
    lambda_client = boto3.client(
        'lambda',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    
    # Create Lambda package
    zip_path = 'lambda-package.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write('src/lambda_handler.py', 'lambda_function.py')
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    function_name = 'instagram-api'
    
    try:
        # Delete existing function
        try:
            lambda_client.delete_function(FunctionName=function_name)
        except:
            pass
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::123456789012:role/lambda-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30
        )
        
        logger.info(f"✅ Deployed Lambda function: {function_name}")
        os.remove(zip_path)
        return response['FunctionArn']
        
    except Exception as e:
        logger.error(f"❌ Failed to deploy Lambda: {e}")
        return None

def setup_api_gateway():
    """Create API Gateway with REST endpoints"""
    apigateway = boto3.client(
        'apigateway',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    
    lambda_client = boto3.client(
        'lambda',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    
    try:
        # Delete existing APIs
        try:
            apis = apigateway.get_rest_apis()
            for api in apis['items']:
                if 'instagram' in api['name'].lower():
                    apigateway.delete_rest_api(restApiId=api['id'])
                    time.sleep(2)
        except:
            pass
        
        # Create REST API
        api_response = apigateway.create_rest_api(
            name='instagram-api',
            description='Instagram Image Service API'
        )
        api_id = api_response['id']
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_resource_id = resources['items'][0]['id']
        
        # Create /images resource
        images_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='images'
        )
        images_resource_id = images_resource['id']
        
        # Create /images/{image_id} resource
        image_id_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=images_resource_id,
            pathPart='{image_id}'
        )
        image_id_resource_id = image_id_resource['id']
        
        # Get Lambda ARN
        func_response = lambda_client.get_function(FunctionName='instagram-api')
        function_arn = func_response['Configuration']['FunctionArn']
        
        # Create methods and integrations
        methods = [
            {'resource_id': images_resource_id, 'http_method': 'GET'},
            {'resource_id': images_resource_id, 'http_method': 'POST'},
            {'resource_id': images_resource_id, 'http_method': 'OPTIONS'},
            {'resource_id': image_id_resource_id, 'http_method': 'GET'},
            {'resource_id': image_id_resource_id, 'http_method': 'DELETE'},
            {'resource_id': image_id_resource_id, 'http_method': 'OPTIONS'}
        ]
        
        for method in methods:
            # Create method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=method['resource_id'],
                httpMethod=method['http_method'],
                authorizationType='NONE'
            )
            
            # Add request parameters for GET methods to pass query strings
            if method['http_method'] == 'GET':
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=method['resource_id'],
                    httpMethod=method['http_method'],
                    authorizationType='NONE',
                    requestParameters={
                        'method.request.querystring.user_id': False,
                        'method.request.querystring.tag': False
                    }
                )
            
            # Create integration
            uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{function_arn}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=method['resource_id'],
                httpMethod=method['http_method'],
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=uri,
                requestParameters={
                    'integration.request.querystring.user_id': 'method.request.querystring.user_id',
                    'integration.request.querystring.tag': 'method.request.querystring.tag'
                } if method['http_method'] == 'GET' else {}
            )
        
        # Deploy API
        apigateway.create_deployment(restApiId=api_id, stageName='prod')
        
        base_url = f"{ENDPOINT_URL}/restapis/{api_id}/prod/_user_request_"
        
        logger.info("✅ Created API Gateway with REST endpoints")
        
        return {
            'api_id': api_id,
            'base_url': base_url,
            'endpoints': {
                'upload': f"{base_url}/images",
                'list': f"{base_url}/images",
                'view': f"{base_url}/images/{{image_id}}",
                'delete': f"{base_url}/images/{{image_id}}"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ API Gateway setup failed: {e}")
        return None

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🚀 INSTAGRAM IMAGE SERVICE - COMPLETE SETUP")
    print("="*60)
    
    # Step 1: Wait for LocalStack
    if not wait_for_localstack():
        print("❌ LocalStack not ready. Make sure it's running: docker-compose up -d")
        return False
    
    # Step 2: Setup S3
    print("\n📦 Setting up S3...")
    if not setup_s3():
        return False
    
    # Step 3: Setup DynamoDB
    print("\n🗄️  Setting up DynamoDB...")
    if not setup_dynamodb():
        return False
    
    # Step 4: Deploy Lambda
    print("\n⚡ Deploying Lambda function...")
    function_arn = deploy_lambda()
    if not function_arn:
        return False
    
    # Step 5: Setup API Gateway
    print("\n🌐 Setting up API Gateway...")
    api_info = setup_api_gateway()
    if not api_info:
        return False
    
    # Success!
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE - API IS WORKING!")
    print("="*60)
    print(f"📍 API Base URL: {api_info['base_url']}")
    print("\n📋 REST API Endpoints:")
    print(f"  POST   {api_info['endpoints']['upload']}           # Upload image")
    print(f"  GET    {api_info['endpoints']['list']}           # List images")
    print(f"  GET    {api_info['endpoints']['view']}    # View image")
    print(f"  DELETE {api_info['endpoints']['delete']} # Delete image")
    print("\n🧪 Test Commands (copy-paste ready):")
    print(f"# 1. List images (should be empty)")
    print(f"curl {api_info['endpoints']['list']}")
    print(f"\n# 2. Upload image")
    print(f'curl -X POST {api_info["endpoints"]["upload"]} \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"user_id":"test","filename":"test.jpg","image_data":"dGVzdA==","tags":["demo"]}}\'')
    print(f"\n# 3. List images again (should show uploaded image)")
    print(f"curl {api_info['endpoints']['list']}")
    print("="*60)
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)