import logging
import requests
from datetime import datetime
from flask import Flask, jsonify
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants
ELEVENLABS_API_KEY = 'your-elevenlabs-api-key'
S3_BUCKET_NAME = 'your-s3-bucket-name'
S3_REGION = 'us-west-2'  # or your region
S3_CLIENT = boto3.client('s3', region_name=S3_REGION)

# Function to upload file to S3
def store_file_s3(file_content, filename):
    try:
        response = S3_CLIENT.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType='audio/mp3'
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info(f"File successfully uploaded to S3: {filename}")
            return True
        else:
            logger.error(f"Failed to upload file to S3: {filename}")
            return False
    except NoCredentialsError:
        logger.error("No AWS credentials found.")
        return False
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return False

# Function to generate a presigned URL for the uploaded file
def generate_presigned_url(filename):
    try:
        url = S3_CLIENT.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None

# Route to check the dubbing progress
@app.route('/check-progress/<dubbing_id>', methods=['GET'])
def check_progress(dubbing_id):
    # Simulate fetching the progress status from ElevenLabs (replace with actual API call)
    # Example: you might fetch the progress from ElevenLabs API using dubbing_id
    # For demonstration, we'll assume the file is complete.
    download_url = None
    file_content = None
    
    logger.info(f"Checking progress for dubbing ID: {dubbing_id}")
    # Simulating the final download URL after dubbing process is complete
    download_url = f"https://elevenlabs.com/dubbed_files/{dubbing_id}.mp3"  # Replace with the actual download URL from ElevenLabs
    
    # Simulate downloading the dubbed MP3 file
    download_response = requests.get(
        download_url,
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        stream=True  # Stream the response to handle large files
    )
    
    # Check if the download is successful before proceeding
    if download_response.status_code != 200:
        logger.error(f"Download failed: {download_response.text}")
        return jsonify({
            'status': 'failed',
            'error': 'Failed to download dubbed file'
        }), 500

    # Validate that the full file was downloaded
    file_content = download_response.content
    if not file_content:
        logger.error("Downloaded file is empty")
        return jsonify({
            'status': 'failed',
            'error': 'Downloaded file is empty or incomplete'
        }), 500

    # Proceed with the S3 upload only if the file is complete
    content_type = download_response.headers.get('content-type', '')
    extension = 'mp4' if 'video' in content_type else 'mp3'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    s3_filename = f"Eleven-Labs/dubbed_{dubbing_id}_{timestamp}.{extension}"

    # Upload the file to S3
    logger.info(f"Uploading to S3: {s3_filename}")
    if store_file_s3(file_content, s3_filename):
        # Generate a presigned URL for download
        download_url = generate_presigned_url(s3_filename)
        if download_url:
            return jsonify({
                'status': 'completed',
                'download_url': download_url
            })
        else:
            logger.error("Failed to generate download URL.")
            return jsonify({
                'status': 'failed',
                'error': 'Failed to generate download URL'
            }), 500

    return jsonify({
        'status': 'failed',
        'error': 'Failed to upload file to S3'
    }), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
