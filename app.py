from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from elevenlabs.client import ElevenLabs
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import ClientError
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
from pydub import AudioSegment
import io
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from collections import deque
import psutil

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Monitoring System
class AppMonitor:
    def __init__(self):
        self.process_times = deque(maxlen=100)  # Last 100 processing times
        self.concurrent_processes = 0
        self.daily_process_count = 0
        self.error_count = 0
        self.total_requests = 0
        self.lock = threading.Lock()
        
        # Thresholds
        self.MEMORY_THRESHOLD = 80  # 80% RAM usage
        self.CONCURRENT_THRESHOLD = 3  # 3 concurrent processes
        self.DAILY_PROCESS_THRESHOLD = 45  # 45 processes per day
        self.ERROR_RATE_THRESHOLD = 5  # 5% error rate
        
        # Start daily reset thread
        self.start_daily_reset()

    def start_process(self):
        with self.lock:
            self.concurrent_processes += 1
            self.daily_process_count += 1
            self.total_requests += 1
            self.check_thresholds()

    def end_process(self, processing_time):
        with self.lock:
            self.concurrent_processes -= 1
            self.process_times.append(processing_time)

    def log_error(self):
        with self.lock:
            self.error_count += 1
            self.check_error_rate()

    def get_error_rate(self):
        if self.total_requests == 0:
            return 0
        return (self.error_count / self.total_requests) * 100

    def check_thresholds(self):
        alerts = []
        
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.MEMORY_THRESHOLD:
            alerts.append(f"Memory usage is at {memory_percent}%")

        # Check concurrent processes
        if self.concurrent_processes >= self.CONCURRENT_THRESHOLD:
            alerts.append(f"Concurrent processes: {self.concurrent_processes}")

        # Check daily process count
        if self.daily_process_count >= self.DAILY_PROCESS_THRESHOLD:
            alerts.append(f"Daily process count: {self.daily_process_count}")

        if alerts:
            self.send_alert_email(alerts)

    def check_error_rate(self):
        error_rate = self.get_error_rate()
        if error_rate > self.ERROR_RATE_THRESHOLD:
            self.send_alert_email([f"Error rate has reached {error_rate:.1f}%"])

    def send_alert_email(self, alerts):
        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('SMTP_USERNAME')
            msg['To'] = os.getenv('ADMIN_EMAIL')
            msg['Subject'] = "⚠️ Dubbing App Alert - Upgrade May Be Needed"

            body = f"""
            Hello,

            Your dubbing application has reached some important thresholds:

            {chr(10).join('- ' + alert for alert in alerts)}

            Current Statistics:
            - Memory Usage: {psutil.virtual_memory().percent}%
            - Concurrent Processes: {self.concurrent_processes}
            - Daily Process Count: {self.daily_process_count}
            - Error Rate: {self.get_error_rate():.1f}%
            - Average Processing Time: {self.get_average_process_time():.1f} seconds

            Consider upgrading from the free tier to ensure stable service.

            Best regards,
            Your Monitoring System
            """

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(os.getenv('SMTP_SERVER', 'smtp.gmail.com'), 
                            int(os.getenv('SMTP_PORT', '587'))) as server:
                server.starttls()
                server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")

    def get_average_process_time(self):
        if not self.process_times:
            return 0
        return sum(self.process_times) / len(self.process_times)

    def start_daily_reset(self):
        def reset_daily_counts():
            while True:
                now = datetime.now()
                next_reset = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                time_to_wait = (next_reset - now).total_seconds()
                threading.Event().wait(timeout=time_to_wait)
                
                with self.lock:
                    self.daily_process_count = 0
                    self.error_count = 0
                    self.total_requests = 0

        thread = threading.Thread(target=reset_daily_counts, daemon=True)
        thread.start()

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

# Initialize AWS S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize monitoring
monitor = AppMonitor()

# Helper functions (keeping your existing ones)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def add_silence_to_audio(audio_file, silence_duration=750, trim_duration=250):
    try:
        if audio_file.filename.lower().endswith('.mp4'):
            audio = AudioSegment.from_file(audio_file, format="mp4")
        else:
            audio = AudioSegment.from_file(audio_file)

        silence = AudioSegment.silent(duration=silence_duration)
        padded_audio = silence + audio
        
        temp_padded = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1])
        padded_audio.export(temp_padded.name, format=os.path.splitext(audio_file.filename)[1][1:])
        
        padded_file = AudioSegment.from_file(temp_padded.name)
        final_audio = padded_file[trim_duration:]

        temp_final = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1])
        final_audio.export(temp_final.name, format=os.path.splitext(audio_file.filename)[1][1:])
        
        if os.path.exists(temp_padded.name):
            os.remove(temp_padded.name)
            
        return temp_final.name
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return None

