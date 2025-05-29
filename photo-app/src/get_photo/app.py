import json
import os
import boto3
from botocore.exceptions import ClientError
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
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION', 3600))  # Default 1 hour

# Initialize DynamoDB table
photos_table = dynamodb.Table(PHOTOS_TABLE)

def lambda_handler(event, context):
    """
    Lambda function to retrieve photo information and generate a pre-signed URL.
    
    This function:
    1. Extracts the photo ID from the path parameters
    2. Retrieves the photo metadata from DynamoDB
    3. Generates a pre-signed URL for downloading the photo from S3
    4. Returns the photo metadata and pre-signed URL
    
    Args:
        event: API Gateway event containing the photo ID
        context: Lambda context
        
    Returns:
        API Gateway response with status code and photo information
    """
    try:
        logger.info("Processing get photo request")
        
        # Extract photo ID from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing photo ID'})
            }
            
        photo_id = event['pathParameters']['photoId']
        logger.info(f"Retrieving photo with ID: {photo_id}")
        
        # Get photo metadata from DynamoDB
        response = photos_table.get_item(
            Key={'photoId': photo_id}
        )
        
        # Check if photo exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Photo not found'})
            }
            
        photo_metadata = response['Item']
        s3_key = photo_metadata['s3Key']
        
        # Generate pre-signed URL
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=URL_EXPIRATION
            )
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to generate download URL'})
            }
            
        # Add pre-signed URL to response
        photo_metadata['downloadUrl'] = presigned_url
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps(photo_metadata)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving photo: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }