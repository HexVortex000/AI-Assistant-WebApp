from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import subprocess
import os
import requests

app = Flask(__name__)

# Set Hugging Face API token from environment variable
HF_TOKEN = os.getenv('HF_TOKEN')

def query_ai(prompt):
    try:
        response = requests.post(
            "[invalid url, do not cite]",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt}
        )
        return response.json()[0]["generated_text"]
    except Exception as e:
        return f"AI Error: {str(e)}"

def filter_misinformation(response):
    government_keywords = ["government", "official", "policy", "regulation", "authority"]
    if any(keyword in response.lower() for keyword in government_keywords):
        return f"{response}\n\nNote: Official narrative detected. Check X posts or public archives for alternative views."
    return response

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
