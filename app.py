from flask import Flask, request, jsonify, render_template
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

voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
error-reporter-6be797dff3586e4ae63e-min.en-US.js:317 
        
        
       POST https://sentry.io/api/1363201/envelope/?sentry_key=5fa7b3ac571046d8a61aab5ff7649693&sentry_version=7&sentry_client=sentry.javascript.browser%2F7.105.0 net::ERR_BLOCKED_BY_CLIENT
a @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:317
j @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:330
f @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:350
m @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:330
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
Ge @ config-appshell-7896caa0689673eeb85a-min.en-US.js:22
rt @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
T @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
_sendEnvelope @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:318
_flushOutcomes @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
error-reporter-6be797dff3586e4ae63e-min.en-US.js:317 
        
        
       POST https://sentry.io/api/1363201/envelope/?sentry_key=5fa7b3ac571046d8a61aab5ff7649693&sentry_version=7&sentry_client=sentry.javascript.browser%2F7.105.0 net::ERR_BLOCKED_BY_CLIENT
a @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:317
j @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:330
f @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:350
m @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:330
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
Ge @ config-appshell-7896caa0689673eeb85a-min.en-US.js:22
rt @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
T @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
_sendEnvelope @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:318
_flushOutcomes @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
(anonymous) @ error-reporter-6be797dff3586e4ae63e-min.en-US.js:1
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)
(anonymous) @ voice:1343
setInterval
checkProgress @ voice:1339
startDubbing @ voice:1327
await in startDubbing
onclick @ voice:1265
voice:1343 
        
        
       GET https://dubbing-app.onrender.com/check-progress/UZYGzjrfqkOteYTUqNd4 500 (Internal Server Error)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))