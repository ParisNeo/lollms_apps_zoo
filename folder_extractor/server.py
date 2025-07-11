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

try:
    import pipmaster
except ImportError:
    print("Pipmaster not found. Installing...")
    os.system(f"{sys.executable} -m pip install pipmaster")
    import pipmaster

pipmaster.ensure_packages(["fastapi", "uvicorn", "python-multipart"])

from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

APP_TITLE = "Folder Structure Extractor Web App"
APP_VERSION = "2.8.5"
CONFIG_DIR = Path.home() / ".config" / "folder_extractor_web"
PROMPTS_FILE = CONFIG_DIR / "prompt_templates.json"

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
    if not PROMPTS_FILE.exists():
        templates = get_default_templates()
        save_prompt_templates(templates)
        return templates
    try:
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return get_default_templates()

def save_prompt_templates(templates: List[Dict]):
    try:
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2)
    except IOError as e:
        print(f"Error saving prompt templates: {e}")

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
    
    # --- Process Prompt and Placeholders ---
    try:
        author = os.getlogin()
    except Exception:
        author = 'User'
        
    gen_dt = datetime.now()
    
    # Start with the base prompt and replace placeholders
    processed_prompt = request.custom_prompt
    processed_prompt = processed_prompt.replace("{FOLDER_NAME}", root_path.name)
    processed_prompt = processed_prompt.replace("{FOLDER_PATH}", str(root_path))
    processed_prompt = processed_prompt.replace("{DATE}", gen_dt.strftime("%Y-%m-%d"))
    processed_prompt = processed_prompt.replace("{TIME}", gen_dt.strftime("%H:%M:%S"))
    processed_prompt = processed_prompt.replace("{DATETIME}", gen_dt.strftime("%Y-%m-%d %H:%M:%S"))
    processed_prompt = processed_prompt.replace("{AUTHOR}", author)
    
    # Append documentation content to the processed prompt
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
    
    # --- Process File Contents ---
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

    # --- Assemble Final Markdown ---
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
        templates[existing_template_index] = template.dict()
    else:
        templates.append(template.dict())
    
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