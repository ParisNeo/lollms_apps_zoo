# -*- coding: utf-8 -*-
# Project: folder_extractor_webapp
# Author: ParisNeo with gemini 2.5 (and significant user modifications)
# Description: FastAPI backend for folder_extractor web application.

import sys
import fnmatch
import datetime
import re
import json
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict, Any, Union
import functools
import os
import traceback
from collections import defaultdict

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import asyncio

try:
    from PyQt5.QtWidgets import QApplication, QFileDialog
    _PYQT5_AVAILABLE = True
except ImportError:
    _PYQT5_AVAILABLE = False
    print("WARNING: PyQt5 not found on server. 'Browse Server Folder' functionality will be disabled.")

class Template(BaseModel):
    name: str
    content: str

DEFAULT_AI_PROMPT_TEMPLATES_RAW = [
    {"name": "AI: Add New Feature", "content": "..."}, # Truncated for brevity
    # ... other templates
]
_user_prompt_templates: List[Template] = [Template(**t_dict) for t_dict in DEFAULT_AI_PROMPT_TEMPLATES_RAW]
executor = ThreadPoolExecutor(max_workers=5)

DEFAULT_EXCLUDED_FOLDERS: Set[str] = {".git", "__pycache__", "node_modules", "target", "dist", "build", "venv", ".venv", "env", ".env", ".vscode", ".idea", "logs", "temp", "tmp", "bin", "obj", "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", "*.egg-info"}
DEFAULT_EXCLUDED_EXTENSIONS: Set[str] = {".pyc", ".pyo", ".pyd", ".o", ".obj", ".class", ".dll", ".so", ".exe", ".bin", ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".war", ".ear", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".ico", ".mp3", ".wav", ".ogg", ".mp4", ".avi", ".mov", ".webm", ".db", ".sqlite", ".sqlite3", ".lock", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".ttf", ".otf", ".woff", ".woff2", ".DS_Store", ".ipynb_checkpoints"}
ALLOWED_TEXT_EXTENSIONS: Set[str] = {".txt", ".md", ".markdown", ".rst", ".adoc", ".asciidoc", ".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass", ".less", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".swift", ".kt", ".kts", ".php", ".rb", ".pl", ".pm", ".lua", ".sh", ".bash", ".zsh", ".bat", ".ps1", ".psm1", ".sql", ".r", ".dart", ".groovy", ".scala", ".clj", ".cljs", ".cljc", ".edn", ".vb", ".vbs", ".f", ".for", ".f90", ".f95", ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".csv", ".tsv", ".env", ".dockerfile", "dockerfile", ".tf", ".tfvars", ".hcl", ".gradle", ".pom", ".csproj", ".vbproj", ".sln", ".gitignore", ".gitattributes", ".npmrc", ".yarnrc", ".editorconfig", ".babelrc", ".eslintrc", ".prettierrc", ".stylelintrc", ".makefile", "makefile", "Makefile", "CMakeLists.txt", ".tex", ".bib", ".sty", ".graphql", ".gql", ".vue", ".svelte", ".astro", ".liquid", ".njk", ".jinja", ".jinja2", ".patch", ".diff"}
TREE_BRANCH, TREE_LAST, TREE_VLINE, TREE_SPACE = "├─ ", "└─ ", "│  ", "   "
FOLDER_ICON_STR, FILE_ICON_STR = "📁", "📄"
DEFAULT_MAX_FILE_SIZE_MB = 1.0
PRESET_EXCLUSIONS: Dict[str, List[str]] = {
    "Python Project": ["*.pyc", "__pycache__/", "venv/"], # Truncated
    # ... other presets
}
PRESET_OPTIONS = sorted(PRESET_EXCLUSIONS.keys())
PLACEHOLDERS = {
    "{FOLDER_NAME}": lambda folder_path: Path(folder_path).name if folder_path and Path(folder_path).exists() else "UnknownProject",
    "{FOLDER_PATH}": lambda folder_path: folder_path if folder_path else "N/A",
    "{DATE}": lambda _: datetime.datetime.now().strftime('%Y-%m-%d'),
    "{TIME}": lambda _: datetime.datetime.now().strftime('%H:%M:%S'),
    "{DATETIME}": lambda _: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "{AUTHOR}": lambda _: os.getenv('USERNAME') or os.getenv('USER', 'Unknown Author'),
}
def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', filename).strip(' _.') or "default"
def apply_placeholders(text: str, folder_path: str, user_request: str = "[User-defined request should go here]") -> str:
    text = text.replace("{USER_REQUEST}", user_request)
    for key, func in PLACEHOLDERS.items():
        try: text = text.replace(key, str(func(folder_path)))
        except Exception as e: print(f"Warning: placeholder {key}: {e}")
    return text

