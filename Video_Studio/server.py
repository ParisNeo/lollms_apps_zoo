import os
import re
import uuid
import json
import yaml
import requests
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder='.')

# Paths
WORKSPACE = Path(__file__).parent / 'workspace'
AUDIO_CACHE = Path(__file__).parent / 'audio_cache'
WORKSPACE.mkdir(exist_ok=True)
AUDIO_CACHE.mkdir(exist_ok=True)

# Load config from description.yaml
CONFIG = {}
yaml_path = Path(__file__).parent / 'description.yaml'
if yaml_path.exists():
    with open(yaml_path, 'r', encoding='utf-8') as f:
        CONFIG = yaml.safe_load(f) or {}

# Default Lollms TTS endpoint (can be overridden in description.yaml)
LOLLMS_HOST = CONFIG.get('lollms_host', 'http://127.0.0.1:9600')
TTS_ENDPOINT = LOLLMS_HOST + '/tts'  # Adjust to your Lollms API path


def extract_narration_from_html(html_content: str) -> list:
    """
    Extracts the NARRATION array from a structured video-source HTML file.
    Searches for: const NARRATION = [ "text1", "text2", ... ];
    Returns a list of narration strings.
    """
    # Match the NARRATION array content between [ and ]
    match = re.search(r'const\s+NARRATION\s*=\s*\[(.*?)\];', html_content, re.DOTALL)
    if not match:
        raise ValueError("No NARRATION array found in the uploaded HTML file.")
    
    array_content = match.group(1).strip()
    
    # Parse the JavaScript array — extract quoted strings
    # Handle both single and double quoted strings
    strings = re.findall(r'(?:["\'])(.*?)(?:["\'])', array_content, re.DOTALL)
    
    if not strings:
        raise ValueError("NARRATION array found but contains no strings.")
    
    # Clean up escaped characters
    cleaned = []
    for s in strings:
        s = s.replace('\\n', '\n').replace('\\\'', '\'').replace('\\"', '"')
        cleaned.append(s.strip())
    
    return cleaned


