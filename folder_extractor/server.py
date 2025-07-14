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
import httpx

try:
    import pipmaster
except ImportError:
    print("Pipmaster not found. Installing...")
    os.system(f"{sys.executable} -m pip install pipmaster")
    import pipmaster

pipmaster.ensure_packages(["fastapi", "uvicorn", "python-multipart", "httpx"])

from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

APP_TITLE = "Folder Structure Extractor Web App"
APP_VERSION = "3.3.0"
CONFIG_DIR = Path.home() / ".config" / "folder_extractor_web"
PROMPTS_FILE = CONFIG_DIR / "prompt_templates.json"
PROJECTS_FILE = CONFIG_DIR / "projects.json"
LLM_SETTINGS_FILE = CONFIG_DIR / "llm_settings.json"

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
    "Large Media Files": { "extensions": [".png", ".jpg", ".gif", ".mp4", ".mov", ".mp3", ".pdf", ".doc", ".docx", ".ppt", ".xls", ".psd", ".ai", ".svg"], "folders": [], "patterns": [] }
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

def load_prompt_templates() -> List[Dict]:
    return load_json_file(PROMPTS_FILE, get_default_templates())

def save_prompt_templates(templates: List[Dict]):
    save_json_file(PROMPTS_FILE, templates)

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

@app.get("/api/settings/llm", response_model=LLMSettings)
async def get_llm_settings():
    return load_json_file(LLM_SETTINGS_FILE, LLMSettings().model_dump())

@app.post("/api/settings/llm", status_code=204)
async def save_llm_settings(settings: LLMSettings):
    save_json_file(LLM_SETTINGS_FILE, settings.model_dump())

async def proxy_lollms_request(endpoint: str, payload: dict, method: str = "POST"):
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.url:
        raise HTTPException(status_code=400, detail="LLM service URL is not configured.")

    base_url = settings.url.rsplit('/v1/', 1)[0]
    # Adjust for base URLs that might not have /v1/
    if endpoint=="count_tokens" or endpoint=="context_size":
        base_url = base_url + "/v1"
    elif not base_url.endswith('/v1'):
        base_url = settings.url.rstrip('/')

    target_url = f"{base_url}/{endpoint}"

    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(target_url, headers=headers)
            else:
                response = await client.post(target_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not connect to LLM service at {target_url}. Error: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"LLM service returned error: {e.response.text}")
    except (ValueError, json.JSONDecodeError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"Could not parse LLM response for {endpoint}. Error: {e}")


@app.get("/api/context_size")
async def get_context_size():
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.model_name:
         raise HTTPException(status_code=400, detail="No model selected in settings.")
    response = await proxy_lollms_request("context_size", {"model": settings.model_name})
    return {"context_size": response.get("context_size", 0)}

@app.post("/api/count_tokens")
async def count_tokens(request: TokenCountRequest):
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.model_name:
         raise HTTPException(status_code=400, detail="No model selected in settings.")
    response = await proxy_lollms_request("count_tokens", {"model": settings.model_name, "text": request.text})
    return {"count": response.get("count", -1)}

@app.get("/api/llm_models", response_model=List[str])
async def get_llm_models():
    try:
        models_data = await proxy_lollms_request("models", {}, method="GET")
        model_ids = [model['id'] for model in models_data.get('data', [])]
        return sorted(model_ids)
    except HTTPException as e:
        # Re-raise the exception to be handled by FastAPI's exception handling
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching models: {e}")


@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.url:
        raise HTTPException(status_code=400, detail="LLM service URL is not configured.")

    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    payload = {
        "model": settings.model_name or "lollms-chat",
        "messages": [msg.model_dump() for msg in request.messages],
        "temperature": 0.1,
        "max_tokens": 4096,
        "stream": True
    }

    async def stream_generator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", settings.url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.RequestError as e:
            error_message = f"Error connecting to LLM service: {e}"
            print(error_message)
            yield f"data: {json.dumps({'error': error_message})}\n\n"
        except httpx.HTTPStatusError as e:
            error_message = f"LLM service returned error: {e.response.status_code} - {e.response.text}"
            print(error_message)
            yield f"data: {json.dumps({'error': error_message})}\n\n"
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            print(error_message)
            yield f"data: {json.dumps({'error': error_message})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/api/llm_select_files")
