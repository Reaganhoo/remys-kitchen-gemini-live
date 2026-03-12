import os
import asyncio
import json
import base64
import uuid
import uvicorn
import re  # Added for Regex
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, Query
from fastapi.responses import FileResponse
from google import genai
from google.genai import types
from googleapiclient.discovery import build  # Added for YouTube API
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# In-memory storage for recipes
recipe_store = {}

# YOUR SPECIFIED MODELS
MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
MODEL_LITE = "gemini-2.5-flash-lite" 

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"), http_options={'api_version': 'v1beta'})

def get_video_id(url):
    """Extracts the 11-character YouTube video ID."""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.post("/summarize")
async def summarize_video(data: dict = Body(...)):
    url = data.get("url")
    print(f"DEBUG: Received URL: {url}")
    
    video_id = get_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL format."}, 400

    try:
        print("DEBUG: Fetching info via YouTube Data API...")
        # Initialize the YouTube service
        youtube = build("youtube", "v3", developerKey=os.getenv("GOOGLE_API_KEY"))
        
        # Request video snippet (contains title and description)
        request = youtube.videos().list(part="snippet", id=video_id)
        response_api = request.execute()

        if not response_api.get("items"):
            return {"error": "Video not found or is private."}, 404

        snippet = response_api["items"][0]["snippet"]
        title = snippet.get("title", "Unknown Title")
        description = snippet.get("description", "No description available")
        
        context_blob = f"Title: {title}\nDescription: {description}"

        prompt = (
            "EXTRACT RECIPE DATA:\n"
            f"{context_blob}\n\n"
            "Output ONLY: 1. Ingredients. 2. Step-by-step instructions."
        )
        
        print("DEBUG: Calling Gemini for summary...")
        response = client.models.generate_content(model=MODEL_LITE, contents=prompt)
        
        session_id = str(uuid.uuid4())
        recipe_store[session_id] = response.text
        
        return {"summary": response.text, "session_id": session_id}
        
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}") 
        return {"error": f"Chef Remy had a slip! Error: {str(e)}"}, 500

# --- REST OF YOUR CODE (WEBSOCKETS & ROUTES) REMAINS UNCHANGED ---

@app.get("/processor.js")
async def get_processor():
    return FileResponse('processor.js', media_type='application/javascript')

@app.get("/")
async def get_index():
    return FileResponse('index.html')

@app.websocket("/ws/remy")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Query(None)):
    await websocket.accept()
    
    recipe = recipe_store.get(session_id, "No recipe found. Just be a helpful chef.")
    
    personalized_instruction = (
        "ROLE: You are Remy, a witty Sous-Chef. "
        "YOUR DATA SOURCE: You MUST follow this specific recipe summary for the user:\n\n"
        f"{recipe}\n\n"
        "Use your tools to set or stop timers when the user asks or when the recipe requires it."
    )

    tools = [{"function_declarations": [
        {
            "name": "set_timer",
            "description": "Sets a kitchen timer for a specified number of minutes.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"minutes": {"type": "NUMBER", "description": "Minutes for the timer"}},
                "required": ["minutes"]
            }
        },
        {
            "name": "stop_timer",
            "description": "Stops and clears the current kitchen timer.",
            "parameters": {"type": "OBJECT", "properties": {}}
        }
    ]}]

    try:
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=personalized_instruction,
            tools=tools,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
                )
            )
        )

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            async def receive_from_browser():
                try:
                    while True:
                        data = await websocket.receive_text()
                        msg = json.loads(data)
                        if "realtime_input" in msg:
                            for chunk in msg["realtime_input"]["media_chunks"]:
                                await session.send_realtime_input(media=chunk)
                except: pass

            async def send_to_browser():
                try:
                    while True:
                        async for response in session.receive():
                            if response.tool_call:
                                for call in response.tool_call.function_calls:
                                    if call.name == "set_timer":
                                        mins = call.args["minutes"]
                                        await websocket.send_json({"timer": "start", "minutes": mins})
                                        await session.send_tool_response(function_responses=[{"name": "set_timer", "response": {"result": "ok"}, "id": call.id}])
                                    elif call.name == "stop_timer":
                                        await websocket.send_json({"timer": "stop"})
                                        await session.send_tool_response(function_responses=[{"name": "stop_timer", "response": {"result": "ok"}, "id": call.id}])

                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        await websocket.send_json({"audio": base64.b64encode(part.inline_data.data).decode('utf-8')})
                                    if part.text:
                                        await websocket.send_json({"text": part.text})
                except: pass

            await asyncio.gather(receive_from_browser(), send_to_browser())
            
    except WebSocketDisconnect:
        if session_id in recipe_store:
            del recipe_store[session_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)