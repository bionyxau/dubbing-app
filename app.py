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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Updated CORS settings
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Constants
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4'}
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

@app.after_request
def after_request(response):
    # Add your website to allowed origins
    response.headers.add('Access-Control-Allow-Origin', 'https://www.bionyx.au')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def store_file_s3(file_content, s3_key):
    """Store the file in S3"""
    try:
        logger.info(f"Storing file in S3: {s3_key}")
        content_type = 'video/mp4' if s3_key.endswith('.mp4') else 'audio/mpeg'
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        logger.info(f"Successfully stored file in S3: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Error storing file in S3: {e}")
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
                    return jsonify({
                        'dubbing_id': response.dubbing_id,
                        'status': 'processing'
                    })
            except Exception as e:
                logger.error(f"Error during dubbing: {str(e)}")
                return jsonify({'error': str(e)}), 500
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Cleaned up file: {filepath}")
                
        logger.error("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check-progress/<dubbing_id>', methods=['GET'])
def check_progress(dubbing_id):
    try:
        logger.info(f"Checking progress for dubbing ID: {dubbing_id}")

        # Use the correct API endpoint with proper authentication
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Accept": "application/json"
        }
        
        # Using ElevenLabs client instead of direct API call
        response = client.dubbing.get_dubbing_metadata(dubbing_id=dubbing_id)
        logger.info(f"Status received: {response}")
        
        if response.status == 'done':
            logger.info(f"Dubbing completed for ID: {dubbing_id}")
            
            # Get the dubbed audio using the client
            download_response = requests.get(
                f"{ELEVENLABS_API_BASE}/v1/dubbing/{dubbing_id}/audio/{response.target_languages[0]}",
                headers=headers
            )
            
            if download_response.status_code == 200:
                # Generate unique filename with extension based on content type
                content_type = download_response.headers.get('content-type', '')
                logger.info(f"Content Type received: {content_type}")
                
                extension = 'mp4' if 'video' in content_type else 'mp3'
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_filename = f"Eleven-Labs/dubbed_{dubbing_id}_{timestamp}.{extension}"
                
                logger.info(f"Attempting to store file in S3 with filename: {s3_filename}")
                
                # Store in S3
                if store_file_s3(download_response.content, s3_filename):
                    download_url = generate_presigned_url(s3_filename)
                    if download_url:
                        logger.info(f"Generated presigned URL: {download_url}")
                        return jsonify({
                            'status': 'completed',
                            'download_url': download_url
                        })
                    
                logger.error("Failed to generate download URL")
                return jsonify({
                    'status': 'failed',
                    'error': 'Failed to generate download URL'
                }), 500
            
            logger.error(f"Failed to download dubbed file: {download_response.status_code}")
            return jsonify({
                'status': 'failed',
                'error': 'Failed to download dubbed file'
            }), 500
            
        elif response.status == 'error':
            return jsonify({
                'status': 'failed',
                'error': getattr(response, 'error', 'Dubbing failed')
            })
        else:
            return jsonify({
                'status': 'processing',
                'progress': getattr(response, 'progress', 0)
            })
    
    except Exception as e:
        logger.error(f"Error checking progress: {str(e)}")
        return jsonify({
            'status': 'failed',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))