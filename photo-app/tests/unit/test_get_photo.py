import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the Lambda function
import app

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_successful_get_photo(self, mock_dynamodb, mock_s3):
        """Test successful photo retrieval"""
        # Test data
        test_photo_id = "test-photo-id"
        test_file_name = "test_image.jpg"
        test_s3_key = f"photos/{test_photo_id}/{test_file_name}"
        test_timestamp = "2023-01-01T12:00:00"
        test_presigned_url = "https://test-bucket.s3.amazonaws.com/test-presigned-url"
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': test_photo_id,
                'fileName': test_file_name,
                'uploadTimestamp': test_timestamp,
                's3Key': test_s3_key
            }
        }
        
        # Mock S3 presigned URL generation
        mock_s3.generate_presigned_url.return_value = test_presigned_url
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': test_photo_id
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], test_photo_id)
        self.assertEqual(response_body['fileName'], test_file_name)
        self.assertEqual(response_body['uploadTimestamp'], test_timestamp)
        self.assertEqual(response_body['downloadUrl'], test_presigned_url)
        
        # Verify DynamoDB get_item was called correctly
        mock_table.get_item.assert_called_once_with(Key={'photoId': test_photo_id})
        
        # Verify S3 generate_presigned_url was called correctly
        mock_s3.generate_presigned_url.assert_called_once()
        s3_call_args = mock_s3.generate_presigned_url.call_args[1]
        self.assertEqual(s3_call_args['Params']['Bucket'], 'test-photos-bucket')
        self.assertEqual(s3_call_args['Params']['Key'], test_s3_key)

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_missing_photo_id(self, mock_dynamodb, mock_s3):
        """Test handling of missing photo ID"""
        # Create test event with no path parameters
        test_event = {}
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing photo ID in path parameters')
        
        # Verify no DynamoDB or S3 calls were made
        mock_dynamodb.Table.assert_not_called()
        mock_s3.generate_presigned_url.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_photo_not_found(self, mock_dynamodb, mock_s3):
        """Test handling of photo not found in DynamoDB"""
        # Test data
        test_photo_id = "nonexistent-photo-id"
        
        # Mock DynamoDB response for item not found
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {}  # No Item in response
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': test_photo_id
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Photo not found')
        
        # Verify DynamoDB get_item was called but not S3
        mock_table.get_item.assert_called_once_with(Key={'photoId': test_photo_id})
        mock_s3.generate_presigned_url.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_dynamodb_error(self, mock_dynamodb, mock_s3):
        """Test handling of DynamoDB error"""
        # Test data
        test_photo_id = "test-photo-id"
        
        # Mock DynamoDB to raise an exception
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.side_effect = Exception("DynamoDB get failed")
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': test_photo_id
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to retrieve photo metadata')
        
        # Verify no S3 calls were made
        mock_s3.generate_presigned_url.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_s3_presigned_url_error(self, mock_dynamodb, mock_s3):
        """Test handling of S3 presigned URL generation error"""
        # Test data
        test_photo_id = "test-photo-id"
        test_file_name = "test_image.jpg"
        test_s3_key = f"photos/{test_photo_id}/{test_file_name}"
        test_timestamp = "2023-01-01T12:00:00"
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': test_photo_id,
                'fileName': test_file_name,
                'uploadTimestamp': test_timestamp,
                's3Key': test_s3_key
            }
        }
        
        # Mock S3 to raise an exception
        mock_s3.generate_presigned_url.side_effect = Exception("S3 presigned URL generation failed")
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': test_photo_id
            }
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to generate download URL')

if __name__ == '__main__':
    unittest.main()