# Instagram-like Image Service API Documentation

## Overview

This is a REST API service for uploading, storing, and managing images with metadata, similar to Instagram. The service uses AWS Lambda, S3, DynamoDB, and API Gateway with LocalStack for local development.

## Base URL

```
http://localhost:4566/restapis/{api-id}/test/_user_request_
```

## Quick Start

```bash
# Start LocalStack
docker-compose up -d

# Setup everything (S3, DynamoDB, Lambda, API Gateway)
python3 scripts/setup_demo.py

# Test the API (use the URLs from setup output)
curl http://localhost:4566/restapis/YOUR_API_ID/prod/_user_request_/images
```

## Project Structure

# Run tests with coverage
python -m pytest tests/ -v --tb=short
```
├── docker-compose.yml     # LocalStack configuration
├── requirements.txt       # Python dependencies
├── scripts/
│   └── setup_demo.py     # Complete setup script
└── src/
    └── lambda_handler.py # Single Lambda function
```

## API Endpoints

- `POST /images` - Upload image
- `GET /images` - List all images with optional filters
- `GET /images/{id}` - Get image details
- `DELETE /images/{id}` - Delete image

### List Images Filters

The list endpoint supports two filters via query parameters:

1. **user_id filter**: `GET /images?user_id=test-user`
2. **tag filter**: `GET /images?tag=demo`
3. **Combined filters**: `GET /images?user_id=test-user&tag=demo`

## Example Usage

```bash
# Upload image
curl -X POST http://localhost:4566/restapis/API_ID/prod/_user_request_/images \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","filename":"test.jpg","image_data":"dGVzdA==","tags":["demo"]}'

# List images
curl http://localhost:4566/restapis/API_ID/prod/_user_request_/images

# List images by user
curl "http://localhost:4566/restapis/API_ID/prod/_user_request_/images?user_id=test-user"

# List images by tag
curl "http://localhost:4566/restapis/API_ID/prod/_user_request_/images?tag=demo"

# Get image
curl http://localhost:4566/restapis/API_ID/prod/_user_request_/images/IMAGE_ID

# Delete image
curl -X DELETE http://localhost:4566/restapis/API_ID/prod/_user_request_/images/IMAGE_ID
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_lambda_handler.py::TestLambdaHandler::test_list_images_with_both_filters -v
```

## Reset Everything

```bash
docker-compose down
docker-compose up -d
python3 scripts/setup_demo.py
```