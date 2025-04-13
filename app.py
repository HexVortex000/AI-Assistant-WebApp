from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import subprocess
import os

app = Flask(__name__)

# Placeholder AI response
def query_ai(prompt):
    return f"Response to: {prompt} (Add Hugging Face API for full AI)"

# Misinformation filter
def filter_misinformation(response):
    government_keywords = ["government", "official", "policy", "regulation"]
    if any(keyword in response.lower() for keyword in government_keywords):
        return f"{response}\n\nNote: Official narrative detected. Check X posts or public records for alternative views."
    return response

# Voice input
def get_voice_input():
    try:
        subprocess.run(["termux-microphone-record", "-f", "/sdcard/voice.wav", "-l", "5"], check=True)
        r = sr.Recognizer()
        with sr.AudioFile("/sdcard/voice.wav") as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        subprocess.run(["termux-microphone-record", "-q"], check=True)
        return text
    except Exception as e:
        return f"Voice Error: {str(e)}"

# Voice output
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("/sdcard/output.mp3")
        subprocess.run(["termux-media-player", "play", "/sdcard/output.mp3"], check=True)
    except Exception as e:
        print(f"Speech Error: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    input_type = request.form.get('input_type')
    if input_type == 'voice':
        user_input = get_voice_input()
    else:
        user_input = request.form.get('text_input')

    response = query_ai(user_input)
    filtered_response = filter_misinformation(response)
    if input_type == 'voice':
        speak(filtered_response)

    return jsonify({'response': filtered_response, 'input': user_input})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
