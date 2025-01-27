import os
import streamlit as st
from groq import Groq
from gtts import gTTS
import time

# Move page configuration to the top of the script
st.set_page_config(page_title="MultiLingual Translator", page_icon="🌍")

# Load secrets from Streamlit's secrets management
API_KEY = st.secrets["GROQ"]["API_KEY"]

# Initialize session state for translations
if 'translations' not in st.session_state:
    st.session_state.translations = []

def generate_audio_filename(lang_code: str, text: str) -> str:
    """Generate a meaningful filename for the audio file"""
    # Clean the text to create a safe filename
    safe_text = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_text = safe_text[:30]  # Limit length
    timestamp = int(time.time())
    return f"{safe_text}_{lang_code}_{timestamp}.mp3"

def translate_and_speak(sentence: str, num_languages: int = 40, output_dir: str = 'translations'):
    """
    Translate a sentence into multiple languages using Groq API and generate MP3 audio files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Groq client without any additional parameters
    try:
        client = Groq(api_key=API_KEY)  # Ensure this is the correct initialization
    except Exception as e:
        st.error(f"Failed to initialize Groq client: {e}")
        return []
    
    # Top 40 most spoken languages globally
    LANGUAGES = [
        ('zh', 'Chinese'), ('es', 'Spanish'), ('en', 'English'), ('hi', 'Hindi'), 
        ('ar', 'Arabic'), ('pt', 'Portuguese'), ('bn', 'Bengali'), ('ru', 'Russian'), 
        ('ja', 'Japanese'), ('pa', 'Punjabi'), ('de', 'German'), ('fr', 'French'), 
        ('it', 'Italian'), ('tr', 'Turkish'), ('ko', 'Korean'), ('vi', 'Vietnamese'), 
        ('ta', 'Tamil'), ('te', 'Telugu'), ('mr', 'Marathi'), ('ur', 'Urdu'), 
        ('gu', 'Gujarati'), ('th', 'Thai'), ('kn', 'Kannada'), ('ml', 'Malayalam'), 
        ('or', 'Odia'), ('ne', 'Nepali'), ('as', 'Assamese'), ('id', 'Indonesian'), 
        ('ms', 'Malay'), ('tl', 'Tagalog'), ('sw', 'Swahili'), ('am', 'Amharic'), 
        ('fa', 'Persian'), ('pl', 'Polish'), ('uk', 'Ukrainian'), ('nl', 'Dutch'), 
        ('ro', 'Romanian'), ('el', 'Greek'), ('he', 'Hebrew'), ('hu', 'Hungarian')
    ]
    
    translations = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (lang_code, lang_name) in enumerate(LANGUAGES[:num_languages]):
        try:
            status_text.text(f"Translating to {lang_name}...")
            
            # Use Groq API to translate
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Translate the following text precisely. Provide ONLY the translation without any additional explanation."},
                    {"role": "user", "content": f"Translate the English text: '{sentence}' to {lang_name}"}
                ],
                model="mixtral-8x7b-32768"
            )
            
            # Extract translated text
            translation = chat_completion.choices[0].message.content
            
            # Generate meaningful filename
            filename = generate_audio_filename(lang_code, sentence)
            filepath = os.path.join(output_dir, filename)
            
            # Generate text-to-speech MP3
            tts = gTTS(text=translation, lang=lang_code)
            tts.save(filepath)
            
            # Store translation details
            translations.append({
                'language_name': lang_name,
                'language_code': lang_code,
                'translation': translation,
                'audio_file': filename,
                'original_text': sentence[:30],
                'filepath': filepath  # Store full filepath
            })
            
            # Update progress bar
            progress_bar.progress((i + 1) / num_languages)
        
        except Exception as e:
            st.error(f"Error processing {lang_name} ({lang_code}): {e}")
    
    progress_bar.empty()
    status_text.empty()
    return translations

def display_translations(translations):
    """Display translations and audio files"""
    if not translations:
        return
    
    st.success(f"Translations available for {len(translations)} languages!")
    
    # Create Expander for Translations
    with st.expander("View Translations", expanded=True):
        for translation in translations:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{translation['language_name']}**: {translation['translation']}")
            with col2:
                # Read audio file
                if os.path.exists(translation['filepath']):
                    with open(translation['filepath'], 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format='audio/mp3')
                        
                        # Download button with meaningful filename
                        download_filename = f"{translation['original_text']}_{translation['language_name']}.mp3"
                        st.download_button(
                            label="Download MP3",
                            data=audio_bytes,
                            file_name=download_filename,
                            mime="audio/mp3",
                            key=f"download_{translation['language_code']}_{translation['original_text']}"
                        )

def main():
    st.title("🌍 MultiLingual Translator")
    
    # Sentence Input
    sentence = st.text_area("Enter sentence to translate", height=150)
    
    # Language Selection
    num_languages = st.slider("Number of Languages", min_value=5, max_value=40, value=20)
    
    # Translate Button
    if st.button("Translate & Generate Audio"):
        if not API_KEY:
            st.error("Groq API Key is not set in the environment.")
            return
        
        if not sentence:
            st.error("Please enter a sentence to translate")
            return
        
        # Perform Translation
        with st.spinner('Translating and generating audio...'):
            st.session_state.translations = translate_and_speak(sentence, num_languages)
    
    # Display translations (will persist across refreshes)
    display_translations(st.session_state.translations)

if __name__ == "__main__":
    main()