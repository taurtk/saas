import os
import threading
import time
from flask import Flask, render_template, request, send_from_directory
from groq import Groq
from gtts import gTTS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure translations directory exists
os.makedirs('translations', exist_ok=True)

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Raise error if API key is not set
if not GROQ_API_KEY:
    raise ValueError("No GROQ_API_KEY set. Please set it in .env file.")

# # Ensure translations directory exists
# os.makedirs('translations', exist_ok=True)

# # Groq API key
# GROQ_API_KEY = "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"

# Language configurations
LANGUAGES = [
    ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'), ('it', 'Italian'), 
    ('ja', 'Japanese'), ('ko', 'Korean'), ('zh', 'Chinese'), ('ru', 'Russian'), 
    ('ar', 'Arabic'), ('hi', 'Hindi'), ('pt', 'Portuguese'), ('nl', 'Dutch'), 
    ('sv', 'Swedish'), ('pl', 'Polish'), ('tr', 'Turkish'), ('vi', 'Vietnamese'), 
    ('th', 'Thai'), ('el', 'Greek'), ('he', 'Hebrew'), ('id', 'Indonesian'),
    ('da', 'Danish'), ('fi', 'Finnish'), ('no', 'Norwegian'), ('ro', 'Romanian'),
    ('hu', 'Hungarian'), ('cs', 'Czech'), ('sk', 'Slovak'), ('uk', 'Ukrainian'),
    ('bn', 'Bengali'), ('fa', 'Persian'), ('sr', 'Serbian'), ('hr', 'Croatian'),
    ('bg', 'Bulgarian'), ('ur', 'Urdu'), ('mr', 'Marathi'), ('ta', 'Tamil')
]

def cleanup_translations():
    """
    Periodically delete all files in the translations directory
    """
    while True:
        # Sleep for 1 hour
        time.sleep(3600)
        
        try:
            # Get the translations directory path
            translations_dir = 'translations'
            
            # Iterate and remove all files
            for filename in os.listdir(translations_dir):
                file_path = os.path.join(translations_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        except Exception as e:
            print(f"Cleanup error: {e}")

def translate_and_generate_audio(sentence, client):
    translations = []
    
    for lang_code, lang_name in LANGUAGES:
        try:
            # Translate using Groq API
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"Translate the following English sentence to {lang_name}:"},
                    {"role": "user", "content": sentence}
                ],
                model="mixtral-8x7b-32768"
            )
            
            # Extract translated text
            translation = chat_completion.choices[0].message.content
            
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
            print(f"Error processing {lang_name}: {e}")
    
    return translations

@app.route('/', methods=['GET', 'POST'])
def index():
    translations = []
    input_sentence = ''
    is_loading = False
    
    if request.method == 'POST':
        input_sentence = request.form.get('sentence', '')
        
        if input_sentence:
            try:
                is_loading = True
                # Initialize Groq client with minimal configuration
                client = Groq()
                client.api_key = GROQ_API_KEY
                
                # Generate translations and audio
                translations = translate_and_generate_audio(input_sentence, client)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
                return render_template('index.html', 
                                    translations=[], 
                                    input_sentence=input_sentence,
                                    error="An error occurred while processing your request.",
                                    is_loading=False)
    
    return render_template('index.html', 
                         translations=translations, 
                         input_sentence=input_sentence,
                         is_loading=is_loading)

@app.route('/translations/<filename>')
def serve_translation(filename):
    return send_from_directory('translations', filename)

if __name__ == '__main__':
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_translations, daemon=True)
    cleanup_thread.start()
    
    # Run the Flask app
    app.run(debug=True)