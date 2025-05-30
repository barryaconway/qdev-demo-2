import json
import os
import boto3
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
PRESIGNED_URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', 3600))  # Default 1 hour

def lambda_handler(event, context):
    """
    Lambda function to handle photo retrieval.
    
    This function:
    1. Extracts the photo ID from the request path parameters
    2. Retrieves the photo metadata from DynamoDB
    3. Generates a pre-signed URL for the photo in S3
    4. Returns the photo metadata and pre-signed URL
    
    Args:
        event (dict): API Gateway Lambda Proxy Input Format
        context (object): Lambda Context runtime methods and attributes
        
    Returns:
        dict: API Gateway Lambda Proxy Output Format
    """
    logger.info('Processing get photo request')
    
    try:
        # Check if the bucket name is configured
        if not BUCKET_NAME:
            raise ValueError("Photos bucket name is not configured")
        
        # Extract photo ID from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return create_response(400, {'error': 'Missing photo ID in path parameters'})
        
        photo_id = event['pathParameters']['photoId']
        logger.info(f"Retrieving photo with ID: {photo_id}")
        
        # Get photo metadata from DynamoDB
        try:
            table = dynamodb.Table(PHOTOS_TABLE)
            response = table.get_item(Key={'photoId': photo_id})
            
            if 'Item' not in response:
                logger.warning(f"Photo not found: {photo_id}")
                return create_response(404, {'error': 'Photo not found'})
            
            photo_metadata = response['Item']
            logger.info(f"Retrieved metadata for photo: {photo_id}")
            
        except ClientError as e:
            logger.error(f"Error retrieving metadata from DynamoDB: {str(e)}")
            return create_response(500, {'error': 'Failed to retrieve photo metadata'})
        
        # Generate pre-signed URL for S3 object
        try:
            s3_key = photo_metadata['s3Key']
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
            logger.info(f"Generated pre-signed URL for photo: {photo_id}")
            
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return create_response(500, {'error': 'Failed to generate download URL'})
        
        # Return success response with photo details and pre-signed URL
        return create_response(200, {
            'photoId': photo_metadata['photoId'],
            'fileName': photo_metadata['fileName'],
            'uploadTimestamp': photo_metadata['uploadTimestamp'],
            'downloadUrl': presigned_url
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