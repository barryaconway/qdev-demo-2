import json
import os
import uuid
import base64
import boto3
from datetime import datetime
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE', 'Photos')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Extracts the photo data from the request
    2. Generates a unique ID for the photo
    3. Uploads the photo to S3
    4. Stores metadata in DynamoDB
    5. Returns the photo ID and other metadata
    
    Args:
        event (dict): API Gateway Lambda Proxy Input Format
        context (object): Lambda Context runtime methods and attributes
        
    Returns:
        dict: API Gateway Lambda Proxy Output Format
    """
    logger.info('Processing upload request')
    
    try:
        # Check if the bucket name is configured
        if not BUCKET_NAME:
            raise ValueError("Photos bucket name is not configured")
        
        # Parse the request body
        if 'body' not in event:
            return create_response(400, {'error': 'Missing request body'})
        
        # Check if the body is base64 encoded
        body = event['body']
        is_base64_encoded = event.get('isBase64Encoded', False)
        
        if is_base64_encoded:
            body = base64.b64decode(body).decode('utf-8')
        
        # Parse the body as JSON
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON in request body'})
        
        # Extract file data and metadata
        if 'fileContent' not in request_data or 'fileName' not in request_data:
            return create_response(400, {'error': 'Missing required fields: fileContent and fileName'})
        
        file_content_base64 = request_data['fileContent']
        file_name = request_data['fileName']
        
        # Decode the base64 file content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logger.error(f"Error decoding base64 content: {str(e)}")
            return create_response(400, {'error': 'Invalid file content encoding'})
        
        # Generate a unique photo ID
        photo_id = str(uuid.uuid4())
        
        # Create S3 key (path in the bucket)
        s3_key = f"photos/{photo_id}/{file_name}"
        
        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType=get_content_type(file_name)
            )
            logger.info(f"Successfully uploaded file to S3: {s3_key}")
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return create_response(500, {'error': 'Failed to upload file to storage'})
        
        # Store metadata in DynamoDB
        try:
            table = dynamodb.Table(PHOTOS_TABLE)
            timestamp = datetime.utcnow().isoformat()
            
            table.put_item(
                Item={
                    'photoId': photo_id,
                    'fileName': file_name,
                    'uploadTimestamp': timestamp,
                    's3Key': s3_key
                }
            )
            logger.info(f"Successfully stored metadata in DynamoDB for photo: {photo_id}")
        except ClientError as e:
            logger.error(f"Error storing metadata in DynamoDB: {str(e)}")
            # If DynamoDB fails, try to delete the S3 object to maintain consistency
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
            return create_response(500, {'error': 'Failed to store photo metadata'})
        
        # Return success response with photo details
        return create_response(201, {
            'photoId': photo_id,
            'fileName': file_name,
            'uploadTimestamp': timestamp,
            's3Key': s3_key
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def create_response(status_code, body):
    """
    Helper function to create a properly formatted API Gateway response
    
    Args:
        status_code (int): HTTP status code
        body (dict): Response body
        
    Returns:
        dict: Formatted response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # For CORS support
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body)
    }

def get_content_type(file_name):
    """
    Determine the content type based on file extension
    
    Args:
        file_name (str): Name of the file
        
    Returns:
        str: MIME type for the file
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