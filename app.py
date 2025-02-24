from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import os
import platform
import pyttsx3  # Backup TTS
import google.generativeai as genai
import requests
import webbrowser

# Flask app setup
app = Flask(__name__)  # ✅ Fixed __name__
CORS(app)  # Enable CORS for API requests

# Set Gemini API key
genai.configure(api_key="AIzaSyBTxpFrER0nGFSGiCwFm4tE9cbbBMfg_g8")

# Initialize TTS (Text-to-Speech) based on OS
if platform.system() == "Windows":
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        win32_tts = True
    except Exception:
        speaker = pyttsx3.init()
        win32_tts = False
else:  # Linux (Render) fallback
    speaker = pyttsx3.init()
    win32_tts = False

# Global variable to track listening state
listening_active = True  # Starts in listening mode

# Function to handle speaking
def speak(text):
    print(f"Atmos: {text}")  # Debugging log
    speaker.say(text)
    speaker.runAndWait()

# Function to query Gemini API
def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text if response else "I couldn't generate a response."
    except Exception as e:
        return f"Gemini API error: {e}"

# Function to recognize speech input
def recognize_speech():
    global listening_active
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if not listening_active:
            return "Listening is disabled."
        speak("I'm listening...")
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            print("Recognizing...")
            command = recognizer.recognize_google(audio, language="en-IN").lower()
            print(f"Recognized: {command}")
            return command
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError as e:
            return f"Speech recognition error: {e}"

# Function to execute tasks
def execute_task(command):
    if "weather" in command:
        speak("For which city do you want to know the weather?")
        city = recognize_speech()
        response = get_weather(city)
    elif "open youtube" in command:
        speak("What would you like to search for?")
        search_query = recognize_speech()
        url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        webbrowser.open(url)
        response = f"Searching YouTube for {search_query}."
    elif "shutdown" in command:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
        response = "System shutdown initiated."
    elif "restart" in command:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
        response = "System restart initiated."
    else:
        response = ask_gemini(command)
    
    speak(response)  # 🔥 Now Atmos speaks the response! 🔊
    return response

# Function to get weather
def get_weather(city="Delhi"):
    api_key = "bd5e378503939ddaee76f12ad7a97608"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"]
            return f"The temperature in {city} is {temp}°C with {description}."
        return f"Could not fetch weather data."
    except Exception as e:
        return f"Weather API error: {e}"

# API to handle text-based Atmos requests
@app.route("/api/atmos", methods=["POST"])
def atmos_response():
    data = request.get_json()
    command = data.get("command", "")
    if not command:
        return jsonify({"error": "No command provided"}), 400
    response = execute_task(command)
    return jsonify({"response": response})

# API to handle voice commands
@app.route("/api/listen", methods=["GET"])
def listen():
    global listening_active
    if listening_active:
        command = recognize_speech()
        response = execute_task(command)
        return jsonify({"command": command, "response": response})
    else:
        return jsonify({"command": "", "response": "Listening is turned off."})

# API to toggle listening state
@app.route("/api/toggle_listen", methods=["POST"])
def toggle_listening():
    global listening_active
    listening_active = not listening_active
    state = "on" if listening_active else "off"
    return jsonify({"message": f"Listening turned {state}."})

# API to stop execution
@app.route("/api/stop", methods=["POST"])
def stop_execution():
    global listening_active
    listening_active = False
    return jsonify({"message": "Listening stopped."})

# Run the app using Gunicorn in Render
if __name__ == "__main__":  # ✅ Fixed __name__
    print("Atmos Assistant is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
