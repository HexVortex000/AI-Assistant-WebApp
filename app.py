from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import subprocess
import os
import requests
import time
import logging
import random

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set Hugging Face API token from environment variable
HF_TOKEN = os.getenv('HF_TOKEN')
if not HF_TOKEN:
    logging.error("HF_TOKEN environment variable not set")
    raise ValueError("HF_TOKEN environment variable not set")

def query_ai(prompt):
    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.post(
                "[invalid url, do not cite]",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": prompt}
            )
            response.raise_for_status()  # Raise exception for bad status
            logging.info(f"AI query successful for prompt: {prompt}")
            return response.json()[0]["generated_text"]
        except Exception as e:
            logging.warning(f"AI query attempt failed: {str(e)}")
            continue
    logging.error("AI query failed after retries")
    return "AI Error: Failed after retries"

def filter_misinformation(response):
    government_keywords = ["government", "official", "policy", "regulation", "authority", "state", "agency"]
    if any(keyword in response.lower() for keyword in government_keywords):
        with open("filter_log.txt", "a") as f:
            f.write(f"Response: {response}\nNote: Official narrative detected\n\n")
        logging.info("Misinformation filter triggered")
        return f"{response}\n\nAlternative: Search X for #UnfilteredTruth or archives like Wikileaks."
    return response

def get_voice_input():
    for _ in range(3):  # Retry up to 3 times
        filename = f"/sdcard/voice_{int(time.time())}_{random.randint(1, 10000)}.wav"  # More unique filename
        try:
            if os.path.exists(filename):
                os.remove(filename)  # Delete if exists
            subprocess.run(["termux-microphone-record", "-f", filename, "-l", "5"], check=True)
            r = sr.Recognizer()
            with sr.AudioFile(filename) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            subprocess.run(["termux-microphone-record", "-q"], check=True)
            os.remove(filename)  # Clean up after use
            logging.info("Voice input successful")
            return text
        except Exception as e:
            logging.warning(f"Voice input attempt failed: {str(e)}")
            continue
    logging.error("Voice input failed after retries")
    return "Voice Error: Failed after retries"

def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        output_file = "/sdcard/output.mp3"
        tts.save(output_file)
        subprocess.run(["termux-media-player", "play", output_file], check=True)
        logging.info("Speech output successful")
    except Exception as e:
        logging.error(f"Speech Error: {str(e)}")
        print(f"Speech Error: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    try:
        input_type = request.form.get('input_type')
        if input_type == 'voice':
            user_input = get_voice_input()
        else:
            user_input = request.form.get('text_input')

        if not user_input:
            logging.warning("Empty input received")
            return jsonify({'response': 'Error: No input provided', 'input': ''})

        response = query_ai(user_input)
        filtered_response = filter_misinformation(response)
        if input_type == 'voice':
            speak(filtered_response)

        logging.info(f"Query processed: input={user_input}, response={filtered_response}")
        return jsonify({'response': filtered_response, 'input': user_input})
    except Exception as e:
        logging.error(f"Query processing failed: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}", 'input': ''})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
