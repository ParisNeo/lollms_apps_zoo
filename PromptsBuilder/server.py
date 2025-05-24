import os
import json
import time
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from lollms_client import LollmsClient
import safe_store # Assuming safe_store is installed and importable

# --- Configuration ---
# Ensure these directories exist
DATA_DIR = Path("data")
PROMPT_STORE_DIR = Path("prompt_store_db")
TEMP_PROMPT_FILES_DIR = PROMPT_STORE_DIR / "temp_prompt_files"

DATA_DIR.mkdir(exist_ok=True)
PROMPT_STORE_DIR.mkdir(exist_ok=True)
TEMP_PROMPT_FILES_DIR.mkdir(exist_ok=True)

SUBJECTS_FILE = DATA_DIR / "subjects.json"
TASKS_FILE = DATA_DIR / "tasks.json"
TESTS_FILE = DATA_DIR / "tests.json"

SAFE_STORE_DB_FILE = PROMPT_STORE_DIR / "app_store.db"
# Ensure the .lock file can be created if it doesn't exist by removing stale one
Path(f"{SAFE_STORE_DB_FILE}.lock").unlink(missing_ok=True)

# Initialize SafeStore
# Using a common default vectorizer. Ensure you have sentence-transformers installed
# pip install safe-store[sentence-transformers]
try:
    VECTORIZER_NAME = "st:all-MiniLM-L6-v2" 
    store = safe_store.SafeStore(db_path=str(SAFE_STORE_DB_FILE), log_level=safe_store.LogLevel.INFO)
    print(f"SafeStore initialized with DB: {SAFE_STORE_DB_FILE}")
except Exception as e:
    print(f"Error initializing SafeStore: {e}. Make sure dependencies are installed (e.g., sentence-transformers).")
    store = None # App can run but storing will fail

# Initialize LollmsClient
# Configure based on your LoLLMs setup
# Example: Default local LoLLMs service
try:
    lc = LollmsClient() 
    # Or specific: lc = LollmsClient(host_address="http://localhost:9600")
    # Or ollama: lc = LollmsClient("ollama", model_name="mistral:latest")
    print("LollmsClient initialized.")
    # Quick test to see if server is responsive (optional)
    # print("Available models:", lc.listModels())
except Exception as e:
    print(f"Error initializing LollmsClient: {e}. Ensure LoLLMs or chosen backend is running.")
    lc = None # App can run but LLM testing will fail

# --- Flask App Setup ---
app = Flask(__name__, template_folder="templates", static_folder="static")

# --- Helper Functions ---
def load_json_data(filepath):
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] # Return empty list if JSON is corrupted

def save_json_data(filepath, data):
    DATA_DIR.mkdir(exist_ok=True) # Ensure data directory exists
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({
        'subjects': load_json_data(SUBJECTS_FILE),
        'tasks': load_json_data(TASKS_FILE),
        'tests': load_json_data(TESTS_FILE)
    })

@app.route('/api/add_item/<category_name>', methods=['POST'])
def add_item(category_name):
    data = request.get_json()
    new_item = data.get('item')
    if not new_item:
        return jsonify({'error': 'No item provided'}), 400

    filepath = None
    if category_name == 'subject':
        filepath = SUBJECTS_FILE
    elif category_name == 'task':
        filepath = TASKS_FILE
    elif category_name == 'test':
        filepath = TESTS_FILE
    else:
        return jsonify({'error': 'Invalid category'}), 400

    current_items = load_json_data(filepath)
    if new_item not in current_items:
        current_items.append(new_item)
        save_json_data(filepath, current_items)
        return jsonify({'message': f'{category_name.capitalize()} "{new_item}" added successfully.', 'items': current_items}), 201
    else:
        return jsonify({'message': f'{category_name.capitalize()} "{new_item}" already exists.', 'items': current_items}), 200


@app.route('/api/store_prompt', methods=['POST'])
def store_prompt_route():
    if not store:
        return jsonify({'error': 'SafeStore is not initialized. Cannot store prompt.'}), 500
        
    data = request.get_json()
    prompt_text = data.get('prompt')
    subject = data.get('subject')
    task = data.get('task')
    test_focus = data.get('test') # Renamed to avoid conflict with 'test' keyword

    if not prompt_text:
        return jsonify({'error': 'No prompt text provided'}), 400

    try:
        # SafeStore add_document needs a file. We write the prompt to a temporary file.
        prompt_filename = f"prompt_{uuid.uuid4()}.txt"
        temp_file_path = TEMP_PROMPT_FILES_DIR / prompt_filename
        
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)

        metadata = {
            "subject": subject,
            "task": task,
            "test_focus": test_focus,
            "timestamp": time.time(),
            "source_app": "LollmsPromptCrafter"
        }
        
        # Using 'with store:' ensures thread-safe operations if SafeStore implements context management
        # for locking. SafeStore internally handles file locking on writes.
        store.add_document(
            doc_path=str(temp_file_path), 
            vectorizer_name=VECTORIZER_NAME, 
            metadata=metadata
        )
        
        # Optional: Clean up the temp file after indexing if not needed
        # temp_file_path.unlink() 
        # Or keep them for audit/backup, but manage disk space.

        return jsonify({'message': f'Prompt stored successfully with ID referring to: {prompt_filename}'}), 200
    except Exception as e:
        app.logger.error(f"Error storing prompt in SafeStore: {e}")
        return jsonify({'error': f'Failed to store prompt: {str(e)}'}), 500

@app.route('/api/test_llm', methods=['POST'])
def test_llm_route():
    if not lc:
        return jsonify({'error': 'LollmsClient is not initialized. Cannot test prompt.'}), 500

    data = request.get_json()
    prompt_text = data.get('prompt')
    if not prompt_text:
        return jsonify({'error': 'No prompt text provided'}), 400

    try:
        # You might want to configure temperature, max_tokens etc.
        response = lc.generate_text(prompt=prompt_text, max_new_tokens=1024, stream=False) # stream=False for simple string response
        return jsonify({'response': response}), 200
    except Exception as e:
        app.logger.error(f"Error communicating with LLM: {e}")
        return jsonify({'error': f'LLM communication error: {str(e)}'}), 500

if __name__ == '__main__':
    # Ensure required directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_STORE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_PROMPT_FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create empty JSON files if they don't exist for initial load
    for f_path in [SUBJECTS_FILE, TASKS_FILE, TESTS_FILE]:
        if not f_path.exists():
            save_json_data(f_path, [])

    app.run(debug=True, host='0.0.0.0', port=5001) # Changed port to avoid conflict with common 5000