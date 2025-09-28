# Instagram-like Image Service API Documentation

## Overview

This is a REST API service for uploading, storing, and managing images with metadata, similar to Instagram. The service uses AWS Lambda, S3, DynamoDB, and API Gateway with LocalStack for local development.

## Base URL

```
http://localhost:4566/restapis/{api-id}/test/_user_request_
```

## Endpoints

### 1. Upload Image

**POST** `/images`

Upload an image with metadata.

#### Request Body

```json
{
  "user_id": "string (required)",
  "filename": "string (required)",
  "image_data": "string (required, base64-encoded image)",
  "tags": ["string"] (optional),
  "description": "string (optional)"
}
```

#### Response

**Success (201):**
```json
{
  "message": "Image uploaded successfully",
  "image_id": "uuid",
  "upload_date": "ISO 8601 timestamp"
}
```

**Error (400):**
```json
{
  "error": "Missing required fields: user_id, filename, image_data"
}
```

#### Example

```bash
curl -X POST http://localhost:4566/restapis/{api-id}/test/_user_request_/images \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "filename": "sunset.jpg",
    "image_data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bz6LzqAVhFCsVoOEvyDYSRy3WzVZAKSZq34H9EiVk6nZd+7/AB=",
    "tags": ["sunset", "nature", "beautiful"],
    "description": "Beautiful sunset over the ocean"
  }'
```

### 2. List Images

**GET** `/images`

List all images with optional filters.

#### Query Parameters

- `user_id` (optional): Filter by user ID
- `tag` (optional): Filter by tag
- `date_from` (optional): Filter images from this date (ISO 8601)
- `date_to` (optional): Filter images until this date (ISO 8601)
- `limit` (optional): Number of results to return (default: 50)

#### Response

**Success (200):**
```json
{
  "images": [
    {
      "image_id": "uuid",
      "user_id": "string",
      "filename": "string",
      "upload_date": "ISO 8601 timestamp",
      "tags": ["string"],
      "description": "string"
    }
  ],
  "count": "number"
}
```

#### Examples

```bash
# List all images
curl http://localhost:4566/restapis/{api-id}/test/_user_request_/images

# List images by user
curl "http://localhost:4566/restapis/{api-id}/test/_user_request_/images?user_id=user123"

# List images with tag filter
curl "http://localhost:4566/restapis/{api-id}/test/_user_request_/images?tag=nature"

# List images with date range
curl "http://localhost:4566/restapis/{api-id}/test/_user_request_/images?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59"

# Combined filters
curl "http://localhost:4566/restapis/{api-id}/test/_user_request_/images?user_id=user123&tag=sunset&limit=10"
```

### 3. View/Download Image

**GET** `/images/{image_id}`

Get image metadata and download URL.

#### Path Parameters

- `image_id` (required): The unique identifier of the image

#### Response

**Success (200):**
```json
{
  "image_id": "uuid",
  "user_id": "string",
  "filename": "string",
  "upload_date": "ISO 8601 timestamp",
  "tags": ["string"],
  "description": "string",
  "download_url": "string (presigned S3 URL)"
}
```

**Error (404):**
```json
{
  "error": "Image not found"
}
```

#### Example

```bash
curl http://localhost:4566/restapis/{api-id}/test/_user_request_/images/123e4567-e89b-12d3-a456-426614174000
```

### 4. Delete Image

**DELETE** `/images/{image_id}`

Delete an image and its metadata.

#### Path Parameters

- `image_id` (required): The unique identifier of the image

#### Response

**Success (200):**
```json
{
  "message": "Image deleted successfully",
  "image_id": "uuid"
}
```

**Error (404):**
```json
{
  "error": "Image not found"
}
```

#### Example

```bash
curl -X DELETE http://localhost:4566/restapis/{api-id}/test/_user_request_/images/123e4567-e89b-12d3-a456-426614174000
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Description of the validation error"
}
```

### 404 Not Found
```json
{
  "error": "Image not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## Data Models

### Image Metadata

```json
{
  "image_id": "string (UUID)",
  "user_id": "string",
  "filename": "string",
  "s3_key": "string",
  "upload_date": "string (ISO 8601)",
  "tags": ["string"],
  "description": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.7+
- pip

### Local Development Setup

1. **Clone the repository and install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Start LocalStack:**

```bash
docker-compose up -d
```

3. **Set up AWS resources:**

```bash
python scripts/setup_localstack.py
```

4. **Run tests:**

```bash
pytest tests/ -v
```

5. **Test API endpoints:**

```bash
python scripts/test_api.py
```

### Configuration

The service uses the following AWS resources:

- **S3 Bucket**: `instagram-images`
- **DynamoDB Table**: `images`
- **Lambda Functions**: One for each endpoint
- **API Gateway**: REST API with resource mapping