from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
from elevenlabs.client import ElevenLabs
from werkzeug.utils import secure_filename

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

# Folder settings
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
ELEVENLABS_API_KEY = "sk_f54ab3b3ee8672b1590d35ca9435f2154734869549b3e8f9"

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/dub', methods=['POST'])
def dub_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Open the uploaded file and send it to ElevenLabs for dubbing
            with open(filepath, 'rb') as audio_file:
                response = client.dubbing.dub_a_video_or_an_audio_file(
                    file=(filename, audio_file, request.form.get('format', 'audio/mpeg')),
                    target_lang=request.form.get('target_language'),
                    source_lang=request.form.get('source_language'),
                    num_speakers=int(request.form.get('num_speakers', 1))
                )
                
            # Validate that the response contains audio data
            if hasattr(response, 'audio_data') and response.audio_data:
                # Save the processed file to the 'processed' folder
                processed_filename = f"processed_{filename}"
                processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
                
                with open(processed_filepath, 'wb') as f:
                    f.write(response.audio_data)  # Assuming the response contains the processed audio data.
                
                # Generate a URL for the processed file
                file_url = f"/download/{processed_filename}"

                return jsonify({
                    'dubbing_id': response.dubbing_id,
                    'status': 'processing',
                    'file_url': file_url
                })
            else:
                return jsonify({'error': 'No audio data returned from dubbing service'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Remove the original file after processing
            os.remove(filepath)
            
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    # Ensure the file exists before attempting to download it
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
