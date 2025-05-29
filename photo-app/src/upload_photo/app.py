import json
import os
import uuid
import base64
import boto3
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE', 'Photos')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')

# Initialize DynamoDB table
photos_table = dynamodb.Table(PHOTOS_TABLE)

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Receives a base64 encoded image and metadata from API Gateway
    2. Decodes the image
    3. Generates a unique ID for the photo
    4. Uploads the photo to S3
    5. Stores metadata in DynamoDB
    6. Returns the photo ID and other relevant information
    
    Args:
        event: API Gateway event containing the photo data and metadata
        context: Lambda context
        
    Returns:
        API Gateway response with status code and photo information
    """
    try:
        logger.info("Processing upload request")
        
        # Parse request body
        if 'body' not in event:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing request body'})
            }
            
        # If the body is a string (from API Gateway), parse it as JSON
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        
        # Validate required fields
        if 'image' not in body or 'fileName' not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required fields: image and fileName'})
            }
        
        # Extract data from request
        image_data = body['image']
        file_name = body['fileName']
        
        # Remove potential data URL prefix
        if image_data.startswith('data:'):
            # Extract the base64 part after the comma
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_binary = base64.b64decode(image_data)
        
        # Generate unique photo ID and S3 key
        photo_id = str(uuid.uuid4())
        s3_key = f"{photo_id}/{file_name}"
        
        # Upload to S3
        logger.info(f"Uploading file to S3: {s3_key}")
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=image_binary,
            ContentType=get_content_type(file_name)
        )
        
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Store metadata in DynamoDB
        logger.info(f"Storing metadata in DynamoDB for photo: {photo_id}")
        photos_table.put_item(
            Item={
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            }
        )
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                'message': 'Photo uploaded successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def get_content_type(file_name):
    """
    Determine the content type based on file extension
    
    Args:
        file_name: Name of the file
        
    Returns:
        Content type string
    """
    extension = os.path.splitext(file_name.lower())[1]
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml'
    }
    return content_types.get(extension, 'application/octet-stream')