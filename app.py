import os
import threading
import time
import logging
from flask import Flask, render_template, request, send_from_directory
from groq import Groq
from gtts import gTTS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure translations directory exists
os.makedirs('translations', exist_ok=True)

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Language configurations
LANGUAGES = [
    ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'), ('it', 'Italian'), 
    ('ja', 'Japanese'), ('ko', 'Korean'), ('zh', 'Chinese'), ('ru', 'Russian'), 
    ('ar', 'Arabic'), ('hi', 'Hindi'), ('pt', 'Portuguese'), ('nl', 'Dutch'), 
    ('sv', 'Swedish'), ('pl', 'Polish'), ('tr', 'Turkish'), ('vi', 'Vietnamese'), 
    ('th', 'Thai'), ('el', 'Greek'), ('he', 'Hebrew'), ('id', 'Indonesian')
]

def create_groq_client():
    """
    Create Groq client with error handling and proxy support
    """
    try:
        # Get optional proxy settings from environment
        http_proxy = os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('HTTPS_PROXY')
        
        # Prepare proxy configuration
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        # Create client with or without proxies
        client = Groq(
            api_key=GROQ_API_KEY,
            **({"proxies": proxies} if proxies else {})
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing Groq client: {e}")
        return None

def cleanup_translations():
    """Periodically delete all files in the translations directory"""
    while True:
        time.sleep(3600)
        try:
            for filename in os.listdir('translations'):
                file_path = os.path.join('translations', filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def translate_and_generate_audio(sentence, client):
    """Translate sentence and generate audio for multiple languages"""
    if not client:
        logger.error("Groq client not initialized")
        return []
    
    translations = []
    
    for lang_code, lang_name in LANGUAGES:
        try:
            # Updated prompt to get only the translated text
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Translate the following text precisely. Provide ONLY the translation without any additional explanation."},
                    {"role": "user", "content": f"Translate '{sentence}' to {lang_name}"}
                ],
                model="mixtral-8x7b-32768"
            )
            
            # Extract translated text (trimmed to remove any potential extra context)
            translation = chat_completion.choices[0].message.content.strip().strip('"')
            
            # Generate text-to-speech MP3
            tts = gTTS(text=translation, lang=lang_code)
            
            # Create filename
            filename = f'translation_{lang_code}.mp3'
            filepath = os.path.join('translations', filename)
            tts.save(filepath)
            
            translations.append({
                'language_code': lang_code,
                'language_name': lang_name,
                'translation': translation,
                'audio_file': filename
            })
        
        except Exception as e:
            logger.error(f"Error processing {lang_name}: {e}")
    
    return translations

@app.route('/', methods=['GET', 'POST'])
def index():
    translations = []
    input_sentence = ''
    
    if request.method == 'POST':
        input_sentence = request.form.get('sentence', '')
        
        if input_sentence:
            # Create Groq client
            client = create_groq_client()
            
            # Generate translations and audio
            translations = translate_and_generate_audio(input_sentence, client)
    
    return render_template('index.html', 
                           translations=translations, 
                           input_sentence=input_sentence)

@app.route('/translations/<filename>')
def serve_translation(filename):
    return send_from_directory('translations', filename)

if __name__ == '__main__':
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_translations, daemon=True)
    cleanup_thread.start()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))