def store_file_s3(file_content, s3_key, original_filename):
    try:
        response = s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            Metadata={'original-filename': original_filename}
        )
        return True
    except ClientError as e:
        logger.error(f"S3 ClientError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in S3 upload: {str(e)}")
        return False

def generate_presigned_url(s3_key, original_filename):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': f'attachment; filename="{original_filename}"'
            },
            ExpiresIn=3600
        )
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None

# Routes with monitoring
@app.route('/dub', methods=['POST'])
def dub_audio():
    start_time = datetime.now()
    monitor.start_process()
    
    try:
        if 'file' not in request.files:
            monitor.log_error()
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            monitor.log_error()
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            processed_filepath = None
            
            try:
                processed_filepath = add_silence_to_audio(file)
                
                if not processed_filepath:
                    monitor.log_error()
                    return jsonify({'error': 'Failed to process audio file'}), 500

                with open(processed_filepath, 'rb') as audio_file:
                    response = client.dubbing.dub_a_video_or_an_audio_file(
                        file=(original_filename, audio_file, request.form.get('format', 'audio/mpeg')),
                        target_lang=request.form.get('target_language'),
                        source_lang=request.form.get('source_language'),
                        num_speakers=int(request.form.get('num_speakers', 1))
                    )
                    
                    process_time = (datetime.now() - start_time).total_seconds()
                    monitor.end_process(process_time)
                    
                    return jsonify({
                        'dubbing_id': response.dubbing_id,
                        'status': 'processing',
                        'original_filename': original_filename
                    })
            except Exception as e:
                monitor.log_error()
                logger.error(f"Error during dubbing: {str(e)}", exc_info=True)
                return jsonify({'error': str(e)}), 500
            finally:
                if processed_filepath and os.path.exists(processed_filepath):
                    os.remove(processed_filepath)
                
        monitor.log_error()
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        monitor.log_error()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/check-progress/<dubbing_id>', methods=['GET'])
def check_progress(dubbing_id):
    try:
        original_filename = request.args.get('original_filename')
        if not original_filename:
            logger.warning("No original filename provided")
            original_filename = f"dubbed_{dubbing_id}"
        
        status_url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}"
        
        status_response = requests.get(
            status_url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Accept": "application/json"
            }
        )
        
        if not status_response.ok:
            monitor.log_error()
            return jsonify({
                'status': 'failed',
                'error': f"ElevenLabs API error: {status_response.text}"
            }), 500
            
        elif status_data['status'] == 'error':
            monitor.log_error()
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
        monitor.log_error()
        logger.error(f"Unexpected error in check_progress: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'failed',
            'error': f"Server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))500
            
        status_data = status_response.json()
        
        if 'status' not in status_data:
            monitor.log_error()
            return jsonify({
                'status': 'failed',
                'error': 'Invalid response from ElevenLabs API'
            }), 500

        if status_data['status'] == 'dubbed':
            if not status_data.get('target_languages'):
                monitor.log_error()
                return jsonify({
                    'status': 'failed',
                    'error': 'No target language available'
                }), 500
                
            target_lang = status_data['target_languages'][0]
            download_url = f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}/audio/{target_lang}"
            
            download_response = requests.get(
                download_url,
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                stream=True
            )
            
            if download_response.status_code != 200:
                monitor.log_error()
                return jsonify({
                    'status': 'failed',
                    'error': 'Failed to download dubbed file'
                }), 500

            content_type = download_response.headers.get('content-type', '')
            extension = 'mp4' if 'video' in content_type else 'mp3'
            base_filename = os.path.splitext(original_filename)[0]
            new_filename = f"{base_filename}_{target_lang}.{extension}"
            s3_filename = f"Eleven-Labs/{dubbing_id}/{new_filename}"
            
            if store_file_s3(download_response.content, s3_filename, new_filename):
                download_url = generate_presigned_url(s3_filename, new_filename)
                if download_url:
                    return jsonify({
                        'status': 'completed',
                        'download_url': download_url,
                        'filename': new_filename
                    })
                
            monitor.log_error()
            return jsonify({
                'status': 'failed',
                'error': 'Failed to process dubbed file'
            }),