def synthesize_tts(text: str, voice: str = None, speed: float = 1.0) -> bytes:
    """
    Calls the Lollms TTS endpoint to synthesize speech from text.
    Returns the raw audio bytes (WAV or MP3).
    """
    payload = {
        'text': text,
        'voice': voice or CONFIG.get('default_voice', 'default'),
        'speed': speed
    }
    
    try:
        response = requests.post(TTS_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'audio' not in content_type and 'octet-stream' not in content_type:
            raise ValueError(f"TTS endpoint returned non-audio content type: {content_type}")
        
        return response.content
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Lollms TTS at {TTS_ENDPOINT}. "
            f"Ensure Lollms is running and TTS is enabled."
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("TTS synthesis timed out — the text may be too long.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"TTS API error: {e.response.status_code} — {e.response.text[:200]}")


@app.route('/')
def index():
    """Serve the main app UI."""
    return send_from_directory('.', 'index.html')


@app.route('/upload', methods=['POST'])
def upload_video_source():
    """
    Accepts an HTML video-source file upload.
    Extracts the NARRATION array and stores the file in the workspace.
    Returns: { file_id, slides: [{ index, narration }] }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.html'):
        return jsonify({'error': 'File must be .html'}), 400
    
    file_id = str(uuid.uuid4())[:8]
    filename = f"{file_id}.html"
    filepath = WORKSPACE / filename
    file.save(str(filepath))
    
    # Read the file and extract narration
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    try:
        narration = extract_narration_from_html(html_content)
    except ValueError as e:
        os.remove(str(filepath))
        return jsonify({'error': str(e)}), 400
    
    # Return the narration list to the frontend
    slides = [{'index': i, 'narration': text} for i, text in enumerate(narration)]
    
    return jsonify({
        'file_id': file_id,
        'filename': filename,
        'slide_count': len(narration),
        'slides': slides
    })


@app.route('/synthesize', methods=['POST'])
def synthesize_audio():
    """
    Synthesizes TTS audio for a single slide.
    Input: { file_id, slide_index, narration, voice, speed }
    Returns: audio file (wav/mp3)
    """
    data = request.json
    file_id = data.get('file_id')
    slide_index = data.get('slide_index', 0)
    narration = data.get('narration', '')
    voice = data.get('voice', CONFIG.get('default_voice', 'default'))
    speed = data.get('speed', 1.0)
    
    if not narration:
        return jsonify({'error': 'No narration text provided'}), 400
    
    # Generate unique cache filename
    cache_key = f"{file_id}_{slide_index}_{hash(narration)}.wav"
    cache_path = AUDIO_CACHE / cache_key
    
    # Check cache first
    if cache_path.exists():
        return send_from_directory(str(AUDIO_CACHE), cache_key, mimetype='audio/wav')
    
    # Synthesize via Lollms TTS
    try:
        audio_bytes = synthesize_tts(narration, voice, speed)
    except Exception as e:
        return jsonify({'error': f'TTS synthesis failed: {str(e)}'}), 500
    
    # Save to cache
    with open(cache_path, 'wb') as f:
        f.write(audio_bytes)
    
    return send_from_directory(str(AUDIO_CACHE), cache_key, mimetype='audio/wav')


@app.route('/synthesize_all', methods=['POST'])
def synthesize_all():
    """
    Pre-renders ALL slides' TTS audio. Returns a list of audio URLs.
    Input: { file_id, slides: [{index, narration}], voice, speed }
    Returns: { audio_files: [{ index, url, duration_hint }] }
    """
    data = request.json
    file_id = data.get('file_id')
    slides = data.get('slides', [])
    voice = data.get('voice', 'default')
    speed = data.get('speed', 1.0)
    
    audio_files = []
    
    for slide in slides:
        idx = slide['index']
        text = slide['narration']
        cache_key = f"{file_id}_{idx}_{hash(text)}.wav"
        cache_path = AUDIO_CACHE / cache_key
        
        if not cache_path.exists():
            try:
                audio_bytes = synthesize_tts(text, voice, speed)
                with open(cache_path, 'wb') as f:
                    f.write(audio_bytes)
            except Exception as e:
                return jsonify({
                    'error': f'TTS failed on slide {idx}: {str(e)}'
                }), 500
        
        audio_files.append({
            'index': idx,
            'url': f'/audio_cache/{cache_key}'
        })
    
    return jsonify({
        'file_id': file_id,
        'audio_files': audio_files,
        'total': len(audio_files)
    })


@app.route('/audio_cache/<path:filename>')
def serve_audio(filename):
    """Serves cached audio files to the frontend."""
    return send_from_directory(str(AUDIO_CACHE), filename, mimetype='audio/wav')


@app.route('/workspace/<path:filename>')
def serve_source(filename):
    """Serves the uploaded video-source HTML file."""
    return send_from_directory(str(WORKSPACE), filename, mimetype='text/html')


@app.route('/list_voices')
def list_voices():
    """
    Returns available TTS voices from the Lollms TTS service.
    Falls back to a default list if the endpoint is unavailable.
    """
    default_voices = [
        {'name': 'default', 'language': 'en', 'gender': 'neutral'},
    ]
    
    try:
        response = requests.get(f"{LOLLMS_HOST}/tts_voices", timeout=5)
        if response.status_code == 200:
            return jsonify({'voices': response.json().get('voices', default_voices)})
    except:
        pass
    
    return jsonify({'voices': default_voices})


@app.route('/config')
def get_config():
    """Returns app configuration to the frontend."""
    return jsonify({
        'default_voice': CONFIG.get('default_voice', 'default'),
        'default_speed': CONFIG.get('default_speed', 1.0),
        'canvas_width': CONFIG.get('canvas_width', 1920),
        'canvas_height': CONFIG.get('canvas_height', 1080),
        'canvas_fps': CONFIG.get('canvas_fps', 30),
        'output_format': CONFIG.get('output_format', 'webm'),
        'lollms_host': LOLLMS_HOST
    })


if __name__ == '__main__':
    port = CONFIG.get('server', {}).get('port', 8080) if isinstance(CONFIG.get('server'), dict) else 8080
    host = CONFIG.get('server', {}).get('host', '127.0.0.1') if isinstance(CONFIG.get('server'), dict) else '127.0.0.1'
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  VIDEO STUDIO APP — ParisNeo              ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  Server:  http://{host}:{port:<24}║",)
    print(f"║  TTS:     {TTS_ENDPOINT:<28}║")
    print(f"║  Cache:   {AUDIO_CACHE}║")
    print(f"╚══════════════════════════════════════════╝")
    app.run(host=host, port=port, debug=True)