class FolderProcessor:
    def __init__(self):
        self._active_excluded_folders: Set[str] = set()
        self._active_excluded_extensions: Set[str] = set()
        self._active_excluded_patterns: List[str] = []
        self._active_include_patterns: List[str] = []
        self._max_file_size_bytes: int = 0
        self._root_folder: Path = Path(".")

    def setup_exclusions_and_limits(
        self, selected_preset_names: List[str], custom_folders_str: str, custom_exts_str: str,
        custom_patterns_str: str, dynamic_patterns_list: List[str], custom_inclusions_str: str,
        max_size_mb: float, root_folder_for_context: Optional[Path] = None
    ):
        self._root_folder = (root_folder_for_context or Path(".")).resolve()
        self._active_excluded_folders = set(DEFAULT_EXCLUDED_FOLDERS)
        self._active_excluded_extensions = set(DEFAULT_EXCLUDED_EXTENSIONS)
        self._active_excluded_patterns = []
        self._active_include_patterns = [p.strip().replace("\\", "/") for p in custom_inclusions_str.split(',') if p.strip()]
        
        for preset_name in selected_preset_names:
            if preset_name in PRESET_EXCLUSIONS:
                self._active_excluded_patterns.extend(PRESET_EXCLUSIONS[preset_name])
        
        self._active_excluded_folders.update(f.strip().lower() for f in custom_folders_str.split(',') if f.strip())
        self._active_excluded_extensions.update(e.strip().lower() for e in custom_exts_str.split(',') if e.strip() and e.strip().startswith('.'))
        self._active_excluded_patterns.extend(p.strip() for p in custom_patterns_str.split(',') if p.strip())
        if dynamic_patterns_list: self._active_excluded_patterns.extend(dynamic_patterns_list)
        self._active_excluded_patterns = sorted(list(set(self._active_excluded_patterns)))
        self._max_file_size_bytes = int(max(0.01, max_size_mb) * 1024 * 1024)

    def _is_excluded(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        context_root = current_root_override or self._root_folder
        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower() if item.is_file() else ""
        if (item.is_dir() and item_name_lower in self._active_excluded_folders) or \
           (item.is_file() and item_suffix_lower in self._active_excluded_extensions):
            return True
        try:
            rel_path_str = str(item.resolve().relative_to(context_root).as_posix()) if item.resolve().is_relative_to(context_root) else item.name
        except (AttributeError, ValueError): rel_path_str = item.name
        for pattern in self._active_excluded_patterns:
            if (pattern.endswith('/') and item.is_dir() and fnmatch.fnmatchcase(item.name, pattern[:-1])) or \
               (pattern.endswith('/') and rel_path_str.startswith(pattern[:-1] + "/")) or \
               (not pattern.endswith('/') and fnmatch.fnmatchcase(item.name, pattern)) or \
               ("/" in pattern and fnmatch.fnmatchcase(rel_path_str, pattern)):
                return True
        return False

    def _is_included_by_filter(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        if not self._active_include_patterns: return True
        context_root = current_root_override or self._root_folder
        try:
            rel_path_str = str(item.resolve().relative_to(context_root).as_posix()) if item.resolve().is_relative_to(context_root) else item.name
        except (AttributeError, ValueError): rel_path_str = item.name
        for pattern in self._active_include_patterns:
            if fnmatch.fnmatchcase(rel_path_str, pattern): return True
            if item.is_dir() and "/" in rel_path_str:
                try:
                    current_path_obj = Path(rel_path_str)
                    if fnmatch.fnmatchcase(str(current_path_obj), pattern) or \
                       (pattern.endswith("/") and fnmatch.fnmatchcase(str(current_path_obj), pattern[:-1])): return True
                    for parent_part_path in current_path_obj.parents:
                        if str(parent_part_path) == ".": continue
                        if fnmatch.fnmatchcase(str(parent_part_path), pattern) or \
                           (pattern.endswith("/") and fnmatch.fnmatchcase(str(parent_part_path), pattern[:-1])): return True
                except: pass
        return False

    def _is_text_file(self, file: Path) -> bool:
        return file.suffix.lower() in ALLOWED_TEXT_EXTENSIONS

    def _read_file_content(self, file: Path) -> str:
        try:
            if file.stat().st_size > self._max_file_size_bytes: return f"[File omitted: Exceeds size limit ({self._max_file_size_bytes/(1024*1024):.2f} MB)]"
            if file.stat().st_size == 0: return "[Empty file]"
            try: content = file.read_text(encoding="utf-8", errors='strict')
            except UnicodeDecodeError:
                for enc in ['latin-1', 'cp1252']:
                    try: content = file.read_text(encoding=enc); print(f"Warning: {file.name} decoded as {enc}."); break
                    except: pass
                else: return "[Error: Could not decode]"
            except Exception as e: return f"[Error reading: {e}]"
            if any(len(line) > 5000 for line in content.splitlines()): print(f"Warning: {file.name} has long lines.")
            return content or "[File appears empty]"
        except OSError as e: return f"[OS error: {e}]"
        except Exception as e: print(f"Unexpected error reading {file.name}: {e}\n{traceback.format_exc()}"); return "[Unexpected error]"

    def build_file_tree_json(self, folder_path_str: str, filter_settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        root_path = Path(folder_path_str).resolve()
        if not root_path.is_dir(): raise ValueError(f"Path is not a directory: {folder_path_str}")
        self.setup_exclusions_and_limits(
            filter_settings.get("selected_presets", []), filter_settings.get("custom_folders", ""),
            filter_settings.get("custom_extensions", ""), filter_settings.get("custom_patterns", ""),
            [p.strip() for p in filter_settings.get("dynamic_patterns", "").split(',') if p.strip()],
            filter_settings.get("custom_inclusions", ""), filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB), root_path
        )
        return [{"name": root_path.name, "path": str(root_path.as_posix()), "is_dir": True, "is_text": False, "can_be_checked": True, "children": self._collect_tree_data_recursive(root_path, root_path)}]

    def _collect_tree_data_recursive(self, current_dir_path: Path, root_scan_path: Path) -> List[Dict[str, Any]]:
        items_data = []
        try: paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError) as e:
            return [{"name": f"[{'Permission Denied' if isinstance(e,PermissionError) else 'OS Error'}: {current_dir_path.name}]", "path": str(current_dir_path.as_posix()), "is_dir": True, "is_text": False, "can_be_checked": False, "error": True}]
        for path_obj in paths_in_dir:
            is_excluded = self._is_excluded(path_obj, root_scan_path)
            is_included = self._is_included_by_filter(path_obj, root_scan_path)
            item_data = {"name": path_obj.name, "path": str(path_obj.as_posix()), "is_dir": path_obj.is_dir(), "children": [], "error": False, "can_be_checked": True}
            if item_data["is_dir"]:
                item_data["is_text"] = False
                item_data["children"] = self._collect_tree_data_recursive(path_obj, root_scan_path)
                item_data["can_be_checked"] = not is_excluded or is_included
            else:
                item_data["is_text"] = self._is_text_file(path_obj)
                if item_data["is_text"]:
                    try: file_too_large = path_obj.stat().st_size > self._max_file_size_bytes
                    except OSError: file_too_large = True
                    item_data["can_be_checked"] = not is_excluded and is_included and not file_too_large
                else: item_data["can_be_checked"] = False
            items_data.append(item_data)
        return items_data

    # NEW helper to get all displayable paths for the full tree structure
    def _get_all_displayable_paths(self, current_dir_path: Path, root_scan_path: Path) -> List[Path]:
        all_paths = []
        try:
            paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError):
            return [] # Skip on error for this purpose

        for path_obj in paths_in_dir:
            is_excluded = self._is_excluded(path_obj, root_scan_path)
            is_included_by_filter = self._is_included_by_filter(path_obj, root_scan_path)

            # Logic to decide if it's displayable (similar to can_be_checked logic for files, but simpler for display)
            is_displayable = True 
            if path_obj.is_file():
                if not self._is_text_file(path_obj): # Don't display binary files in the markdown tree either
                    is_displayable = False
                if is_excluded and not is_included_by_filter: # Hide if excluded and not specifically included
                    is_displayable = False
            elif path_obj.is_dir(): # For directories
                if is_excluded and not is_included_by_filter:
                    is_displayable = False
            
            if is_displayable:
                all_paths.append(path_obj.resolve())
                if path_obj.is_dir():
                    all_paths.extend(self._get_all_displayable_paths(path_obj, root_scan_path))
        return all_paths


    def _generate_tree_markdown_from_paths(self, root_path: Path, paths_for_tree_structure: List[str]) -> List[str]:
        if not paths_for_tree_structure:
            return ["*No items to display in the file tree based on filters.*"] # Modified message
        resolved_root_path = root_path.resolve()
        hierarchy: Dict[str, Any] = {}
        all_nodes_to_represent = set()

        for p_str_raw in paths_for_tree_structure:
            p = Path(p_str_raw).resolve()
            all_nodes_to_represent.add(p)
            try:
                if p.is_relative_to(resolved_root_path):
                    current_parent = resolved_root_path
                    for part in p.relative_to(resolved_root_path).parts[:-1]:
                        current_parent = current_parent / part
                        all_nodes_to_represent.add(current_parent)
            except (ValueError, AttributeError): pass
        if str(resolved_root_path.as_posix()) in paths_for_tree_structure or resolved_root_path in all_nodes_to_represent :
            all_nodes_to_represent.add(resolved_root_path)

        sorted_nodes = sorted(list(all_nodes_to_represent), key=lambda x_path: str(x_path.relative_to(resolved_root_path) if x_path.is_relative_to(resolved_root_path) else x_path))

        for node_path_resolved in sorted_nodes:
            try: parts = node_path_resolved.relative_to(resolved_root_path).parts if node_path_resolved.is_relative_to(resolved_root_path) else ( (node_path_resolved.name,) if node_path_resolved != resolved_root_path else () )
            except (ValueError, AttributeError): parts = (node_path_resolved.name,) if node_path_resolved != resolved_root_path else ()
            current_level = hierarchy
            for part in parts: current_level = current_level.setdefault(part, {})
            current_level["_isfile_"] = node_path_resolved.is_file()
        if not parts and resolved_root_path in all_nodes_to_represent: hierarchy["_isfile_"] = resolved_root_path.is_file()

        def format_level(level_dict: Dict[str, Any], current_prefix: str) -> List[str]:
            lines, items = [], {k:v for k,v in level_dict.items() if not k.startswith("_")}
            sorted_names = sorted(items.keys(), key=lambda k: (items[k].get("_isfile_", False), k.lower()))
            for i, name in enumerate(sorted_names):
                node, last = items[name], (i == len(sorted_names) - 1)
                is_file, icon = node.get("_isfile_", False), FILE_ICON_STR if node.get("_isfile_", False) else FOLDER_ICON_STR
                lines.append(f"{current_prefix}{TREE_LAST if last else TREE_BRANCH}{icon} {name}{'' if is_file else '/'}")
                children = {k_c: v_c for k_c, v_c in node.items() if not k_c.startswith("_")}
                if not is_file and children:
                    lines.extend(format_level(children, current_prefix + (TREE_SPACE if last else TREE_VLINE)))
            return lines
        return [f"{FOLDER_ICON_STR} {resolved_root_path.name}/"] + format_level(hierarchy, "")

    def _generate_file_contents_markdown(self, root_folder: Path, selected_file_paths_abs: List[str]) -> List[str]: # Takes explicitly selected files
        content_lines = ["", "---", "", "## File Contents"]
        if not selected_file_paths_abs:
            content_lines.append("\n*No files selected in the tree to show content.*")
            return content_lines
        resolved_root_folder, files_for_content = root_folder.resolve(), []
        for path_str in selected_file_paths_abs:
            path = Path(path_str)
            if path.is_file() and self._is_text_file(path):
                try:
                    if path.stat().st_size <= self._max_file_size_bytes: files_for_content.append(path)
                except OSError as e: print(f"Warning: Stat failed for {path_str}: {e}")
        files_for_content.sort(key=lambda p: str(p.resolve().relative_to(resolved_root_folder) if p.resolve().is_relative_to(resolved_root_folder) else p.name).lower())
        for file_path in files_for_content:
            try: rel_path_str = str(file_path.resolve().relative_to(resolved_root_folder).as_posix())
            except: rel_path_str = file_path.name
            content_lines.append(f"\n### `{rel_path_str}`")
            file_content = self._read_file_content(file_path)
            lang = (file_path.suffix[1:] if file_path.suffix else "text").lower()
            lang = "".join(c for c in lang if c.isalnum()) or "text"
            aliases = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript', 'jsx': 'javascript', 'md': 'markdown', 'sh': 'bash', 'yml': 'yaml', 'dockerfile': 'docker', 'h': 'c', 'hpp': 'cpp', 'cs': 'csharp', 'rb': 'ruby', 'pl': 'perl', 'kt': 'kotlin', 'rs': 'rust', 'go': 'golang', 'html': 'html', 'css': 'css', 'scss': 'scss', 'vue': 'vue', 'java': 'java', 'xml': 'xml', 'json': 'json', 'sql': 'sql', 'php': 'php'}
            lang = aliases.get(lang, lang)
            content_lines.extend([f"```{lang}", *(file_content.splitlines() if file_content else [""]), "```"])
        return content_lines

    def generate_structure_text(
        self, folder_path_str: str, filter_settings: Dict[str, Any], custom_prompt: str = "",
        documentation_content: str = "", selected_file_paths_abs: Optional[List[str]] = None,
    ) -> str:
        try:
            self._root_folder = Path(folder_path_str).resolve()
            if not self._root_folder.is_dir(): raise ValueError(f"Path not dir: {self._root_folder}")
        except Exception as e: raise ValueError(f"Path error '{folder_path_str}': {e}")

        self.setup_exclusions_and_limits( # This setup is for filtering what's displayable/content-readable
            filter_settings.get("selected_presets", []), filter_settings.get("custom_folders", ""),
            filter_settings.get("custom_extensions", ""), filter_settings.get("custom_patterns", ""),
            [p.strip() for p in filter_settings.get("dynamic_patterns", "").split(',') if p.strip()],
            filter_settings.get("custom_inclusions", ""), filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB), self._root_folder
        )

        # Get all paths that WOULD be displayed in the tree based on initial filters
        all_displayable_paths_objects = self._get_all_displayable_paths(self._root_folder, self._root_folder)
        all_displayable_paths_str = [str(p.as_posix()) for p in all_displayable_paths_objects]
        
        # Generate the Markdown tree structure using ALL displayable paths
        tree_lines = self._generate_tree_markdown_from_paths(self._root_folder, all_displayable_paths_str)

        structure_output_lines = [f"# Folder Structure: {self._root_folder.name}", f"*(Generated: {datetime.datetime.now():%Y-%m-%d %H:%M:%S})*", "", "```text", *tree_lines, "```"]
        
        # Generate content ONLY for explicitly user-selected files
        content_output_lines = self._generate_file_contents_markdown(self._root_folder, selected_file_paths_abs or [])
        
        full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)
        final_prompt_parts = []
        if documentation_content and documentation_content.strip(): final_prompt_parts.append("## Imported Documentation\n\n" + documentation_content.strip())
        if custom_prompt and custom_prompt.strip(): final_prompt_parts.append("## Custom Instructions\n\n" + custom_prompt.strip())
        if final_prompt_parts: full_output += "\n\n---\n\n" + "\n\n---\n\n".join(final_prompt_parts)
        return full_output.strip()

