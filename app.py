from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
from elevenlabs.client import ElevenLabs
from werkzeug.utils import secure_filename

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
ELEVENLABS_API_KEY = "sk_f54ab3b3ee8672b1590d35ca9435f2154734869549b3e8f9"

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        if status.status == 'done':
            logger.info(f"Dubbing completed for ID: {dubbing_id}")
            download = client.dubbing.get_dubbed_file(dubbing_id)
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