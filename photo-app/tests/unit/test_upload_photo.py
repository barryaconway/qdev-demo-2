import json
import os
import unittest
from unittest.mock import patch, MagicMock
import base64

# Set environment variables for testing
os.environ['PHOTOS_TABLE'] = 'test-photos-table'
os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'

# Import the Lambda function
from src.upload_photo.app import lambda_handler, get_content_type

class TestUploadPhoto(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('src.upload_photo.app.boto3.client')
    @patch('src.upload_photo.app.boto3.resource')
    def test_successful_upload(self, mock_resource, mock_client):
        """Test successful photo upload"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test image data
        test_image = "test image data"
        base64_image = base64.b64encode(test_image.encode()).decode()
        
        # Create test event
        event = {
            'body': json.dumps({
                'image': base64_image,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        
        # Parse the response body
        body = json.loads(response['body'])
        self.assertIn('photoId', body)
        self.assertEqual(body['fileName'], 'test.jpg')
        self.assertIn('uploadTimestamp', body)
        self.assertIn('message', body)
        
        # Verify S3 put_object was called
        mock_s3.put_object.assert_called_once()
        _, kwargs = mock_s3.put_object.call_args
        self.assertEqual(kwargs['Bucket'], 'test-photos-bucket')
        self.assertIn('test.jpg', kwargs['Key'])
        self.assertEqual(kwargs['ContentType'], 'image/jpeg')
        
        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        _, kwargs = mock_table.put_item.call_args
        self.assertIn('Item', kwargs)
        self.assertIn('photoId', kwargs['Item'])
        self.assertEqual(kwargs['Item']['fileName'], 'test.jpg')
        self.assertIn('uploadTimestamp', kwargs['Item'])
        self.assertIn('s3Key', kwargs['Item'])

    def test_missing_body(self):
        """Test handling of missing request body"""
        event = {}
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Missing request body')

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        event = {
            'body': json.dumps({
                'fileName': 'test.jpg'
                # Missing 'image' field
            })
        }
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertIn('Missing required fields', body['error'])

    def test_get_content_type(self):
        """Test content type detection"""
        self.assertEqual(get_content_type('test.jpg'), 'image/jpeg')
        self.assertEqual(get_content_type('test.jpeg'), 'image/jpeg')
        self.assertEqual(get_content_type('test.png'), 'image/png')
        self.assertEqual(get_content_type('test.gif'), 'image/gif')
        self.assertEqual(get_content_type('test.unknown'), 'application/octet-stream')

    @patch('src.upload_photo.app.boto3.client')
    @patch('src.upload_photo.app.boto3.resource')
    def test_exception_handling(self, mock_resource, mock_client):
        """Test exception handling"""
        # Mock S3 client to raise an exception
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("Test exception")
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create test event
        event = {
            'body': json.dumps({
                'image': base64.b64encode(b'test image data').decode(),
                'fileName': 'test.jpg'
            })
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