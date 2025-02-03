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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Updated CORS settings
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://platinum-octahedron-wm3l.squarespace.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def store_file_s3(file_content, filename):
    """Store the audio file in S3"""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType='audio/mpeg'
        )
        return True
    except ClientError as e:
        logger.error(f"Error storing file in S3: {e}")
        return False

def generate_presigned_url(filename, expiration=3600):
    """Generate a presigned URL for file download"""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': filename
            },
            ExpiresIn=expiration
        )
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
        status = client.dubbing.get_dubbing_status(dubbing_id)
        logger.info(f"Status received: {status.status}, Progress: {status.progress}")
        
        if status.status == 'done':
            logger.info(f"Dubbing completed for ID: {dubbing_id}")
            download = client.dubbing.get_dubbed_file(dubbing_id)
            logger.info(f"Got download URL from ElevenLabs: {download.download_url}")
            
            # Download the file from ElevenLabs
            response = requests.get(download.download_url)
            logger.info(f"Download response status: {response.status_code}")
            
            if response.status_code == 200:
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_filename = f"dubbed_audio_{dubbing_id}_{timestamp}.mp3"
                logger.info(f"Generated S3 filename: {s3_filename}")
                
                try:
                    # Store in S3
                    if store_file_s3(response.content, s3_filename):
                        logger.info(f"Successfully stored file in S3: {s3_filename}")
                        # Generate presigned URL
                        download_url = generate_presigned_url(s3_filename)
                        logger.info(f"Generated presigned URL: {download_url}")
                        return jsonify({
                            'status': 'completed',
                            'download_url': download_url,
                            'original_url': download.download_url
                        })
                    else:
                        logger.error("Failed to store file in S3")
                except Exception as e:
                    logger.error(f"Error during S3 operations: {str(e)}")
                    # Fallback to original URL
                    return jsonify({
                        'status': 'completed',
                        'download_url': download.download_url
                    })
            else:
                logger.error(f"Failed to download file from ElevenLabs: {response.status_code}")
            
            # Fallback to original URL
            return jsonify({
                'status': 'completed',
                'download_url': download.download_url
            })
            
        elif status.status == 'error':
            logger.error(f"Dubbing failed for ID: {dubbing_id}")
            return jsonify({
                'status': 'failed',
                'error': 'Dubbing failed'
            })
        else:
            logger.info(f"Dubbing in progress for ID: {dubbing_id}, progress: {status.progress}")
            return jsonify({
                'status': 'processing',
                'progress': status.progress
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