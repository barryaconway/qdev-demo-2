# Serverless Photo Application

A serverless application for uploading, storing, and retrieving photos using AWS services. This application provides a simple way to upload photos via a web interface, store them securely in S3, and retrieve them using pre-signed URLs.

## Architecture

![Architecture Diagram](https://via.placeholder.com/800x400?text=Photo+App+Architecture+Diagram)

### Components

- **Frontend**: Simple HTML/CSS/JavaScript web interface for uploading and retrieving photos
- **API Gateway**: HTTP API with endpoints for uploading and retrieving photos
- **Lambda Functions**: Serverless functions for handling photo uploads and retrievals
- **S3**: Private bucket for secure photo storage
- **DynamoDB**: NoSQL database for storing photo metadata

### API Endpoints

- `POST /photos`: Upload a photo and its metadata
- `GET /photos/{photoId}`: Get a photo by ID and generate a pre-signed URL for download

## Prerequisites

- [AWS Account](https://aws.amazon.com/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/) (for AWS CDK, if needed)

## Setup and Deployment

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/photo-app.git
   cd photo-app
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install test dependencies:
   ```bash
   pip install pytest pytest-mock
   ```

### Deploy to AWS

1. Build the application:
   ```bash
   sam build
   ```

2. Deploy the application:
   ```bash
   sam deploy --guided
   ```

   Follow the prompts to configure your deployment. For the first deployment, you'll need to provide:
   - Stack name (e.g., photo-app)
   - AWS Region
   - Parameter values (if any)
   - Confirm IAM role creation
   - Allow SAM CLI to create IAM roles

3. Note the outputs from the deployment, including the API Gateway endpoint URL.

### Testing the Deployment

1. Open the frontend application in your browser:
   ```bash
   open src/frontend/index.html
   ```

2. Configure the API URL in the application using the API Gateway endpoint URL from the deployment outputs.

3. Upload a photo and verify that it appears in the gallery.

4. Copy the photo ID and use it to retrieve the photo.

## Running Tests

Run unit tests:
```bash
pytest tests/unit
```

## Project Structure

```
photo-app/
├── src/
│   ├── upload_photo/
│   │   ├── app.py                 # Lambda function for uploading photos
│   │   └── requirements.txt       # Dependencies for upload function
│   ├── get_photo/
│   │   ├── app.py                 # Lambda function for retrieving photos
│   │   └── requirements.txt       # Dependencies for get function
│   └── frontend/
│       └── index.html             # Simple web interface for testing
├── tests/
│   └── unit/
│       ├── test_upload_photo.py   # Unit tests for upload function
│       └── test_get_photo.py      # Unit tests for get function
├── template.yaml                  # AWS SAM template
└── README.md                      # Project documentation
```

## Security Considerations

- **S3 Bucket**: The S3 bucket is configured as private, with no public access.
- **IAM Permissions**: Lambda functions use least-privilege permissions.
- **Pre-signed URLs**: Photos are accessed via pre-signed URLs that expire after a configurable time.
- **API Gateway**: CORS is configured to allow requests from specific origins.

## Assumptions and Limitations

- **File Size**: The application assumes photos are less than 6MB (API Gateway payload limit).
- **File Types**: The application accepts common image formats (JPEG, PNG, GIF, etc.).
- **Authentication**: This demo does not include user authentication. In a production environment, you would want to add authentication and authorization.
- **Scaling**: The serverless architecture will automatically scale with demand, but be aware of AWS service limits.

## Future Enhancements

- Add user authentication and authorization
- Implement image resizing and optimization
- Add support for photo albums and organization
- Implement a more robust frontend with a modern framework (React, Vue, etc.)
- Add support for image metadata (EXIF data)
- Implement a CDN for faster photo delivery

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.