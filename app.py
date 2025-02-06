from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from elevenlabs.client import ElevenLabs
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import ClientError
import requests
from datetime import datetime
from urllib.parse import urljoin

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Updated CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ["https://www.bionyx.au"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Constants
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4'}
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'

# S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def store_file_s3(file_content, s3_key):
    """Store the file in S3"""
    try:
        logger.info(f"Starting S3 upload for key: {s3_key}")
        logger.info(f"Content length: {len(file_content)}")
        
        content_type = 'video/mp4' if s3_key.endswith('.mp4') else 'audio/mpeg'
        logger.info(f"Content type determined: {content_type}")
        
        response = s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        logger.info(f"S3 upload response: {response}")
        return True
    except ClientError as e:
        logger.error(f"S3 ClientError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in S3 upload: {str(e)}")
        return False

def generate_presigned_url(s3_key):
    """Generate a presigned URL for file download"""
    try:
        logger.info(f"Generating presigned URL for: {s3_key}")
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': 'attachment'
            },
            ExpiresIn=3600
        )
        logger.info(f"Generated presigned URL successfully")
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None

@app.route('/dub', methods=['POST'])
def dub_audio():
    try:
        logger.info("Received dubbing request")
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            logger.info(f"Saving file to {filepath}")
            file.save(filepath)
            
            try:
                with open(filepath, 'rb') as audio_file:
                    logger.info("Starting dubbing process")
                    response = client.dubbing.dub_a_video_or_an_audio_file(
                        file=(filename, audio_file, request.form.get('format', 'audio/mpeg')),
                        target_lang=request.form.get('target_language'),
                        source_lang=request.form.get('source_language'),
                        num_speakers=int(request.form.get('num_speakers', 1))
                    )
                    logger.info(f"Dubbing initiated with ID: {response.dubbing_id}")
                    
                    # Store the original filename in the response
                    return jsonify({
                        'dubbing_id': response.dubbing_id,
                        'status': 'processing',
                        'original_filename': filename
                    })
            except Exception as e:
                logger.error(f"Error during dubbing: {str(e)}", exc_info=True)
                return jsonify({'error': str(e)}), 500
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Cleaned up file: {filepath}")
                
        logger.error("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/check-progress/<dubbing_id>', methods=['GET'])
def check_progress(dubbing_id):
    try:
        logger.info(f"Checking progress for dubbing ID: {dubbing_id}")

        # Get dubbing status
        status_url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}"
        logger.info(f"Requesting status from: {status_url}")
        
        status_response = requests.get(
            status_url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Accept": "application/json"
            }
        )
        
        # Log the response for debugging
        logger.info(f"Status response code: {status_response.status_code}")
        logger.info(f"Status response headers: {dict(status_response.headers)}")
        
        if not status_response.ok:
            logger.error(f"Error response from ElevenLabs: {status_response.text}")
            return jsonify({
                'status': 'failed',
                'error': f"ElevenLabs API error: {status_response.text}"
            }), 500
            
        status_data = status_response.json()
        logger.info(f"Status data received: {status_data}")
        
        # Check if we have a valid status
        if 'status' not in status_data:
            logger.error(f"Invalid status data received: {status_data}")
            return jsonify({
                'status': 'failed',
                'error': 'Invalid response from ElevenLabs API'
            }), 500

        if status_data['status'] == 'dubbed':  # Changed from 'done' to 'dubbed'
            logger.info("Dubbing status is dubbed, proceeding to download")
            
            # Get the target language
            if not status_data.get('target_languages'):
                logger.error("No target languages found in response")
                return jsonify({
                    'status': 'failed',
                    'error': 'No target language available'
                }), 500
                
            target_lang = status_data['target_languages'][0]
            
            # Get the dubbed audio
            download_url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}/audio/{target_lang}"
            logger.info(f"Attempting to download from: {download_url}")
            
            download_response = requests.get(
                download_url,
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                stream=True  # Stream the response to handle large files
            )
            
            if download_response.status_code != 200:
                logger.error(f"Download failed: {download_response.text}")
                return jsonify({
                    'status': 'failed',
                    'error': 'Failed to download dubbed file'
                }), 500

            # Process the downloaded file
            content_type = download_response.headers.get('content-type', '')
            extension = 'mp4' if 'video' in content_type else 'mp3'
            
            # Attempt to get original filename from request headers or query parameters
            original_filename = request.args.get('original_filename', '')
            if not original_filename:
                original_filename = f'dubbed_{dubbing_id}'
            
            # Remove the extension if present
            original_filename = os.path.splitext(original_filename)[0]
            
            # Create new filename with target language
            s3_filename = f"Eleven-Labs/{original_filename}_{target_lang}.{extension}"
            
            logger.info(f"Using original filename: {original_filename} for S3 upload")
            logger.info(f"Uploading to S3: {s3_filename}")
            
            if store_file_s3(download_response.content, s3_filename):
                download_url = generate_presigned_url(s3_filename)
                if download_url:
                    return jsonify({
                        'status': 'completed',
                        'download_url': download_url
                    })
                
            logger.error("Failed to generate download URL")
            return jsonify({
                'status': 'failed',
                'error': 'Failed to process dubbed file'
            }), 500
            
        elif status_data['status'] == 'error':
            logger.error(f"Dubbing error: {status_data.get('error', 'Unknown error')}")
            return jsonify({
                'status': 'failed',
                'error': status_data.get('error', 'Dubbing failed')
            })
        else:
            # Processing or other status
            return jsonify({
                'status': 'processing',
                'progress': status_data.get('progress', 0)
            })
    
    except Exception as e:
        logger.error(f"Unexpected error in check_progress: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'failed',
            'error': f"Server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))