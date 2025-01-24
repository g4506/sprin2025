from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, flash
import os

# Google Cloud libraries for Speech-to-Text and Text-to-Speech
from google.cloud import speech
from google.cloud import texttospeech_v1
from google.protobuf import wrappers_pb2




app = Flask(__name__)



# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Google Cloud clients
speech_client = speech.SpeechClient()
text_to_speech_client = texttospeech_v1.TextToSpeechClient()

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to list files in the upload folder
def get_files():
    files = []
    tts_files= []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
    
    tts_folder = os.path.join(UPLOAD_FOLDER, 'tts')
    if os.path.exists(tts_folder):
        for filename in os.listdir(tts_folder):
            if allowed_file(filename):
                tts_files.append(f'tts/{filename}')
    
    files.sort(reverse=True)
    tts_files.sort(reverse=True)
    return files + tts_files

# Route to the home page
@app.route('/')
def index():
    files = get_files()
    return render_template('index.html', files=files)

# Route to upload audio
@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        # Generate a unique filename based on the current timestamp
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Call the Google Cloud Speech-to-Text API and save the transcript
        with open(file_path, 'rb') as f:
            audio_content = f.read()

        # Recognize speech
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            language_code="en-US",
            audio_channel_count=1,
            enable_word_confidence=True,
            enable_word_time_offsets=True,
        )
        operation = speech_client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=90)

        # Save the transcript
        transcript = "\n".join([result.alternatives[0].transcript for result in response.results])
        with open(file_path + '.txt', 'w') as f:
            f.write(transcript)

        return redirect('/')  # Redirect back to the index

# Route to serve the uploaded file
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
     #return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'tts'), filename)
# Route to upload text for TTS (Text-to-Speech)
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    
    # Call Google Cloud Text-to-Speech API
    synthesis_input = texttospeech_v1.SynthesisInput(text=text)
    voice = texttospeech_v1.VoiceSelectionParams(
        language_code="en-UK", ssml_gender=texttospeech_v1.SsmlVoiceGender.MALE
    )
    audio_config = texttospeech_v1.AudioConfig(audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16)
    
    response = text_to_speech_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Save the output audio to a file in the 'tts' folder
    tts_filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    tts_path = os.path.join(app.config['UPLOAD_FOLDER'], 'tts', tts_filename)
    os.makedirs(os.path.dirname(tts_path), exist_ok=True)

    with open(tts_path, 'wb') as out:
        out.write(response.audio_content)

    return redirect('/')  # Redirect to home page after saving

# Serve static JS file
@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_file('./script.js')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
