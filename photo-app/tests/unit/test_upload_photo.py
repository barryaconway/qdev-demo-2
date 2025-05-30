import json
import unittest
from unittest.mock import patch, MagicMock
import base64
import os
import sys
import uuid

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the Lambda function
import app

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.dynamodb')
    @patch('uuid.uuid4')
    def test_successful_upload(self, mock_uuid, mock_dynamodb, mock_s3):
        """Test successful photo upload"""
        # Mock UUID generation
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = uuid.UUID(mock_uuid_value)
        
        # Mock S3 client
        mock_s3.put_object.return_value = {}
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = {}
        
        # Create test event
        test_file_content = base64.b64encode(b"test image content").decode('utf-8')
        test_file_name = "test_image.jpg"
        
        test_event = {
            'body': json.dumps({
                'fileContent': test_file_content,
                'fileName': test_file_name
            })
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], mock_uuid_value)
        self.assertEqual(response_body['fileName'], test_file_name)
        self.assertIn('uploadTimestamp', response_body)
        self.assertEqual(response_body['s3Key'], f"photos/{mock_uuid_value}/{test_file_name}")
        
        # Verify S3 upload was called correctly
        mock_s3.put_object.assert_called_once()
        s3_call_args = mock_s3.put_object.call_args[1]
        self.assertEqual(s3_call_args['Bucket'], 'test-photos-bucket')
        self.assertEqual(s3_call_args['Key'], f"photos/{mock_uuid_value}/{test_file_name}")
        self.assertEqual(s3_call_args['ContentType'], 'image/jpeg')
        
        # Verify DynamoDB put_item was called correctly
        mock_table.put_item.assert_called_once()
        ddb_call_args = mock_table.put_item.call_args[1]
        self.assertEqual(ddb_call_args['Item']['photoId'], mock_uuid_value)
        self.assertEqual(ddb_call_args['Item']['fileName'], test_file_name)
        self.assertEqual(ddb_call_args['Item']['s3Key'], f"photos/{mock_uuid_value}/{test_file_name}")

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_missing_request_body(self, mock_dynamodb, mock_s3):
        """Test handling of missing request body"""
        # Create test event with no body
        test_event = {}
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing request body')
        
        # Verify no S3 or DynamoDB calls were made
        mock_s3.put_object.assert_not_called()
        mock_dynamodb.Table.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_invalid_json_body(self, mock_dynamodb, mock_s3):
        """Test handling of invalid JSON in request body"""
        # Create test event with invalid JSON
        test_event = {
            'body': 'This is not valid JSON'
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Invalid JSON in request body')
        
        # Verify no S3 or DynamoDB calls were made
        mock_s3.put_object.assert_not_called()
        mock_dynamodb.Table.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_missing_required_fields(self, mock_dynamodb, mock_s3):
        """Test handling of missing required fields in request"""
        # Create test event with missing fields
        test_event = {
            'body': json.dumps({
                'someOtherField': 'value'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing required fields: fileContent and fileName')
        
        # Verify no S3 or DynamoDB calls were made
        mock_s3.put_object.assert_not_called()
        mock_dynamodb.Table.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    def test_s3_upload_error(self, mock_dynamodb, mock_s3):
        """Test handling of S3 upload error"""
        # Mock S3 client to raise an exception
        mock_s3.put_object.side_effect = Exception("S3 upload failed")
        
        # Create test event
        test_file_content = base64.b64encode(b"test image content").decode('utf-8')
        test_event = {
            'body': json.dumps({
                'fileContent': test_file_content,
                'fileName': 'test_image.jpg'
            })
        }
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to upload file to storage')
        
        # Verify no DynamoDB calls were made
        mock_dynamodb.Table.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb')
    @patch('uuid.uuid4')
    def test_dynamodb_error(self, mock_uuid, mock_dynamodb, mock_s3):
        """Test handling of DynamoDB error"""
        # Mock UUID generation
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = uuid.UUID(mock_uuid_value)
        
        # Mock S3 client
        mock_s3.put_object.return_value = {}
        
        # Mock DynamoDB table to raise an exception
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.side_effect = Exception("DynamoDB put failed")
        
        # Create test event
        test_file_content = base64.b64encode(b"test image content").decode('utf-8')
        test_event = {
            'body': json.dumps({
                'fileContent': test_file_content,
                'fileName': 'test_image.jpg'
            })
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
        self.assertEqual(response_body['error'], 'Failed to store photo metadata')
        
        # Verify S3 delete was called to clean up
        mock_s3.delete_object.assert_called_once()

if __name__ == '__main__':
    unittest.main()