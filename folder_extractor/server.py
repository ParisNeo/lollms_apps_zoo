# folder_extractor/server.py
# [UPDATE]

import os
import sys
import fnmatch
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Set
import webbrowser
import threading
import uuid
from ascii_colors import trace_exception # Still needed for potential proxying or other uses if not fully replaced, but core LLM logic moves to lollms_client

try:
    import pipmaster
except ImportError:
    print("Pipmaster not found. Installing...")
    os.system(f"{sys.executable} -m pip install pipmaster")
    import pipmaster

# Ensure lollms-client is installed
pipmaster.ensure_packages(["fastapi", "uvicorn", "python-multipart", "httpx", "lollms-client"])

# Import Server and Config directly from uvicorn
from uvicorn import Server, Config
from fastapi import FastAPI, HTTPException, Body, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import argparse
import asyncio

# Import LollmsClient and MSG_TYPE from the lollms_client library
from lollms_client import LollmsClient, MSG_TYPE

APP_TITLE = "Folder Structure Extractor Web App"
APP_VERSION = "3.5.0"
CONFIG_DIR = Path.home() / ".config" / "folder_extractor_web"
PROMPTS_FILE = CONFIG_DIR / "prompt_templates.json"
PROJECTS_FILE = CONFIG_DIR / "projects.json"
LLM_SETTINGS_FILE = CONFIG_DIR / "llm_settings.json"

# New constants for AI file selection context
CORE_PROJECT_CONTEXT_FILES = [
    "server.py",
    "static/main.js",
    "static/index.html",
    "static/style.css",
    "requirements.txt",
    "description.yaml",
    "default_prompts.json",
    "README.md"
]
CORE_FILE_MAX_SIZE_BYTES = 50 * 1024 # 50 KB

DEFAULT_TEMPLATES_DATA = [
  {
    "name": "AI: Full Code Generation",
    "content": "You are an expert software developer. Your task is to implement a new feature.\n\n**Feature Request:** {USER_REQUEST}\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the provided folder structure and file contents (full content or signatures as indicated).\n2.  **Develop a Plan:** Create a detailed plan outlining:\n    *   Which files need to be created.\n    *   Which existing files need to be modified.\n    *   A summary of changes for each affected file.\n    *   Any new dependencies required.\n    *   Potential impacts on existing functionality.\n    *   Suggestions for necessary tests.\n    **Present this plan first and wait for my explicit 'ACKNOWLEDGE PLAN' or 'PROCEED' command before generating any code.**\n\n3.  **Implement Changes (Full Code):**\n    *   For **new files**, generate the complete file content from scratch. Ensure the code is clean, well-commented (docstrings/JSDoc where appropriate), and adheres to best practices.\n    *   For **modified files**, regenerate the ENTIRE file with the necessary changes incorporated. Do NOT use placeholders like '// ... existing code ...' or provide only fragments. The output for a modified file must be its complete new content.\n    *   Address all aspects of the feature request.\n    *   Consider edge cases and potential error handling.\n\n**Output Format:**\nAfter I acknowledge the plan, provide the content for each new or modified file one by one. Start each file block with `--- FILE: path/to/your/file.ext ---` and end with `--- END OF FILE ---`. Wait for my 'NEXT' command after each file before proceeding to the next one."
  },
  {
    "name": "AI: Guided Code Changes",
    "content": "You are an expert software developer. Your task is to modify the existing codebase based on my request.\n\n**Change Request:** {USER_REQUEST}\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context & Plan:** Review the project and my request. Formulate a plan for the required changes. Briefly explain the plan.\n2.  **Wait for Confirmation:** After presenting the plan, wait for me to confirm with a command like 'ACKNOWLEDGE PLAN' or 'PROCEED'.\n3.  **Provide Changes in Diff Format:** Generate the changes for each modified file using a standard diff format. For each file, start with `--- path/to/original/file.ext` and `+++ path/to/new/file.ext`. Use `+` for additions and `-` for deletions. Provide enough surrounding context (unchanged lines) for clarity.\n4.  **Provide New Files in Full:** If a new file is required, provide its full content, starting with `--- FILE: path/to/new/file.ext ---` and ending with `--- END OF FILE ---`."
  },
  {
    "name": "General: Project Overview",
    "content": "Please provide a high-level overview of this project based on its file structure and contents. Identify the main programming languages, frameworks, and potential purpose of the application. Highlight any key configuration files or entry points."
  },
  {
    "name": "Docs: Generate README",
    "content": "Based on the provided project context, generate a comprehensive `README.md` file. It should include:\n- A project title and a brief description.\n- A section on features.\n- Instructions on how to build and run the project.\n- The folder structure tree.\n- A summary of key source files."
  }
]