# --- FastAPI App Setup and the rest of server.py remains largely the same ---
app = FastAPI(title="Folder Structure Extractor Web App", version="2.7.1")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
folder_processor = FolderProcessor()

class FilterSettings(BaseModel):
    selected_presets: List[str] = []; custom_folders: str = ""; custom_extensions: str = ""; custom_patterns: str = ""
    dynamic_patterns: str = ""; custom_inclusions: str = ""; max_file_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB
class LoadTreeRequest(BaseModel): folder_path: str; filters: FilterSettings
class GenerateRequest(BaseModel):
    folder_path: str; filters: FilterSettings; selected_paths_abs: List[str]
    custom_prompt: str; loaded_doc_paths: List[str]
class EnvironmentSettings(BaseModel): # Truncated for brevity
    folder_path: str; selected_presets: List[str]; custom_folders: str; custom_extensions: str; custom_patterns: str
    dynamic_patterns: str; custom_inclusions: str; max_file_size_mb: float; save_output_checked: bool
    custom_prompt: str; current_theme_file: str = "default_light.qss"; prompt_templates: List[Template]
    loaded_doc_paths: List[str]; checked_tree_paths_str_abs: List[str]; version: str = "2.7.1"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open("static/index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())

@app.post("/api/load_project_tree")
async def load_project_tree(request: LoadTreeRequest):
    if not request.folder_path: raise HTTPException(400, "Folder path empty.")
    folder_path = Path(request.folder_path)
    if not folder_path.is_dir(): raise HTTPException(400, f"Not a directory: {request.folder_path}")
    try:
        tree_data = await asyncio_to_thread(folder_processor.build_file_tree_json, request.folder_path, request.filters.dict())
        return JSONResponse(content={"tree": tree_data})
    except Exception as e: print(f"Error loading tree for {request.folder_path}: {e}\n{traceback.format_exc()}"); raise HTTPException(500, f"Failed to load tree: {e}")

def _get_folder_path_from_pyqt5_dialog():
    app_instance = QApplication.instance() or QApplication(sys.argv)
    return QFileDialog.getExistingDirectory(None, "Select Folder on Server")

@app.post("/api/browse_server_folder")
async def browse_server_folder():
    if not _PYQT5_AVAILABLE: raise HTTPException(500, "PyQt5 not available on server.")
    try:
        path = await asyncio_to_thread(_get_folder_path_from_pyqt5_dialog)
        return {"status": "success" if path else "cancelled", "path": path}
    except Exception as e: print(f"PyQt5 dialog error: {e}\n{traceback.format_exc()}"); raise HTTPException(500, f"Server dialog error: {e}")

@app.post("/api/generate_structure")
async def generate_structure(request: GenerateRequest):
    if not request.folder_path: raise HTTPException(400, "Folder path empty.")
    try:
        doc_content = ""
        for path_str in request.loaded_doc_paths:
            path = Path(path_str)
            if path.is_file():
                try: doc_content += f"\n---\n**Doc: `{path.name}`**\n\n{path.read_text(encoding='utf-8', errors='ignore').strip()}\n---"
                except Exception as e: doc_content += f"\n---\n**Doc: `{path.name}` [Error: {e}]**\n---"; print(f"Doc read error {path_str}: {e}")
        prompt = apply_placeholders(request.custom_prompt, request.folder_path)
        text = await asyncio_to_thread(folder_processor.generate_structure_text, request.folder_path, request.filters.dict(), prompt, doc_content, request.selected_paths_abs)
        return JSONResponse(content={"markdown": text})
    except Exception as e: print(f"Error generating: {e}\n{traceback.format_exc()}"); raise HTTPException(500, f"Failed to generate: {e}")

@app.get("/api/prompt_templates")
async def get_prompt_templates(): return JSONResponse(content=[t.dict() for t in _user_prompt_templates])
@app.post("/api/save_template")
async def save_template(template: Template):
    global _user_prompt_templates
    is_default = any(td['name'] == template.name and td['content'] == template.content for td in DEFAULT_AI_PROMPT_TEMPLATES_RAW)
    if is_default: # Revert/ensure original default
        updated = False
        for i, t_current in enumerate(_user_prompt_templates):
            if t_current.name == template.name: _user_prompt_templates[i] = template; updated = True; break
        if not updated: _user_prompt_templates.append(template)
        _user_prompt_templates.sort(key=lambda t: t.name.lower())
        return JSONResponse({"status": "warning", "message": f"Template '{template.name}' matches default."})
    
    found_idx = next((i for i, t in enumerate(_user_prompt_templates) if t.name == template.name), -1)
    if found_idx != -1: _user_prompt_templates[found_idx] = template
    else: _user_prompt_templates.append(template)
    _user_prompt_templates.sort(key=lambda t: t.name.lower())
    return JSONResponse({"status": "success", "message": f"Template '{template.name}' saved."})

@app.post("/api/delete_template")
async def delete_template(template: Template):
    global _user_prompt_templates
    is_default_content = any(td['name'] == template.name and td['content'] == template.content for td in DEFAULT_AI_PROMPT_TEMPLATES_RAW)
    if is_default_content: raise HTTPException(403, f"Cannot delete original default template '{template.name}'.")
    
    initial_len = len(_user_prompt_templates)
    _user_prompt_templates = [t for t in _user_prompt_templates if t.name != template.name]
    if len(_user_prompt_templates) < initial_len:
        # If a *customized* default was deleted, ensure the original is still there.
        original_default = next((Template(**d) for d in DEFAULT_AI_PROMPT_TEMPLATES_RAW if d['name'] == template.name), None)
        if original_default and not any(t.name == original_default.name for t in _user_prompt_templates):
            _user_prompt_templates.append(original_default)
            _user_prompt_templates.sort(key=lambda t: t.name.lower())
        return JSONResponse({"status": "success", "message": f"Template '{template.name}' deleted/reverted."})
    raise HTTPException(404, f"Template '{template.name}' not found.")

@app.post("/api/save_environment")
async def save_environment(settings: EnvironmentSettings): return JSONResponse(content=settings.dict())
@app.post("/api/load_documentation_content")
async def load_documentation_content(doc_paths: List[str]):
    docs = []
    for p_str in doc_paths:
        p = Path(p_str)
        if p.is_file():
            try: docs.append(f"\n---\n**Doc: `{p.name}`**\n\n{p.read_text(encoding='utf-8',errors='ignore').strip()}\n---")
            except Exception as e: docs.append(f"\n---\n**Doc: `{p.name}` [Error: {e}]**\n---")
    return {"content": "\n\n".join(docs)}

_executor = ThreadPoolExecutor(max_workers=5)
async def asyncio_to_thread(func, *args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(_executor, functools.partial(func, *args, **kwargs))

if __name__ == "__main__":
    import uvicorn
    if not _user_prompt_templates: _user_prompt_templates.extend([Template(**td) for td in DEFAULT_AI_PROMPT_TEMPLATES_RAW])
    uvicorn.run(app, host="127.0.0.1", port=8000)