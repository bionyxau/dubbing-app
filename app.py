from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from elevenlabs.client import ElevenLabs
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "OPTIONS"]}})

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
            with open(filepath, 'rb') as audio_file:
                response = client.dubbing.dub_a_video_or_an_audio_file(
                    file=(filename, audio_file, request.form.get('format', 'audio/mpeg')),
                    target_lang=request.form.get('target_language'),
                    source_lang=request.form.get('source_language'),
                    num_speakers=int(request.form.get('num_speakers', 1))
                )
            return jsonify({
                'dubbing_id': response.dubbing_id,
                'status': 'processing'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.remove(filepath)
            
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))