ALWAYS_PRUNE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "target", "build", "dist", "out"
}

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PRESET_EXCLUSIONS = {
    "Python Project": {
        "folders": ["htmlcov", ".tox", ".hypothesis", "*.egg-info"],
        "extensions": [".pyc", ".pyo", ".pyd", ".so"],
        "patterns": ["site/*"]
    },
    "Node.js Project": {
        "folders": [".next", ".nuxt", "coverage", ".svelte-kit", "public/build"],
        "extensions": [".log"],
        "patterns": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
    },
    "Java Project (Maven/Gradle)": {
        "folders": [".gradle"],
        "extensions": [".class", ".jar", ".war", ".ear"],
        "patterns": []
    },
    "Git Repository": {
        "folders": [],
        "extensions": [],
        "patterns": [".gitignore", ".gitattributes", ".gitmodules"]
    },
    "IDE/Editor Configs": {
        "folders": [".vscode", ".idea", ".vs", ".history", "nbproject", ".settings"],
        "extensions": [".suo", ".user", ".sln.docstates"],
        "patterns": []
    },
    "Operating System/Misc": {
        "folders": [".DS_Store", "$RECYCLE.BIN", "System Volume Information"],
        "extensions": [".bak", ".tmp", ".swp", ".swo"],
        "patterns": ["Thumbs.db", "desktop.ini"]
    },
    "Log Files": {"folders": [], "extensions": [".log", ".log.*"], "patterns": ["*.log"]},
    "Binary/Archives": { "extensions": [".exe", ".dll", ".bin", ".o", ".a", ".lib", ".so", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso"], "folders": [], "patterns": [] },
    "Large Media Files": { "extensions": [".png", ".jpg", ".gif", ".mp4", ".mov", ".mp3", ".pdf", ".doc", ".docx", ".ppt", ".xls", ".psd", ".ai", ".svg"], "folders": [] , "patterns": []}
}

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# --- Pydantic Models ---
class FilterSettings(BaseModel):
    selected_presets: List[str] = Field(default_factory=list)
    custom_folders: str = ""
    custom_extensions: str = ""
    custom_patterns: str = ""
    dynamic_patterns: str = ""
    custom_inclusions: str = ""
    max_file_size_mb: float = 1.0

class LoadProjectTreeRequest(BaseModel):
    folder_path: str
    filters: FilterSettings

class GenerateStructureRequest(BaseModel):
    folder_path: str
    filters: FilterSettings
    selected_files_info: List[Dict[str, str]]
    custom_prompt: str = ""
    loaded_doc_paths: List[str] = Field(default_factory=list)
    hard_excluded_paths: List[str] = Field(default_factory=list)

class Template(BaseModel):
    name: str
    content: str

class DeleteTemplateRequest(BaseModel):
    name: str
    content: Optional[str] = None

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    path: str
    starred: bool = False
    last_accessed: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    starred: Optional[bool] = None

class ProjectExportRequest(BaseModel):
    project_ids: List[str]

class LLMSettings(BaseModel):
    url: str = ""
    api_key: str = ""
    model_name: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class TokenCountRequest(BaseModel):
    text: str

class LLMSelectRequest(BaseModel):
    project_path: str
    user_goal: str
    filters: FilterSettings

def load_json_file(file_path: Path, default_value: Any) -> Any:
    if not file_path.exists():
        return default_value
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default_value

def save_json_file(file_path: Path, data: Any):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving to {file_path}: {e}")

def get_exclusion_sets(filters: FilterSettings) -> (Set[str], Set[str], Set[str]):
    excluded_folders = set()
    excluded_extensions = set()
    excluded_patterns = set()
    for preset_name in filters.selected_presets:
        preset = PRESET_EXCLUSIONS.get(preset_name, {})
        excluded_folders.update(preset.get("folders", []))
        excluded_extensions.update(preset.get("extensions", []))
        excluded_patterns.update(preset.get("patterns", []))
    if filters.custom_folders:
        excluded_folders.update(p.strip() for p in filters.custom_folders.split(',') if p.strip())
    if filters.custom_extensions:
        excluded_extensions.update(p.strip() for p in filters.custom_extensions.split(',') if p.strip())
    if filters.custom_patterns:
        excluded_patterns.update(p.strip() for p in filters.custom_patterns.split(',') if p.strip())
    if filters.dynamic_patterns:
        excluded_patterns.update(p.strip() for p in filters.dynamic_patterns.split(',') if p.strip())
    return excluded_folders, excluded_extensions, excluded_patterns

def get_inclusion_patterns(filters: FilterSettings) -> Set[str]:
    if not filters.custom_inclusions:
        return set()
    return {p.strip() for p in filters.custom_inclusions.split(',') if p.strip()}

def is_path_explicitly_included(path: Path, root_path: Path, inclusion_patterns: Set[str]) -> bool:
    if not inclusion_patterns:
        return False
    relative_path_str = str(path.relative_to(root_path)).replace('\\', '/')
    for pattern in inclusion_patterns:
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        if fnmatch.fnmatch(path.name, pattern):
            return True
        if pattern.endswith('/') and path.is_dir() and relative_path_str.startswith(pattern[:-1]):
            return True
    return False

def is_excluded(path: Path, root_path: Path, excluded_folders: Set[str], excluded_extensions: Set[str], excluded_patterns: Set[str]) -> bool:
    relative_path = path.relative_to(root_path)
    if path.is_dir() and path.name in excluded_folders:
        return True
    if path.is_file() and path.suffix.lower() in excluded_extensions:
        return True
    
    path_parts = [str(relative_path).replace('\\', '/'), path.name]
    for part in path_parts:
        for pattern in excluded_patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False

def is_text_file(path: Path) -> bool:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def extract_signatures_python(code: str) -> str:
    try:
        tree = ast.parse(code)
        signatures = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                signatures.append(f"class {node.name}:")
                docstring = ast.get_docstring(node)
                if docstring:
                    signatures.append(f'    """{docstring}"""')
                signatures.append("    ...")
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                decorator_list = [f"@{d.id}" for d in node.decorator_list if isinstance(d, ast.Name)]
                if decorator_list:
                    signatures.extend(decorator_list)
                signature_line = f"def {node.name}({', '.join(args)}):"
                signatures.append(signature_line)
                docstring = ast.get_docstring(node)
                if docstring:
                    signatures.append(f'    """{docstring}"""')
                signatures.append("    ...")
        return "\n".join(signatures)
    except Exception as e:
        return f"Could not parse Python signatures: {e}"

def extract_signatures_js(code: str) -> str:
    signatures = []
    pattern = re.compile(
        r'(\/\*\*[\s\S]*?\*\/[\r\n\s]*)?'
        r'(class\s+\w+|'
        r'(?:async\s+)?function\s+\w+\s*\(.*?\)|'
        r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\(.*?\)\s*=>)', re.MULTILINE)
    
    for match in pattern.finditer(code):
        signatures.append(match.group(0).strip() + " { ... }")

    if not signatures:
        return "No obvious signatures found."
    return "\n\n".join(signatures)

def build_file_tree_with_selection_info(root_path_str: str, filters: FilterSettings) -> List[Dict]:
    root_path = Path(root_path_str)
    if not root_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Root folder not found: {root_path_str}")

    excluded_folders, excluded_extensions, excluded_patterns = get_exclusion_sets(filters)
    inclusion_patterns = get_inclusion_patterns(filters)
    
    def should_process(path: Path):
        if is_path_explicitly_included(path, root_path, inclusion_patterns):
            return True
        if is_excluded(path, root_path, excluded_folders, excluded_extensions, excluded_patterns):
            return False
        return True

    def recurse_tree(current_path: Path, parent_list: List[Dict]):
        try:
            items_iterator = current_path.iterdir()
        except OSError:
            return
        
        items = sorted(list(items_iterator), key=lambda p: (not p.is_dir(), p.name.lower()))
        
        for path in items:
            if path.is_dir() and path.name in ALWAYS_PRUNE_DIRS:
                if not is_path_explicitly_included(path, root_path, inclusion_patterns):
                    continue

            if not should_process(path):
                continue
            
            node_info = {"name": path.name, "path": str(path.resolve()), "is_dir": path.is_dir()}
            
            if path.is_dir():
                node_info["children"] = []
                node_info["can_be_checked"] = True
                recurse_tree(path, node_info["children"])
                if not node_info["children"] and not is_path_explicitly_included(path, root_path, inclusion_patterns):
                    continue
            else:
                is_text = is_text_file(path)
                file_size_mb = path.stat().st_size / (1024 * 1024)
                node_info["is_text"] = is_text
                node_info["is_signature_candidate"] = path.suffix.lower() in ['.py', '.js']
                node_info["can_be_checked"] = True
                node_info["tooltip"] = f"{file_size_mb:.3f} MB"

                if not is_text:
                    node_info["tooltip"] = node_info["tooltip"] + " (Binary)"
                    node_info["can_be_checked"] = False
                elif file_size_mb > filters.max_file_size_mb:
                    node_info["tooltip"] = node_info["tooltip"] + f" (Exceeds {filters.max_file_size_mb} MB limit)"
                    node_info["can_be_checked"] = False
            parent_list.append(node_info)

    root_node_info = {"name": root_path.name, "path": str(root_path.resolve()), "is_dir": True, "can_be_checked": True, "children": []}
    recurse_tree(root_path, root_node_info["children"])
    return [root_node_info]

def generate_markdown_tree(root_path_str: str, hard_excluded_paths: Set[str]) -> str:
    root_path = Path(root_path_str)
    markdown_lines = [f"📁 {root_path.name}/"]
    
    def recurse_md_tree(current_path: Path, prefix: str):
        try:
            items_iterator = current_path.iterdir()
        except OSError:
            return

        items_to_process = [p for p in sorted(list(items_iterator), key=lambda p: (not p.is_dir(), p.name.lower())) if str(p.resolve()) not in hard_excluded_paths]
        
        for i, path in enumerate(items_to_process):
            if path.is_dir() and path.name in ALWAYS_PRUNE_DIRS:
                if str(path.resolve()) not in hard_excluded_paths:
                    continue

            is_last = (i == len(items_to_process) - 1)
            connector = "└─ " if is_last else "├─ "
            icon = "📁" if path.is_dir() else "📄"

            line = f"{prefix}{connector}{icon} {path.name}"
            if path.is_dir():
                line += "/"
            
            markdown_lines.append(line)

            if path.is_dir():
                new_prefix = prefix + ("   " if is_last else "│  ")
                recurse_md_tree(path, new_prefix)
    
    recurse_md_tree(root_path, "")
    return "\n".join(markdown_lines)

def get_default_templates() -> List[Dict]:
    return DEFAULT_TEMPLATES_DATA

def save_prompt_templates(templates: List[Dict]):
    save_json_file(PROMPTS_FILE, templates)

def load_prompt_templates() -> List[Dict]:
    """
    Loads prompt templates, automatically healing the file if it's corrupted
    with project data from a previous bug.
    """
    # Load raw data, fall back to default if file doesn't exist.
    if not PROMPTS_FILE.exists():
        default_templates = get_default_templates()
        save_prompt_templates(default_templates)
        return default_templates
    
    templates_data = load_json_file(PROMPTS_FILE, [])

    # Filter out any entries that don't look like templates.
    # A valid template must be a dict with 'name' and 'content' keys.
    # A project has 'id' and 'path', so checking for 'content' is a good discriminator.
    cleaned_templates = [
        t for t in templates_data 
        if isinstance(t, dict) and 'name' in t and 'content' in t
    ]

    # If the file was empty after cleaning, or if we removed items, we need to take action.
    if not cleaned_templates:
        # If cleaning resulted in an empty list, the file was fully corrupted or empty. Reset to default.
        print("INFO: Prompt templates file was empty or fully corrupted. Resetting to defaults.")
        default_templates = get_default_templates()
        save_prompt_templates(default_templates)
        return default_templates

    if len(cleaned_templates) < len(templates_data):
        # If we removed some corrupted entries, save the cleaned list back.
        print(f"INFO: Removed {len(templates_data) - len(cleaned_templates)} corrupted entries from prompt templates file.")
        save_prompt_templates(cleaned_templates)

    return cleaned_templates

# --- API Endpoints ---

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    projects = load_json_file(PROJECTS_FILE, [])
    return sorted(projects, key=lambda p: p['last_accessed'], reverse=True)

@app.post("/api/projects", response_model=Project)
async def create_project(project: Project):
    projects = load_json_file(PROJECTS_FILE, [])
    projects.append(project.model_dump())
    save_json_file(PROJECTS_FILE, projects)
    return project

@app.put("/api/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update_data: ProjectUpdateRequest):
    projects = load_json_file(PROJECTS_FILE, [])
    project_index = next((i for i, p in enumerate(projects) if p['id'] == project_id), None)
    if project_index is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    project_dict = projects[project_index]
    update_dict = update_data.model_dump(exclude_unset=True)
    project_dict.update(update_dict)
    project_dict['last_accessed'] = datetime.utcnow().isoformat()
    
    projects[project_index] = project_dict
    save_json_file(PROJECTS_FILE, projects)
    return Project(**project_dict)

@app.delete("/api/projects/{project_id}", status_code=204)
async def delete_project(project_id: str):
    projects = load_json_file(PROJECTS_FILE, [])
    initial_len = len(projects)
    projects = [p for p in projects if p['id'] != project_id]
    if len(projects) == initial_len:
        raise HTTPException(status_code=404, detail="Project not found.")
    save_json_file(PROJECTS_FILE, projects)

@app.post("/api/projects/{project_id}/clone", response_model=Project)
async def clone_project(project_id: str):
    projects = load_json_file(PROJECTS_FILE, [])
    project_to_clone = next((p for p in projects if p['id'] == project_id), None)
    if project_to_clone is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    cloned_project_dict = project_to_clone.copy()
    cloned_project_dict['id'] = str(uuid.uuid4())
    cloned_project_dict['name'] = f"{cloned_project_dict['name']} (copy)"
    cloned_project_dict['last_accessed'] = datetime.utcnow().isoformat()
    cloned_project_dict['starred'] = False

    projects.append(cloned_project_dict)
    save_json_file(PROJECTS_FILE, projects)
    return Project(**cloned_project_dict)

@app.post("/api/projects/export", response_model=List[Project])
async def export_projects(request: ProjectExportRequest):
    projects = load_json_file(PROJECTS_FILE, [])
    projects_to_export = [p for p in projects if p['id'] in request.project_ids]
    return projects_to_export

@app.post("/api/projects/import", response_model=List[Project])
async def import_projects(imported_projects: List[Project]):
    if not imported_projects:
        raise HTTPException(status_code=400, detail="No projects provided for import.")

    projects = load_json_file(PROJECTS_FILE, [])
    existing_paths = {p['path'] for p in projects}
    
    newly_added_projects = []
    for proj in imported_projects:
        if proj.path in existing_paths:
            # Skip projects with the same path to avoid duplicates
            continue
        
        new_proj = proj.model_dump()
        new_proj['id'] = str(uuid.uuid4()) # Assign a new ID to avoid conflicts
        new_proj['last_accessed'] = datetime.utcnow().isoformat()
        projects.append(new_proj)
        newly_added_projects.append(Project(**new_proj))

    save_json_file(PROJECTS_FILE, projects)
    return newly_added_projects

@app.get("/api/settings/llm", response_model=LLMSettings)
async def get_llm_settings():
    return load_json_file(LLM_SETTINGS_FILE, LLMSettings().model_dump())

@app.post("/api/settings/llm", status_code=204)
async def save_llm_settings(settings: LLMSettings):
    save_json_file(LLM_SETTINGS_FILE, settings.model_dump())

# Helper function to get a configured LollmsClient instance
def _get_lollms_client_instance() -> LollmsClient:
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.url:
        raise HTTPException(status_code=400, detail="LLM service URL is not configured.")

       
    try:
        # Use 'lollms' binding
        return LollmsClient(
            llm_binding_name="lollms",
            llm_binding_config={
                "host_address":settings.url+"/v1",
                "service_key":settings.api_key,
                "model_name":settings.model_name
            }
            
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LollmsClient: {e}")

@app.get("/api/context_size")
async def get_context_size():
    try:
        lc = _get_lollms_client_instance()
        context_size = lc.get_ctx_size(lc.binding.model_name) # Use the client's configured model_name
        return {"context_size": context_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching context size: {e}")

@app.post("/api/count_tokens")
async def count_tokens(request: TokenCountRequest):
    try:
        lc = _get_lollms_client_instance()
        count = lc.get_token_count(request.text, model=lc.model_name) # Use the client's configured model_name
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting tokens: {e}")

@app.get("/api/llm_models", response_model=List[str])
async def get_llm_models():
    try:
        lc = _get_lollms_client_instance()
        models = lc.list_models()
        model_ids = [model['model_name'] for model in models] if isinstance(models, list) and models else models
        return sorted(model_ids) if isinstance(model_ids, list) else []
    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")

@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    lc = _get_lollms_client_instance()

    # Generator to stream chunks from lollms_client callback to SSE
    async def stream_generator():
        full_response_content = ""
        
        # This queue will hold chunks received from the lollms_client callback
        # and allow the FastAPI StreamingResponse to consume them.
        chunk_queue = asyncio.Queue()
        
        # Callback function to put chunks into the queue
        def streaming_callback(chunk: str, msg_type: MSG_TYPE, params=None, metadata=None) -> bool:
            nonlocal full_response_content
            if msg_type == MSG_TYPE.MSG_TYPE_CHUNK:
                full_response_content += chunk
                # Send chunk as SSE data
                chunk_queue.put_nowait(f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n".encode('utf-8'))
            elif msg_type == MSG_TYPE.MSG_TYPE_EXCEPTION:
                error_message = f"Streaming Error: {chunk}"
                chunk_queue.put_nowait(f"data: {json.dumps({'error': error_message})}\n\n".encode('utf-8'))
                return False # Stop streaming on exception
            return True # Continue streaming

        # Run the lollms_client generation in a separate task to not block the FastAPI event loop
        generation_task = asyncio.create_task(
            lc.generate_from_messages(
                messages=[msg.model_dump() for msg in request.messages],
                stream=True,
                streaming_callback=streaming_callback,
                temperature=0.1,
                max_tokens=4096
            )
        )

        try:
            # Yield chunks from the queue as they arrive
            while True:
                chunk_data = await asyncio.wait_for(chunk_queue.get(), timeout=60.0) # Add a timeout for safety
                yield chunk_data
                if generation_task.done() and chunk_queue.empty():
                    break # Stop if generation is done and queue is empty
        except asyncio.TimeoutError:
            # If timeout occurs, assume generation has stalled or finished, but queue not empty
            # Check if task is already done, if not, print a warning and break.
            if not generation_task.done():
                print("Warning: Streaming generator timed out, LLM generation might be stuck.")
            # Ensure the final DONE message is sent
        
        # Ensure the generation task is awaited to catch any exceptions it might raise
        # and to properly clean up resources.
        await generation_task
        
        # Send the final DONE message
        yield b"data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
import json
import re
from pathlib import Path
from typing import List, Dict

from fastapi import HTTPException
from fastapi.responses import JSONResponse


@app.post("/api/llm_select_files")
async def llm_select_files(request: LLMSelectRequest):
    try:
        lc = _get_lollms_client_instance()

        project_root = Path(request.project_path)
        if not project_root.is_dir():
            raise HTTPException(status_code=404, detail=f"Project folder not found: {request.project_path}")

        # Existing logic to get full tree and flatten file list
        tree_nodes = build_file_tree_with_selection_info(request.project_path, request.filters)

        # This list will contain ALL eligible files the LLM can choose from, relative paths
        file_list_all_eligible_paths = []

        def flatten_tree_eligible_paths(nodes):
            for node in nodes:
                path = Path(node["path"])
                if not node["is_dir"] and node.get("can_be_checked", True):  # Only include files that can be checked
                    file_list_all_eligible_paths.append(
                        {
                            "path": str(path.relative_to(project_root)).replace('\\', '/'),
                            "is_signature_candidate": node.get("is_signature_candidate", False),
                        }
                    )
                if node.get("children"):
                    flatten_tree_eligible_paths(node["children"])

        if tree_nodes:  # tree_nodes[0] is the root folder itself
            flatten_tree_eligible_paths(tree_nodes[0].get("children", []))

        if not file_list_all_eligible_paths:
            return JSONResponse(content={"status": "success", "files": []})

        # --- New logic to gather core project context ---
        core_context_parts = []
        for rel_path_str in CORE_PROJECT_CONTEXT_FILES:
            file_path = project_root / rel_path_str
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    if file_size > CORE_FILE_MAX_SIZE_BYTES:
                        core_context_parts.append(
                            f"### Core File: `{rel_path_str}` (too large for full content, size: {file_size / 1024:.2f} KB)"
                        )
                        continue

                    content = file_path.read_text(encoding="utf-8")
                    lang = file_path.suffix.lstrip('.')

                    processed_content = ""
                    if lang == "py":
                        processed_content = extract_signatures_python(content)
                        core_context_parts.append(
                            f"### Core File Signatures: `{rel_path_str}`\n```{lang}\n{processed_content}\n```"
                        )
                    elif lang == "js":
                        processed_content = extract_signatures_js(content)
                        core_context_parts.append(
                            f"### Core File Signatures: `{rel_path_str}`\n```{lang}\n{processed_content}\n```"
                        )
                    elif is_text_file(file_path):  # Ensure it's truly text
                        core_context_parts.append(
                            f"### Core File Content: `{rel_path_str}`\n```{lang if lang else 'text'}\n{content}\n```"
                        )
                    else:
                        core_context_parts.append(
                            f"### Core File: `{rel_path_str}` (binary or unreadable)"
                        )
                except Exception as e:
                    core_context_parts.append(
                        f"### Core File: `{rel_path_str}` (Error reading: {e})"
                    )

        core_context_string = ""
        if core_context_parts:
            core_context_string = "---\n## Core Project Overview\n\n" + "\n\n".join(
                core_context_parts
            ) + "\n---"

        system_prompt = (
            "You are an expert software development assistant. Your task is to analyze a user's instructions and a list of project files. "
            "You will first be provided with a 'Core Project Overview' containing content or signatures of crucial project files to help you understand the project's nature. "
            "Then, you will receive a comprehensive list of all eligible files in the project, including whether they are 'signature candidates' (i.e., Python or JavaScript files from which signatures can be extracted). "
            "Based on the user's primary goal, identify the most relevant files from the *comprehensive list* that a developer would need to work on to achieve that goal. "
            "For each selected file, you must decide whether to include its 'full' content or only its 'signatures'. "
            "Choose 'signatures' for large code files, libraries, framework files, or when only an overview of functions/classes is sufficient. Choose 'full' for critical files needing detailed analysis or modification, or for non-code files (like READMEs, config files, etc.)."
            "Respond ONLY with a JSON array of objects, where each object has a 'path' (the full relative path of the file) and a 'type' (string: 'full' or 'signatures'). "
            "** Do not include any other text, explanation, or markdown formatting **. Your entire response must be a single valid JSON array."
            "\nExample response: [{\"path\": \"src/main.py\", \"type\": \"full\"}, {\"path\": \"core/utils.py\", \"type\": \"signatures\"}, {\"path\": \"tests/test_utils.py\", \"type\": \"full\"}]"
        )

        user_message = (
            f"{core_context_string}\n\n"
            f"User Instructions:\n---\n{request.user_goal}\n---\n\n"
            f"Comprehensive Project Files (path, is_signature_candidate):\n{json.dumps(file_list_all_eligible_paths, indent=2)}"
        )

        schema = {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "type": {"type": "string", "enum": ["full", "signatures"]},
                    },
                    "required": ["path", "type"],
                },
            }
        }

        try:
            # Use generate_structured_content
            content_str = lc.generate_structured_content(
                prompt=user_message,
                schema=schema,
                system_prompt=system_prompt,
            )

            if content_str is None:
                raise ValueError("LLM failed to generate structured content.")

            selected_files_raw = content_str

            if not isinstance(selected_files_raw, list) or not all(
                isinstance(f, dict) and "path" in f and "type" in f for f in selected_files_raw
            ):
                raise ValueError("LLM response was not a JSON array of objects with 'path' and 'type' keys.")

            # Convert relative paths from AI to absolute paths for the frontend
            selected_files_info = []
            for item in selected_files_raw:
                rel_path = Path(item["path"])
                abs_path = project_root / rel_path
                if abs_path.exists():
                    selection_type = item["type"].lower()
                    if selection_type not in ["full", "signatures"]:
                        print(
                            f"Warning: Invalid selection type '{selection_type}' for {item['path']} from LLM. Defaulting to 'full'."
                        )
                        selection_type = "full"

                    is_sig_candidate_in_list = next(
                        (
                            f["is_signature_candidate"]
                            for f in file_list_all_eligible_paths
                            if f["path"] == item["path"]
                        ),
                        False,
                    )
                    if selection_type == "signatures" and not is_sig_candidate_in_list:
                        print(
                            f"Warning: LLM selected 'signatures' for non-signature-candidate file {item['path']}. Defaulting to 'full'."
                        )
                        selection_type = "full"

                    selected_files_info.append({"path": str(abs_path), "type": selection_type})

            return {"status": "success", "files": selected_files_info}

        except Exception as e:
            trace_exception(e)
            raise HTTPException(
                status_code=500,
                detail=f"AI selection failed: {e}. Raw response: {str(e)}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing AI selection request: {e}",
        )

@app.post("/api/load_project_tree")
async def api_load_project_tree(request: LoadProjectTreeRequest):
    try:
        tree = build_file_tree_with_selection_info(request.folder_path, request.filters)
        return {"status": "success", "tree": tree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading tree: {e}")

@app.post("/api/generate_structure")
async def api_generate_structure(request: GenerateStructureRequest):
    root_path = Path(request.folder_path)
    if not root_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid folder_path.")
    
    hard_excluded_set = set(request.hard_excluded_paths)
    md_tree = generate_markdown_tree(str(root_path), hard_excluded_set)
    
    try:
        author = os.getlogin()
    except Exception:
        author = 'User'
        
    gen_dt = datetime.now()
    
    processed_prompt = request.custom_prompt
    processed_prompt = processed_prompt.replace("{FOLDER_NAME}", root_path.name)
    processed_prompt = processed_prompt.replace("{FOLDER_PATH}", str(root_path))
    processed_prompt = processed_prompt.replace("{DATE}", gen_dt.strftime("%Y-%m-%d"))
    processed_prompt = processed_prompt.replace("{TIME}", gen_dt.strftime("%H:%M:%S"))
    processed_prompt = processed_prompt.replace("{DATETIME}", gen_dt.strftime("%Y-%m-%d %H:%M:%S"))
    processed_prompt = processed_prompt.replace("{AUTHOR}", author)
    
    if request.loaded_doc_paths:
        doc_contents = ["\n\n---\n\n## Imported Documentation"]
        for doc_path_str in request.loaded_doc_paths:
            doc_path = Path(doc_path_str)
            if doc_path.is_file():
                try:
                    doc_contents.append(f"### Doc: `{doc_path.name}`\n```\n{doc_path.read_text(encoding='utf-8')}\n```")
                except Exception as e:
                    doc_contents.append(f"### Doc: `{doc_path.name}` [Error reading: {e}]")
            else:
                doc_contents.append(f"### Doc: `{doc_path.name}` [Not found on server]")
        processed_prompt += "\n".join(doc_contents)
    
    file_contents = []
    selected_files_map = {Path(info['path']).resolve(): info['type'] for info in request.selected_files_info}
    
    for file_path_obj, selection_type in sorted(selected_files_map.items()):
        if str(file_path_obj) in hard_excluded_set:
            continue
            
        relative_path = file_path_obj.relative_to(root_path).as_posix()
        file_contents.append(f"### `{relative_path}`")
        
        language = file_path_obj.suffix.lower().lstrip('.')
        
        try:
            content = file_path_obj.read_text(encoding="utf-8")
            
            if selection_type == "signatures":
                if language == "py": processed_content = extract_signatures_python(content)
                elif language == "js": processed_content = extract_signatures_js(content)
                else: processed_content = f"--- Signatures requested but not supported for .{language}. Showing full content. ---\n{content}"
            else:
                processed_content = content
            
            file_contents.append(f"```{language}\n{processed_content}\n```")

        except Exception as e:
            file_contents.append(f"```\nError reading file: {relative_path}\n{e}\n```")

    final_md_parts = [
        f"# Folder Structure: {root_path.name}",
        f"*(Generated: {gen_dt.strftime('%Y-%m-%d %H:%M:%S')})*",
        "---",
        "## Custom Instructions",
        processed_prompt,
        "---",
        "## Folder Tree",
        f"```text\n{md_tree}\n```",
        "---",
        "## File Contents",
        "\n\n".join(file_contents)
    ]
    
    final_md = "\n\n".join(final_md_parts)
    
    token_count = -1
    try:
        settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
        if settings.url and settings.model_name:
            lc = _get_lollms_client_instance()
            token_count = lc.count_tokens(final_md, model=lc.model_name)
    except Exception as e:
        print(f"Warning: Could not get token count using lollms_client: {e}")
        token_count = -1

    return {"status": "success", "markdown": final_md, "token_count": token_count}

def browse_folder():
    from PyQt5.QtWidgets import QApplication, QFileDialog
    import sys
    app = QApplication(sys.argv)
    folder_path = QFileDialog.getExistingDirectory(None, "Select a Project Folder")
    app.quit()
    return folder_path

@app.post("/api/browse_server_folder")
async def api_browse_server_folder():
    try:
        import asyncio
        # Run the PyQt5 application in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        folder_path = await loop.run_in_executor(None, browse_folder)
        if folder_path:
            return {"status": "success", "path": folder_path}
        else:
            return {"status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Server GUI (PyQt5) not available: {e}")

@app.get("/api/prompt_templates", response_model=List[Template])
async def get_prompt_templates():
    return load_prompt_templates()

@app.post("/api/save_template")
async def save_template(template: Template):
    templates = load_prompt_templates()
    existing_template_index = next((i for i, t in enumerate(templates) if t['name'] == template.name), None)
    
    if existing_template_index is not None:
        templates[existing_template_index] = template.model_dump()
    else:
        templates.append(template.model_dump())
    
    save_prompt_templates(templates)
    return {"status": "success", "message": f"Template '{template.name}' saved."}

@app.post("/api/delete_template")
async def delete_template(request: DeleteTemplateRequest):
    templates = load_prompt_templates()
    defaults = get_default_templates()
    
    is_default = any(t['name'] == request.name and t['content'] == request.content for t in defaults)
    
    if is_default:
        default_template = next((t for t in defaults if t['name'] == request.name), None)
        if default_template:
            templates = [t for t in templates if t['name'] != request.name]
            templates.append(default_template)
            templates.sort(key=lambda x: x['name'])
            save_prompt_templates(templates)
            return {"status": "reverted", "message": f"Template '{request.name}' reverted."}
    
    initial_len = len(templates)
    templates = [t for t in templates if t['name'] != request.name]
    
    if len(templates) < initial_len:
        save_prompt_templates(templates)
        return {"status": "deleted", "message": f"Template '{request.name}' deleted."}
    else:
        return {"status": "not_found", "message": f"Template '{request.name}' not found."}

@app.get("/api/prompts/export", response_model=List[Template])
async def export_prompts():
    """Exports all custom (non-default) prompt templates."""
    all_templates = load_prompt_templates()
    default_template_names = {t['name'] for t in get_default_templates()}
    custom_templates = [t for t in all_templates if t['name'] not in default_template_names]
    return custom_templates

@app.post("/api/prompts/import", response_model=Dict[str, int])
async def import_prompts(imported_templates: List[Template]):
    """Imports new prompt templates, overwriting existing ones with the same name."""
    if not imported_templates:
        raise HTTPException(status_code=400, detail="No prompt templates provided for import.")
    
    current_templates = load_prompt_templates()
    current_templates_map = {t['name']: t for t in current_templates}
    
    added_count = 0
    updated_count = 0

    for imp_template in imported_templates:
        if imp_template.name in current_templates_map:
            current_templates_map[imp_template.name] = imp_template.model_dump()
            updated_count += 1
        else:
            current_templates_map[imp_template.name] = imp_template.model_dump()
            added_count += 1
            
    save_prompt_templates(list(current_templates_map.values()))
    
    return {"added": added_count, "updated": updated_count}

static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir()

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = static_dir / "index.html"
    if not index_path.exists():
        return HTMLResponse(content="<h1>Fatal Error: index.html not found in static folder.</h1>", status_code=404)
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A simple script to demonstrate parsing host and port."
    )

    parser.add_argument('--host', 
                        type=str, 
                        default='localhost', # Changed default host to 'localhost'
                        help='The host to bind the server to (default: localhost)')

    parser.add_argument('--port', 
                        type=int, 
                        default=9601, 
                        help='The port to listen on (default: 9601)')

    args = parser.parse_args()

    HOST = args.host
    PORT = args.port
    
    def open_browser_after_delay():
        webbrowser.open(f"http://{HOST}:{PORT}")

    print("="*50)
    print(f" {APP_TITLE} - v{APP_VERSION} ".center(50, "="))
    print("="*50)

    # Start the browser opening in a separate thread, non-blocking
    browser_thread = threading.Timer(1.25, open_browser_after_delay)
    browser_thread.daemon = True 
    browser_thread.start()
    
    print(f"\nServer starting at http://{HOST}:{PORT}")
    print("Your web browser should open automatically.")
    print("If not, please open the URL manually.")
    print("\nPress Ctrl+C to stop the server.")
    
    try:
        # Use uvicorn.Config and uvicorn.Server for programmatic control
        # This will run the server in the main thread and handle signals gracefully.
        config = Config(app, host=HOST, port=PORT, log_level="warning")
        server = Server(config=config)
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        # Server.run() handles its own shutdown on KeyboardInterrupt
        # No explicit server.stop() is needed here as server.run() completes.