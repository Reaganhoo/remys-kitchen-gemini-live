# 🍳 Remy's Kitchen: AI Sous-Chef



Remy's Kitchen is an interactive, voice-controlled AI sous-chef built for the Gemini Live Agent Challenge. By combining the Gemini 2.5 Flash Multimodal Live API with the YouTube Data API, Remy can "watch" a cooking video, extract the recipe, and then guide you through the cooking process hands-free using real-time audio and vision.

<img width="610" height="654" alt="Screenshot 2026-03-11 231257" src="https://github.com/user-attachments/assets/f2ab8b04-18ad-4f64-9739-f9e5cf2651f8" />



## ✨ Features

- Recipe Extraction: Paste any YouTube URL to have Remy summarize ingredients and instructions.

- Gemini Live Multimodal: Uses the gemini-2.5-flash-native-audio-preview model for low-latency, natural voice conversation.

- Hands-Free Timer: Remy can set and stop kitchen timers via Tool Use (Function Calling).

- Real-time Vision: Share your webcam feed so Remy can see what you're cooking.

- Pastel UI: A clean, chef-friendly interface designed for the kitchen environment.



## 🛠️ Tech Stack

- Backend: FastAPI (Python)

- AI: Google GenAI SDK (Gemini Live API)

- Tools: YouTube Data API v3

- Frontend: Vanilla JS, HTML5 AudioWorklet (for PCM processing), WebSockets

- Deployment: Docker / Google Cloud Run



## 🚀 Spin-up Instructions

1. Prerequisites
   - Google AI Studio API Key: Get it from [aistudio.google.com](https://aistudio.google.com/api-keys)
   - YouTube Data API Key: Enable the YouTube Data API v3 in your [Google Cloud Console](https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com) and create an API Key.
   - Python 3.11+ installed locally.
2. Environment Setup
   Create a .env file in the root directory and add your keys:
   ```
    GOOGLE_API_KEY=your_api_key_here
   ```
   (Note: Both the Gemini SDK and the YouTube Data API client in this project share this environment variable.)
3. Local Installation
   ```
   # Install system dependencies (Linux/macOS)
   # ffmpeg is required for audio processing
   brew install ffmpeg # macOS
   sudo apt-get install ffmpeg # Ubuntu/Debian

   # Install Python requirements
   pip install -r requirements.txt
   ```
4. Run the Application
   ```
   python main.py
   ```
   Once started, open `http://localhost:8080` in your browser.

## 🚀 Deployment (Google Cloud Run)
Remy is containerized and ready for the cloud. To deploy your own instance to Google Cloud Run:
1. Build and Deploy:
   ```
   gcloud run deploy remy-kitchen \
   --source . \
   --region us-central1 \
   --allow-unauthenticated \
   --set-env-vars GOOGLE_API_KEY=your_api_key_here
   ```
2. HTTPS Requirement: Note that browser features like getUserMedia (Camera/Mic) and WebSockets require an HTTPS connection, which Cloud Run provides automatically via its .a.run.app URL. 

## 🧠 How it Works
1. The Brain: The app uses `gemini-2.5-flash-lite` to quickly parse YouTube metadata and `gemini-2.5-flash-native-audio-preview` for the low-latency voice interaction.
2. The Ears & Eyes: The frontend uses a custom `AudioWorklet` `(processor.js)` to stream raw PCM audio and a Canvas-based capture to stream video frames over WebSockets.
3. The Hands: Remy is equipped with `set_timer` and `stop_timer` tools. When you say "Remy, set a timer for 10 minutes," the model triggers a function call that the frontend intercepts to display a visual countdown.

## 📂 Project Structure
- `main.py`: FastAPI backend handling YouTube extraction and the Gemini Live WebSocket session.
- `index.html`: The "Pastel Kitchen" UI and client-side logic for media streaming.
- `processor.js`: AudioWorklet for real-time PCM audio processing.
- `Dockerfile`: Configuration for containerized deployment.

## 📝 License
MIT License - Feel free to use this as a base for your own AI agents!
