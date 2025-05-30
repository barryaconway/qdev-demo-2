# Q Dev Demo Reinforce Serverless Photo App

A serverless application for uploading, storing, and retrieving photos using AWS services.

## Architecture

This application uses a serverless architecture with the following AWS components:

![Architecture Diagram](https://via.placeholder.com/800x400?text=Serverless+Photo+App+Architecture)

### Components

- **Frontend**: Simple HTML/CSS/JavaScript web interface hosted in an S3 bucket
- **API Gateway**: HTTP API with endpoints for uploading and retrieving photos
- **Lambda Functions**: 
  - `UploadPhotoFunction`: Handles photo uploads, stores in S3, saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata and generates pre-signed URLs for downloads
- **S3**: Private bucket for secure photo storage
- **DynamoDB**: NoSQL database for storing photo metadata

### API Endpoints

- `POST /photos`: Upload a photo with metadata
- `GET /photos/{photoId}`: Get photo metadata and a pre-signed URL for download

## Setup Instructions

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed
- [Python 3.9](https://www.python.org/downloads/) or later

### Deployment

1. Clone this repository:
   ```
   git clone <repository-url>
   cd photo-app
   ```

2. Build the application:
   ```
   sam build
   ```

3. Deploy the application:
   ```
   sam deploy --guided
   ```
   
   Follow the prompts to configure your deployment. For first-time deployment, you'll need to provide:
   - Stack name (e.g., `photo-app`)
   - AWS Region
   - Confirmation for IAM role creation

4. After deployment, note the outputs:
   - `ApiEndpoint`: The URL for your API
   - `FrontendWebsiteURL`: The URL for the frontend website

5. Update the frontend with your API endpoint:
   - Edit `src/frontend/index.html`
   - Replace `const API_ENDPOINT = 'https://your-api-gateway-url.amazonaws.com';` with your actual API endpoint
   - Upload the frontend files to the created S3 bucket:
     ```
     aws s3 sync src/frontend/ s3://<frontend-bucket-name>/
     ```

### Local Development

#### Running the Frontend Locally

You can test the frontend locally by opening `src/frontend/index.html` in a web browser. However, you'll need to:

1. Update the `API_ENDPOINT` variable in the HTML file to point to your deployed API
2. Handle CORS if testing with a deployed backend

#### Testing Lambda Functions Locally

1. Install dependencies:
   ```
   pip install -r src/upload_photo/requirements.txt
   pip install -r src/get_photo/requirements.txt
   ```

2. Invoke the Lambda functions locally:
   ```
   # For upload function
   sam local invoke UploadPhotoFunction --event events/upload_event.json
   
   # For get function
   sam local invoke GetPhotoFunction --event events/get_event.json
   ```

3. Run unit tests:
   ```
   python -m unittest discover tests/unit
   ```

## Security Considerations

- **S3 Bucket**: The photos bucket is private, and photos are only accessible via pre-signed URLs
- **IAM Roles**: Lambda functions use least-privilege permissions
- **API Access**: CORS is configured to restrict access to approved origins
- **Data Protection**: DynamoDB point-in-time recovery is enabled

## Assumptions

- Users are authenticated through a separate system (not implemented in this demo)
- File size limits are handled by API Gateway and Lambda defaults
- Only image file types are supported (enforced by frontend)
- Pre-signed URLs expire after 1 hour

## Future Enhancements

- User authentication and authorization
- Photo sharing capabilities
- Image processing (resizing, thumbnails)
- Search functionality
- Pagination for listing photos
- Mobile application support

## License

[MIT License](LICENSE)