async def llm_select_files(request: LLMSelectRequest):
    settings = LLMSettings(**load_json_file(LLM_SETTINGS_FILE, {}))
    if not settings.url:
        raise HTTPException(status_code=400, detail="LLM service URL is not configured.")

    try:
        tree_nodes = build_file_tree_with_selection_info(request.project_path, request.filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading project structure: {e}")

    file_list = []
    def flatten_tree(nodes):
        for node in nodes:
            path = Path(node["path"])
            relative_path = path.relative_to(request.project_path)
            if not node["is_dir"]:
                file_list.append(str(relative_path).replace('\\', '/'))
            if node.get("children"):
                flatten_tree(node["children"])
    
    if tree_nodes:
        flatten_tree(tree_nodes[0].get("children", []))
    
    if not file_list:
        return JSONResponse(content={"status": "success", "files": []})

    system_prompt = (
        "You are an expert software development assistant. Your task is to analyze a user's instructions and a list of project files. "
        "First, determine the user's primary goal from their instructions (e.g., 'add a feature', 'fix a bug', 'refactor code'). "
        "Then, identify the most relevant files from the list that a developer would need to work on to achieve that goal. "
        "Respond ONLY with a JSON array of strings, where each string is the full relative path of a relevant file. "
        "Do not include any other text, explanation, or markdown formatting. Your entire response must be a single valid JSON array."
        "\nExample response: [\"src/main.py\", \"core/utils.py\", \"tests/test_utils.py\"]"
    )

    user_message = f"User Instructions:\n---\n{request.user_goal}\n---\n\nProject Files:\n{json.dumps(file_list, indent=2)}"

    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    payload = {
        "model": settings.model_name or "lollms-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0,
        "max_tokens": 2048
    }
    
    content_str = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(settings.url, json=payload, headers=headers)
        response.raise_for_status()
        llm_response = response.json()
        content_str = llm_response['choices'][0]['message']['content']
        
        match = re.search(r'\[.*\]', content_str, re.DOTALL)
        if not match:
            raise ValueError("LLM response did not contain a valid JSON array.")
        
        selected_files = json.loads(match.group(0))

        if not isinstance(selected_files, list) or not all(isinstance(f, str) for f in selected_files):
            raise ValueError("LLM response was not a JSON array of strings.")
            
        project_root = Path(request.project_path)
        absolute_paths = [str(project_root / Path(f)) for f in selected_files if (project_root / Path(f)).exists()]

        return {"status": "success", "files": absolute_paths}

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not connect to LLM service at {settings.url}. Error: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"LLM service returned error: {e.response.text}")
    except (ValueError, json.JSONDecodeError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"Could not parse LLM response. Error: {e}. Raw response: {content_str}")

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
    
    return {"status": "success", "markdown": final_md}

@app.post("/api/browse_server_folder")
async def api_browse_server_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory(title="Select a Project Folder")
        root.destroy()
        if folder_path:
            return {"status": "success", "path": folder_path}
        else:
            return {"status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Server GUI (Tkinter) not available: {e}")

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
    import uvicorn
    
    HOST = "127.0.0.1"
    PORT = 8765
    
    def run_server():
        uvicorn.run(app, host=HOST, port=PORT, log_level="warning")

    def open_browser():
        webbrowser.open(f"http://{HOST}:{PORT}")

    print("="*50)
    print(f" {APP_TITLE} - v{APP_VERSION} ".center(50, "="))
    print("="*50)

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    threading.Timer(1.25, open_browser).start()
    
    print(f"\nServer starting at http://{HOST}:{PORT}")
    print("Your web browser should open automatically.")
    print("If not, please open the URL manually.")
    print("\nPress Ctrl+C to stop the server.")
    
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down server.")
