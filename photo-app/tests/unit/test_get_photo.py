import json
import os
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Set environment variables for testing
os.environ['PHOTOS_TABLE'] = 'test-photos-table'
os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
os.environ['URL_EXPIRATION'] = '3600'

# Import the Lambda function
from src.get_photo.app import lambda_handler

class TestGetPhoto(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('src.get_photo.app.boto3.client')
    @patch('src.get_photo.app.boto3.resource')
    def test_successful_get_photo(self, mock_resource, mock_client):
        """Test successful photo retrieval"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://test-presigned-url.com/photo.jpg'
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test.jpg'
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse the response body
        body = json.loads(response['body'])
        self.assertEqual(body['photoId'], 'test-photo-id')
        self.assertEqual(body['fileName'], 'test.jpg')
        self.assertEqual(body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(body['s3Key'], 'test-photo-id/test.jpg')
        self.assertEqual(body['downloadUrl'], 'https://test-presigned-url.com/photo.jpg')
        
        # Verify S3 generate_presigned_url was called
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'test-photos-bucket',
                'Key': 'test-photo-id/test.jpg'
            },
            ExpiresIn=3600
        )
        
        # Verify DynamoDB get_item was called
        mock_table.get_item.assert_called_once_with(
            Key={'photoId': 'test-photo-id'}
        )

    def test_missing_photo_id(self):
        """Test handling of missing photo ID"""
        # Test with no pathParameters
        event = {}
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Missing photo ID')
        
        # Test with empty pathParameters
        event = {'pathParameters': {}}
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Missing photo ID')

    @patch('src.get_photo.app.boto3.client')
    @patch('src.get_photo.app.boto3.resource')
    def test_photo_not_found(self, mock_resource, mock_client):
        """Test handling of photo not found"""
        # Mock DynamoDB table and response for photo not found
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item in response
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'non-existent-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Photo not found')

    @patch('src.get_photo.app.boto3.client')
    @patch('src.get_photo.app.boto3.resource')
    def test_presigned_url_error(self, mock_resource, mock_client):
        """Test handling of error when generating pre-signed URL"""
        # Mock S3 client to raise an exception
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'TestException', 'Message': 'Test error message'}},
            'generate_presigned_url'
        )
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'test-photo-id/test.jpg'
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Failed to generate download URL')

    @patch('src.get_photo.app.boto3.client')
    @patch('src.get_photo.app.boto3.resource')
    def test_general_exception_handling(self, mock_resource, mock_client):
        """Test general exception handling"""
        # Mock DynamoDB table to raise an exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("Test exception")
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertIn('Internal server error', body['error'])

if __name__ == '__main__':
    unittest.main()