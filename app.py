import os
from dotenv import load_dotenv
import streamlit as st
from groq import Groq
from gtts import gTTS

# Load environment variables from .env file
load_dotenv()

def translate_and_speak(sentence: str, api_key: str, num_languages: int = 40, output_dir: str = 'translations'):
    """
    Translate a sentence into multiple languages using Groq API and generate MP3 audio files.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
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
    
    for i, (lang_code, lang_name) in enumerate(LANGUAGES[:num_languages]):
        try:
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
            
            # Generate text-to-speech MP3
            tts = gTTS(text=translation, lang=lang_code)
            
            # Create filename
            filename = os.path.join(output_dir, f'translation_{lang_code}.mp3')
            tts.save(filename)
            
            # Store translation details
            translations.append({
                'language_name': lang_name,
                'language_code': lang_code,
                'translation': translation,
                'audio_file': filename
            })
            
            # Update progress bar
            progress_bar.progress((i + 1) / num_languages)
        
        except Exception as e:
            st.error(f"Error processing {lang_name} ({lang_code}): {e}")
    
    progress_bar.empty()
    return translations

def main():
    st.set_page_config(page_title="MultiLingual Translator", page_icon="🌍")
    
    st.title("🌍 MultiLingual Translator")
    
    # Retrieve API Key from environment variable
    default_api_key = os.getenv('GROQ_API_KEY', '')
    
    # API Key Input with default from .env
    api_key = st.text_input("Enter Groq API Key", value=default_api_key, type="password")
    
    # Sentence Input
    sentence = st.text_area("Enter sentence to translate", height=150)
    
    # Language Selection
    num_languages = st.slider("Number of Languages", min_value=5, max_value=40, value=20)
    
    # Translate Button
    if st.button("Translate & Generate Audio"):
        if not api_key:
            st.error("Please enter a Groq API Key")
            return
        
        if not sentence:
            st.error("Please enter a sentence to translate")
            return
        
        # Perform Translation
        with st.spinner('Translating and generating audio...'):
            translations = translate_and_speak(sentence, api_key, num_languages)
        
        # Display Results
        st.success(f"Translations generated for {len(translations)} languages!")
        
        # Create Expander for Translations
        with st.expander("View Translations"):
            for translation in translations:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{translation['language_name']}**: {translation['translation']}")
                with col2:
                    # Read audio file
                    with open(translation['audio_file'], 'rb') as audio_file:
                        st.audio(audio_file.read(), format='audio/mp3')

if __name__ == "__main__":
    main()