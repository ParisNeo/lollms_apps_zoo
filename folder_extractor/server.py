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
import time # For browser opening delay

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Imports for __main__ functionality
import socket
import webbrowser
import threading

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
    {"name": "AI: Add New Feature", "content": "Based on the provided folder structure and file contents, please outline the steps and code modifications needed to implement the following new feature: [Describe New Feature Here]. Consider potential impacts on existing functionality, necessary tests, and any new dependencies."},
    {"name": "AI: Code Review", "content": "Please perform a code review of the selected files. Focus on: \n1. Clarity and Readability\n2. Potential Bugs or Edge Cases\n3. Performance Optimizations\n4. Adherence to Best Practices (e.g., DRY, SOLID)\n5. Security Vulnerabilities\nProvide specific examples and suggestions for improvement."},
    {"name": "AI: Documentation Skeleton", "content": "Generate a documentation skeleton for the project/selected files. For each major component or file, suggest sections like: \n- Purpose\n- Key Functions/Classes\n- Usage Examples\n- Dependencies\n- Configuration Options (if any)"},
    {"name": "AI: Explain Code", "content": "Explain the functionality of the following code snippets. Describe what each part does and how they work together. Identify any complex logic or non-obvious behaviors. \n[You might copy-paste specific code sections here after generation, or refer to file paths]"},
    {"name": "AI: Refactor Suggestions", "content": "Analyze the selected code for potential refactoring opportunities. Suggest improvements to enhance modularity, reduce complexity, improve maintainability, or apply relevant design patterns. Provide reasoning for your suggestions."},
    {"name": "AI: Test Case Ideas", "content": "Based on the selected files, generate a list of potential test cases. Include: \n- Unit tests for individual functions/methods.\n- Integration tests for interactions between components.\n- Edge case scenarios.\n- Happy path and error condition tests."},
    {"name": "General: Project Overview", "content": "Provide a high-level overview of the project based on its structure and file contents. What is its main purpose? What are the key technologies used? What are the major components and their roles?\nUser Request: {USER_REQUEST}"},
    {"name": "General: Summarize Changes for Commit", "content": "I've made some changes. Based on the context (you might need to be provided with a diff or a list of modified files later), help me draft a concise and informative commit message. Key changes involve [User briefly describes changes or points to files]."},
]
_user_prompt_templates: List[Template] = [Template(**t_dict) for t_dict in DEFAULT_AI_PROMPT_TEMPLATES_RAW]
executor = ThreadPoolExecutor(max_workers=5)

DEFAULT_EXCLUDED_FOLDERS: Set[str] = {
    # These are already covered by _MANDATORY_EXCLUDED_FOLDER_NAMES for tree generation
    # ".git", ".vscode", "__pycache__", 
    ".svn", ".hg", ".bzr", "_darcs", "CVS",
    ".idea", ".vs", ".project", ".settings", ".classpath", "nbproject", "*.kdev4",
    "venv", ".venv", "env", ".env", "build", "dist", 
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", ".tox",
    "node_modules", ".yarn",
    "target", ".gradle", "bin", "obj", "out",
    "logs", "temp", "tmp", ".tmp",
    "coverage", "htmlcov", ".nyc_output",
    ".DS_Store", "Thumbs.db", "desktop.ini",
}
DEFAULT_ALWAYS_EXCLUDED_PATTERNS: List[str] = [
    "*.egg-info/", "*.dist-info/", "*.pyc", "*.pyo", "*.pyd",
    "*.class", "*.o", "*.obj", "*.lib", "*.dll", "*.so", "*.a", "*.idx", "*.pack",
    "*.bak", "*.swp", "*.swo", "*~", "._*",
    "*.orig", "*.rej",
    ".DS_Store", # Redundant with folder but good as pattern too
]

DEFAULT_EXCLUDED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".o", ".obj", ".class", ".dll", ".so", ".exe", ".bin", ".app", ".msi", ".deb", ".rpm",
    ".zip", ".tar", ".gz", ".tgz", ".rar", ".7z", ".jar", ".war", ".ear", ".bz2", ".xz",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".ico", ".webp",
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a",
    ".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm",
    ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".lock", ".DS_Store",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".odt", ".ods", ".odp", ".odg",
    ".psd", ".ai", ".eps", ".indd",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".iso", ".img", ".dmg",
    ".ipynb_checkpoints",
}
ALLOWED_TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".markdown", ".rst", ".adoc", ".asciidoc", ".tex", ".bib", ".sty", ".cls",
    ".py", ".pyw", ".pyi", ".rb", ".rbw", ".pl", ".pm", ".t", ".php", ".phtml", ".php3", ".php4", ".php5", ".phps", ".lua", ".sh", ".bash", ".zsh", ".fish", ".csh", ".ksh",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx", ".cs", ".java", ".scala", ".kt", ".kts", ".go", ".rs", ".swift", ".dart", ".groovy", ".gvy", ".gy", ".gsh",
    ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx", ".vue", ".svelte", ".astro",
    ".html", ".htm", ".xhtml", ".xml", ".xsd", ".xsl", ".xslt", ".rss", ".atom", ".rdf", ".owl",
    ".css", ".scss", ".sass", ".less", ".styl",
    ".json", ".jsonc", ".geojson", ".webmanifest", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".editorconfig", ".env",
    ".sql", ".ddl", ".dml",
    ".csv", ".tsv", ".psv",
    ".dockerfile", "dockerfile", "Dockerfile", ".tf", ".tfvars", ".hcl", ".nomad",
    ".gradle", ".pom", ".csproj", ".vbproj", ".fsproj", ".sln", ".vcproj", ".vcxproj",
    ".gitignore", ".gitattributes", ".gitmodules", ".gitkeep", ".npmrc", ".yarnrc", ".babelrc", ".eslintrc", ".prettierrc", ".stylelintrc", ".jshintrc", ".bowerrc",
    ".makefile", "makefile", "Makefile", "GNUmakefile", "CMakeLists.txt", "build.xml", "Rakefile", "Gemfile", "setup.py", "requirements.txt", "Pipfile", "poetry.lock", "pyproject.toml",
    ".graphql", ".gql",
    ".liquid", ".njk", ".jinja", ".jinja2", ".hbs", ".mustache", ".ejs",
    ".patch", ".diff", ".log", ".srt", ".vtt", ".sub", ".ass",
    ".r", ".R", ".rmd", ".qmd",
    ".vb", ".vbs", ".bas",
    ".f", ".for", ".f90", ".f95", ".f03", ".f08",
    ".clj", ".cljs", ".cljc", ".edn",
    ".pas", ".pp", ".inc", ".lpr", ".dpr",
    ".erl", ".hrl", ".ex", ".exs",
    ".elm", ".fs", ".fsi", ".fsx",
    ".scpt", ".applescript",
    ".ps1", ".psm1", ".psd1",
    ".bat", ".cmd",
    ".fasta", ".fastq", ".fa", ".pdb", ".gff", ".gtf", ".bed"
}
TREE_BRANCH, TREE_LAST, TREE_VLINE, TREE_SPACE = "├─ ", "└─ ", "│  ", "   "
FOLDER_ICON_STR, FILE_ICON_STR = "📁", "📄"
DEFAULT_MAX_FILE_SIZE_MB = 1.0
PRESET_EXCLUSIONS: Dict[str, List[str]] = {
    "Python Project": ["*.pyc", "__pycache__/", "venv/", ".venv/", "build/", "dist/", "*.egg-info/", "*.whl", "docs/_build/", ".tox/"],
    "Node.js Project": ["node_modules/", "package-lock.json", "yarn.lock", "build/", "dist/", ".nuxt/", ".next/", "*.log", "coverage/"],
    "Java Project (Maven/Gradle)": ["target/", "build/", ".gradle/", "*.jar", "*.war", "*.class", "bin/", "logs/", "hs_err_pid*.log"],
    "Git Repository": [".git/"],
    "IDE/Editor Configs": [".vscode/", ".idea/", "*.iml", "*.ipr", "*.iws", ".project", ".classpath", ".settings/", "nbproject/", "*.sublime-project", "*.sublime-workspace"],
    "Operating System/Misc": [".DS_Store", "Thumbs.db", "*.swp", "*.swo", "*~", ".Trash*", "desktop.ini", "._*"],
    "Log Files": ["*.log", "logs/", "log/", "debug.log", "error.log"],
    "Binary/Archives": ["*.exe", "*.dll", "*.so", "*.bin", "*.zip", "*.tar.gz", "*.rar", "*.7z", "*.jar", "*.war", "*.pkg", "*.dmg", "*.iso", "*.img", "*.deb", "*.rpm"],
    "Large Media Files": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.mp4", "*.avi", "*.mp3", "*.wav", "*.pdf", "*.doc", "*.docx", "*.ppt", "*.pptx", "*.xls", "*.xlsx", "*.psd", "*.ai", "*.sketch"]
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

# Folders that will always be excluded from tree generation, regardless of include filters
_MANDATORY_EXCLUDED_FOLDER_NAMES: Set[str] = {
    ".git", 
    ".vscode", 
    "__pycache__"
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
        
        # Start with general defaults, mandatory ones are handled differently for tree generation
        self._active_excluded_folders = set(DEFAULT_EXCLUDED_FOLDERS) 
        self._active_excluded_extensions = set(DEFAULT_EXCLUDED_EXTENSIONS)
        self._active_excluded_patterns = list(DEFAULT_ALWAYS_EXCLUDED_PATTERNS)
        
        # Add patterns for mandatory excluded folders to catch their contents if paths are directly given
        for folder_name in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            self._active_excluded_patterns.append(f"{folder_name}/") # e.g. .git/
            self._active_excluded_folders.add(folder_name)


        self._active_include_patterns = [p.strip().replace("\\", "/") for p in custom_inclusions_str.split(',') if p.strip()]
        
        for preset_name in selected_preset_names:
            if preset_name in PRESET_EXCLUSIONS:
                for pattern in PRESET_EXCLUSIONS[preset_name]:
                    normalized_pattern = pattern.replace("\\", "/")
                    # Check if it's one of the mandatory excluded ones; if so, it's already handled for patterns
                    is_mandatory_style_pattern = any(normalized_pattern.startswith(m_folder + "/") or normalized_pattern == m_folder for m_folder in _MANDATORY_EXCLUDED_FOLDER_NAMES)
                    
                    if normalized_pattern.endswith('/') and not '*' in normalized_pattern and not '?' in normalized_pattern and not '[' in normalized_pattern:
                        folder_name_to_add = normalized_pattern[:-1].lower()
                        if folder_name_to_add not in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                             self._active_excluded_folders.add(folder_name_to_add)
                    elif normalized_pattern.startswith("*.") and not '/' in normalized_pattern:
                        self._active_excluded_extensions.add(normalized_pattern[1:].lower())
                    elif not is_mandatory_style_pattern: # Avoid duplicate patterns for mandatory excluded folders
                        self._active_excluded_patterns.append(normalized_pattern)
        
        custom_folder_list = [f.strip().lower().replace("\\", "/") for f in custom_folders_str.split(',') if f.strip()]
        for f_cust in custom_folder_list:
            if f_cust not in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                self._active_excluded_folders.add(f_cust)

        self._active_excluded_extensions.update(e.strip().lower() for e in custom_exts_str.split(',') if e.strip() and e.strip().startswith('.'))
        
        custom_pattern_list = [p.strip().replace("\\", "/") for p in custom_patterns_str.split(',') if p.strip()]
        for p_cust in custom_pattern_list:
            is_mandatory_style_pattern = any(p_cust.startswith(m_folder + "/") or p_cust == m_folder for m_folder in _MANDATORY_EXCLUDED_FOLDER_NAMES)
            if not is_mandatory_style_pattern:
                 self._active_excluded_patterns.append(p_cust)
        
        if dynamic_patterns_list: 
            for p_dyn in dynamic_patterns_list:
                p_dyn_norm = p_dyn.strip().replace("\\","/")
                if p_dyn_norm:
                    is_mandatory_style_pattern = any(p_dyn_norm.startswith(m_folder + "/") or p_dyn_norm == m_folder for m_folder in _MANDATORY_EXCLUDED_FOLDER_NAMES)
                    if not is_mandatory_style_pattern:
                        self._active_excluded_patterns.append(p_dyn_norm)

        self._active_excluded_patterns = sorted(list(set(self._active_excluded_patterns)))
        self._active_excluded_folders = set(f.lower() for f in self._active_excluded_folders if f not in _MANDATORY_EXCLUDED_FOLDER_NAMES)
        self._active_excluded_extensions = set(e.lower() for e in self._active_excluded_extensions)
        
        self._max_file_size_bytes = int(max(0.01, max_size_mb) * 1024 * 1024)

    def _is_excluded(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        context_root = current_root_override or self._root_folder
        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower() if item.is_file() else ""
        
        # Mandatory exclusions are handled by skipping them in tree building.
        # This method primarily checks other configured exclusions.
        if item.is_dir() and item_name_lower in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            return True # These are always excluded from processing further by _is_excluded itself

        if item.is_dir() and item_name_lower in self._active_excluded_folders:
            return True
        if item.is_file() and item_suffix_lower in self._active_excluded_extensions:
            return True
            
        try:
            rel_path_str = str(item.resolve().relative_to(context_root).as_posix())
        except (AttributeError, ValueError): 
            rel_path_str = item.name.replace("\\", "/")

        for pattern in self._active_excluded_patterns:
            if pattern.endswith('/'):
                dir_pattern = pattern[:-1]
                if item.is_dir() and (fnmatch.fnmatchcase(item.name, dir_pattern) or fnmatch.fnmatchcase(rel_path_str, dir_pattern)):
                    return True
                # Check if the item is inside an excluded directory pattern
                if rel_path_str.startswith(dir_pattern + "/"): # e.g. item "excluded_dir/file.txt" matches pattern "excluded_dir/"
                    return True
            elif "/" not in pattern: # Simple file/dir name pattern
                if fnmatch.fnmatchcase(item.name, pattern):
                    return True
            else: # Pattern contains / (e.g. "src/*.py" or "some_dir/specific_file.txt")
                if fnmatch.fnmatchcase(rel_path_str, pattern):
                    return True
        return False

    def _is_included_by_filter(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        if not self._active_include_patterns: return True 
        # If it's a mandatorily excluded folder, include patterns cannot override this for tree display
        if item.is_dir() and item.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            return False

        context_root = current_root_override or self._root_folder
        try:
            rel_path_str = str(item.resolve().relative_to(context_root).as_posix())
        except (AttributeError, ValueError): rel_path_str = item.name.replace("\\", "/")

        for pattern in self._active_include_patterns:
            if fnmatch.fnmatchcase(rel_path_str, pattern): return True
            if item.is_dir() and pattern.endswith('/'):
                if fnmatch.fnmatchcase(rel_path_str, pattern[:-1]): return True # Match "foo" for "foo/"
            # If item is a directory, and pattern could be a parent directory of this item
            if item.is_dir() and "/" in rel_path_str:
                try:
                    current_path_obj_parts = Path(rel_path_str).parts
                    for i in range(len(current_path_obj_parts)):
                        parent_part_path_str = "/".join(current_path_obj_parts[:i+1])
                        if fnmatch.fnmatchcase(parent_part_path_str, pattern): return True
                        if pattern.endswith("/") and fnmatch.fnmatchcase(parent_part_path_str, pattern[:-1]): return True
                except: pass # Path parsing error
        return False

    def _is_text_file(self, file: Path) -> bool:
        if file.suffix.lower() in self._active_excluded_extensions and file.suffix.lower() not in ALLOWED_TEXT_EXTENSIONS: # Explicitly excluded and not allowed as text
            return False
        return file.suffix.lower() in ALLOWED_TEXT_EXTENSIONS

    def _read_file_content(self, file: Path) -> str:
        try:
            if file.stat().st_size > self._max_file_size_bytes: return f"[File omitted: Exceeds size limit ({self._max_file_size_bytes/(1024*1024):.2f} MB)]"
            if file.stat().st_size == 0: return "[Empty file]"
            content = ""
            try: content = file.read_text(encoding="utf-8", errors='strict')
            except UnicodeDecodeError:
                for enc in ['latin-1', 'cp1252', 'utf-16']:
                    try: 
                        content = file.read_text(encoding=enc)
                        print(f"Warning: File '{file.as_posix()}' decoded as {enc} after UTF-8 failure.")
                        break
                    except UnicodeDecodeError: pass
                    except Exception:
                        content = f"[Error: Could not decode with {enc} or read]"
                        break
                else: content = "[Error: Could not decode file with common encodings (UTF-8, Latin-1, CP1252, UTF-16)]"
            except Exception as e: return f"[Error reading file '{file.as_posix()}': {e}]"
            
            line_count = 0; long_line_threshold = 5000; excessive_long_lines_count = 0
            for line in content.splitlines():
                line_count += 1
                if len(line) > long_line_threshold: excessive_long_lines_count +=1
            if line_count > 10 and excessive_long_lines_count > line_count * 0.3:
                 print(f"Warning: File '{file.as_posix()}' contains many excessively long lines. It might be minified or not a typical text file.")
            return content or "[File appears empty after read]"
        except OSError as e: return f"[OS error accessing file '{file.as_posix()}': {e}]"
        except Exception as e: print(f"Unexpected error reading {file.as_posix()}: {e}\n{traceback.format_exc()}"); return "[Unexpected error reading file]"

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
        try: 
            paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError) as e:
            error_type = 'Permission Denied' if isinstance(e,PermissionError) else 'OS Error'
            return [{"name": f"[{error_type}: {current_dir_path.name}]", "path": str(current_dir_path.as_posix()), "is_dir": True, "is_text": False, "can_be_checked": False, "error": True, "tooltip": f"Cannot access: {e}"}]
        
        for path_obj in paths_in_dir:
            # Hard skip for mandatory excluded folders
            if path_obj.is_dir() and path_obj.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                continue

            is_item_excluded = self._is_excluded(path_obj, root_scan_path)
            is_item_included_by_filter = self._is_included_by_filter(path_obj, root_scan_path)
            
            item_data = {
                "name": path_obj.name, "path": str(path_obj.as_posix()), "is_dir": path_obj.is_dir(), 
                "children": [], "error": False, "tooltip": ""
            }
            can_be_checked_final = True
            
            if item_data["is_dir"]:
                item_data["is_text"] = False
                # For directories, it can be checked if (not excluded by rules OR explicitly included by filter)
                # AND it's not a mandatorily excluded folder (already handled by `continue` above)
                can_be_checked_final = not is_item_excluded or is_item_included_by_filter
                item_data["children"] = self._collect_tree_data_recursive(path_obj, root_scan_path)
                # If a directory has no children to show (e.g. all children filtered out)
                # AND it's itself excluded by rules AND not explicitly included, then don't allow checking.
                if not item_data["children"] and is_item_excluded and not is_item_included_by_filter:
                    can_be_checked_final = False # Makes empty, excluded dirs uncheckable
            else: # File
                item_data["is_text"] = self._is_text_file(path_obj)
                file_too_large = False
                try: 
                    if item_data["is_text"]: # Only check size for text files we might read
                        file_too_large = path_obj.stat().st_size > self._max_file_size_bytes
                        if file_too_large: item_data["tooltip"] = f"File size exceeds limit ({self._max_file_size_bytes/(1024*1024):.2f}MB)"
                except OSError as e: 
                    file_too_large = True; item_data["tooltip"] = f"Cannot get file size: {e}"

                if not item_data["is_text"]:
                    item_data["tooltip"] = "Binary or non-text file type"; can_be_checked_final = False
                elif is_item_excluded and not is_item_included_by_filter: # Excluded by rule and not saved by an include filter
                    item_data["tooltip"] = "Excluded by filters"; can_be_checked_final = False
                elif file_too_large: can_be_checked_final = False # Tooltip already set
                # If explicitly included by filter, it should be checkable (if text and not too large)
                elif is_item_included_by_filter:  # (and not is_item_excluded implicitly covered here)
                    can_be_checked_final = item_data["is_text"] and not file_too_large
                else: # Not excluded, not explicitly included (so default allow), text, not too large
                     can_be_checked_final = item_data["is_text"] and not file_too_large


            item_data["can_be_checked"] = can_be_checked_final
            items_data.append(item_data)
        return items_data

    def _get_all_displayable_paths(self, current_dir_path: Path, root_scan_path: Path) -> List[Path]:
        all_paths = []
        try: paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError): return [] 

        for path_obj in paths_in_dir:
            # Hard skip for mandatory excluded folders
            if path_obj.is_dir() and path_obj.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                continue

            is_excluded_by_rules = self._is_excluded(path_obj, root_scan_path)
            is_included_by_filter = self._is_included_by_filter(path_obj, root_scan_path)
            
            is_displayable_in_tree = True # Assume displayable unless a condition makes it false
            
            if path_obj.is_file():
                if not self._is_text_file(path_obj): 
                    is_displayable_in_tree = False
                else: # It is a text file, check size
                    try:
                        if path_obj.stat().st_size > self._max_file_size_bytes:
                            is_displayable_in_tree = False
                    except OSError: 
                        is_displayable_in_tree = False # Cannot stat, assume not displayable
            
            # If it's already marked non-displayable (e.g. binary, too large), skip further checks for this path
            if not is_displayable_in_tree:
                pass # Already decided it's not displayable
            # If it's excluded by general rules AND not specifically included by an include filter
            elif is_excluded_by_rules and not is_included_by_filter:
                is_displayable_in_tree = False
            # If it's not excluded OR it is excluded but an include filter saves it, it's displayable (if not already falsified by type/size)
            # This path is effectively covered by the initial True and subsequent falsifications.

            if is_displayable_in_tree:
                all_paths.append(path_obj.resolve())
                if path_obj.is_dir(): 
                    all_paths.extend(self._get_all_displayable_paths(path_obj, root_scan_path))
        return all_paths

    def _generate_tree_markdown_from_paths(self, root_path: Path, paths_for_tree_structure: List[str]) -> List[str]:
        if not paths_for_tree_structure: return ["*No items to display in the file tree based on current filters.*"] 
        resolved_root_path = root_path.resolve(); hierarchy: Dict[str, Any] = {}
        all_nodes_to_represent_resolved = set()
        for p_str_raw in paths_for_tree_structure:
            p_resolved = Path(p_str_raw).resolve(); all_nodes_to_represent_resolved.add(p_resolved)
            try:
                # Add parent directories to ensure structure is complete up to the root
                # Check if p_resolved is truly relative to resolved_root_path before calling .relative_to
                if p_resolved != resolved_root_path and resolved_root_path in p_resolved.parents:
                    current_parent = p_resolved.parent
                    while current_parent != resolved_root_path and resolved_root_path in current_parent.parents:
                        all_nodes_to_represent_resolved.add(current_parent)
                        if current_parent == current_parent.parent: break # Should not happen with valid paths
                        current_parent = current_parent.parent
                    all_nodes_to_represent_resolved.add(resolved_root_path) # Ensure root is always there if anything under it is
            except (ValueError, AttributeError) as e: 
                 # This can happen if p_resolved is not under resolved_root_path, or other path issues
                 # print(f"Debug: Path relationship error for {p_resolved} relative to {resolved_root_path}: {e}")
                 pass # If it's not relative, it will be handled as a top-level item if it's the root itself
        
        if not all_nodes_to_represent_resolved and resolved_root_path.is_dir(): 
            # If paths_for_tree_structure was empty but root is valid, show at least the root
            all_nodes_to_represent_resolved.add(resolved_root_path)

        # Sort nodes by depth and then alphabetically
        def get_sort_key(x_path):
            try:
                # Ensure x_path is truly relative before calling relative_to
                if resolved_root_path in x_path.parents or x_path == resolved_root_path:
                    return (len(x_path.relative_to(resolved_root_path).parts), str(x_path.as_posix()).lower())
                else: # If not relative, treat as top level (depth 0 for sorting purposes, or handle as error)
                    return (0, str(x_path.as_posix()).lower()) # Fallback for paths not under root
            except ValueError: # Path is not relative to root_path
                 return (0, str(x_path.as_posix()).lower()) # Fallback

        sorted_nodes = sorted(list(all_nodes_to_represent_resolved), key=get_sort_key)

        # Build hierarchy
        for node_path_resolved in sorted_nodes:
            try: 
                # Ensure node_path_resolved is relative or is the root itself
                if node_path_resolved == resolved_root_path:
                    parts = ()
                elif resolved_root_path in node_path_resolved.parents:
                    parts = node_path_resolved.relative_to(resolved_root_path).parts
                else:
                    # This case should ideally not happen if paths_for_tree_structure are correctly filtered
                    # print(f"Debug: Node {node_path_resolved} not under root {resolved_root_path} for tree markdown.")
                    parts = (node_path_resolved.name,) # Treat as a single part if not relative
            except (ValueError, AttributeError): 
                parts = (node_path_resolved.name,) 
            
            current_level = hierarchy
            for part in parts: current_level = current_level.setdefault(part, {})
            current_level["_isfile_"] = node_path_resolved.is_file() # Mark if this node itself is a file

        # Special case: if the root itself is the only thing (e.g., an empty filtered folder)
        if not hierarchy and resolved_root_path in all_nodes_to_represent_resolved : 
            hierarchy.setdefault("_isfile_", resolved_root_path.is_file()) # This is unlikely for a root dir but for completeness

        def format_level(level_dict: Dict[str, Any], current_prefix: str) -> List[str]:
            lines = []; items_to_display = {k:v for k,v in level_dict.items() if not k.startswith("_")} # Filter out metadata like _isfile_
            sorted_names = sorted(items_to_display.keys(), key=lambda k: (items_to_display[k].get("_isfile_", False), k.lower())) # Sort files after folders, then alpha
            
            for i, name in enumerate(sorted_names):
                node_details = items_to_display[name]
                is_last_item_in_level = (i == len(sorted_names) - 1)
                is_actually_a_file = node_details.get("_isfile_", False) # Check if this specific node is a file
                icon = FILE_ICON_STR if is_actually_a_file else FOLDER_ICON_STR
                
                lines.append(f"{current_prefix}{TREE_LAST if is_last_item_in_level else TREE_BRANCH}{icon} {name}{'' if is_actually_a_file else '/'}")
                
                children_dict = {k_c: v_c for k_c, v_c in node_details.items() if not k_c.startswith("_")} # Get actual children sub-dictionaries
                if not is_actually_a_file and children_dict: # If it's a directory and has children to list
                    lines.extend(format_level(children_dict, current_prefix + (TREE_SPACE if is_last_item_in_level else TREE_VLINE)))
            return lines

        tree_title = f"{FOLDER_ICON_STR} {resolved_root_path.name}/"
        # If hierarchy is empty (e.g. root itself was filtered out or no displayable items), format_level returns empty
        # This can happen if root_path itself does not meet criteria or has no displayable children.
        formatted_tree_lines = format_level(hierarchy, "")
        if not formatted_tree_lines and resolved_root_path.is_dir() and not paths_for_tree_structure:
             # If tree is empty because no paths were provided (e.g. all filtered out before this stage)
             pass # The initial check for empty paths_for_tree_structure handles this message
        elif not formatted_tree_lines and resolved_root_path.is_dir():
            # This might mean the root folder itself is displayable but has no displayable children.
            # The title alone will be shown, which is acceptable.
            pass


        return [tree_title] + formatted_tree_lines if (formatted_tree_lines or resolved_root_path.is_dir()) else ["*No items to display in the file tree based on current filters.*"]


    def _generate_file_contents_markdown(self, root_folder: Path, selected_file_paths_abs: List[str]) -> List[str]: 
        content_lines = ["", "---", "", "## File Contents"]
        if not selected_file_paths_abs:
            content_lines.append("\n*No files selected in the tree to show content.*")
            return content_lines
        
        resolved_root_folder = root_folder.resolve(); files_for_content_processing = []

        for path_str in selected_file_paths_abs:
            try: path = Path(path_str).resolve()
            except Exception as e_resolve:
                print(f"Warning: Could not resolve selected path '{path_str}' for content: {e_resolve}. Skipping.")
                continue
            
            if path.is_dir() and path.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                # This case should not happen if UI prevents selection from these.
                print(f"Skipping content for mandatorily excluded folder: {path.as_posix()}")
                continue
            
            if not path.is_file():
                # print(f"Debug: Selected path '{path_str}' (resolved: '{path.as_posix()}') is not a file. Skipping for content.")
                continue

            # Ensure selected file is within a non-mandatorily-excluded path
            is_in_mandatory_excluded_dir = False
            try:
                # Check if any parent is a mandatory excluded folder *relative to the root_scan_path*
                # This requires careful handling of path relativity.
                # More simply: the _is_excluded check with patterns like ".git/" should catch this.
                current_check_path = path.parent
                while current_check_path != resolved_root_folder and current_check_path != current_check_path.parent:
                    if current_check_path.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                        is_in_mandatory_excluded_dir = True
                        break
                    current_check_path = current_check_path.parent
                if resolved_root_folder.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES and path.is_relative_to(resolved_root_folder):
                     # If the root itself is a mandatorily excluded name (e.g. user selected a .git folder as root)
                     # This is an edge case, typically _MANDATORY_EXCLUDED_FOLDER_NAMES applies to subfolders.
                     pass # Allow if root is one of these, content logic below will handle it.

            except Exception as e_parent_check:
                print(f"Debug: Parent check error for {path.as_posix()}: {e_parent_check}")


            if is_in_mandatory_excluded_dir:
                 print(f"Skipping content for file '{path.as_posix()}' within a mandatorily excluded directory.")
                 continue


            try: path.relative_to(resolved_root_folder) # Raises ValueError if not a subpath
            except ValueError:
                print(f"Warning: Selected file path '{path.as_posix()}' (from input '{path_str}') for content generation is not within the current root folder '{resolved_root_folder.as_posix()}'. This might be a stale selection from a previously loaded folder. Skipping this file.")
                continue

            is_item_excluded = self._is_excluded(path, resolved_root_folder) # This will be true for files in .git/ etc.
            is_item_included_by_filter = self._is_included_by_filter(path, resolved_root_folder)
            is_text = self._is_text_file(path); is_too_large = False
            try:
                if is_text: is_too_large = path.stat().st_size > self._max_file_size_bytes
            except OSError: is_too_large = True
            
            should_include_content = is_text and not is_too_large and (not is_item_excluded or is_item_included_by_filter)
            
            if should_include_content: files_for_content_processing.append(path)
            else:
                reason = "not text" if not is_text else "too large" if is_too_large else "excluded" if is_item_excluded and not is_item_included_by_filter else "in mandatory excluded parent" if is_in_mandatory_excluded_dir else "unknown"
                print(f"Skipping content for selected file '{path.as_posix()}': {reason}.")
        
        files_for_content_processing.sort(key=lambda p: str(p.relative_to(resolved_root_folder).as_posix() if (resolved_root_folder in p.parents or p == resolved_root_folder) else p.name).lower())
        if not files_for_content_processing:
             content_lines.append("\n*No valid text files selected or available for content display based on current filters, limits, and folder context.*")
             return content_lines
        for file_path in files_for_content_processing:
            try: 
                # Ensure relative_to is only called if applicable
                if resolved_root_folder in file_path.parents or file_path == resolved_root_folder:
                    rel_path_str = str(file_path.relative_to(resolved_root_folder).as_posix())
                else:
                    rel_path_str = file_path.name # Fallback if not truly relative (should be rare)
            except ValueError: 
                rel_path_str = file_path.name
            content_lines.append(f"\n### `{rel_path_str}`")
            file_content = self._read_file_content(file_path)
            lang = (file_path.suffix[1:] if file_path.suffix else "text").lower(); lang = "".join(c for c in lang if c.isalnum()) or "text"
            aliases = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript', 'jsx': 'javascript', 'md': 'markdown', 'sh': 'bash', 'yml': 'yaml', 'dockerfile': 'dockerfile', 'h': 'c', 'hpp': 'cpp', 'cs': 'csharp', 'rb': 'ruby', 'pl': 'perl', 'kt': 'kotlin', 'rs': 'rust', 'go': 'golang', 'html': 'html', 'css': 'css', 'scss': 'scss', 'vue': 'vue', 'java': 'java', 'xml': 'xml', 'json': 'json', 'sql': 'sql', 'php': 'php', 'conf': 'ini', 'cfg':'ini', 'properties':'ini', 'bat': 'batch', 'ps1': 'powershell', 'makefile':'makefile'}
            lang = aliases.get(lang, lang)
            content_lines.extend([f"```{lang}", *(file_content.splitlines() if file_content else [""]), "```"])
        return content_lines

    def generate_structure_text(
        self, folder_path_str: str, filter_settings: Dict[str, Any], custom_prompt: str = "",
        documentation_content: str = "", selected_file_paths_abs: Optional[List[str]] = None,
    ) -> str:
        try:
            self._root_folder = Path(folder_path_str).resolve()
            if not self._root_folder.is_dir(): raise ValueError(f"Path is not a directory: {self._root_folder}")
        except Exception as e: raise ValueError(f"Invalid folder path '{folder_path_str}': {e}")
        
        self.setup_exclusions_and_limits(
            filter_settings.get("selected_presets", []), filter_settings.get("custom_folders", ""),
            filter_settings.get("custom_extensions", ""), filter_settings.get("custom_patterns", ""),
            [p.strip() for p in filter_settings.get("dynamic_patterns", "").split(',') if p.strip()],
            filter_settings.get("custom_inclusions", ""), filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB), self._root_folder
        )
        
        # _get_all_displayable_paths will now respect _MANDATORY_EXCLUDED_FOLDER_NAMES
        all_displayable_paths_resolved = self._get_all_displayable_paths(self._root_folder, self._root_folder)
        all_displayable_paths_str_posix = [str(p.as_posix()) for p in all_displayable_paths_resolved]
        
        tree_lines = self._generate_tree_markdown_from_paths(self._root_folder, all_displayable_paths_str_posix)
        
        structure_output_lines = [f"# Folder Structure: {self._root_folder.name}", f"*(Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*", "", "```text", *tree_lines, "```"]
        
        # Ensure selected_file_paths_abs respects mandatory exclusions before content generation
        valid_selected_paths_for_content = []
        if selected_file_paths_abs:
            for p_str in selected_file_paths_abs:
                try:
                    p_abs = Path(p_str).resolve()
                    is_in_mandatory_excluded_dir = False
                    # Check if any parent is a mandatory excluded folder
                    temp_parent = p_abs.parent
                    while temp_parent != self._root_folder.parent and temp_parent != temp_parent.parent: # Stop before filesystem root or if root folder is a parent
                        if temp_parent.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES and temp_parent.is_relative_to(self._root_folder):
                            is_in_mandatory_excluded_dir = True
                            break
                        temp_parent = temp_parent.parent
                    if not is_in_mandatory_excluded_dir:
                        valid_selected_paths_for_content.append(str(p_abs.as_posix()))
                    # else:
                    #     print(f"Debug: Path {p_str} filtered from content generation due to mandatory exclusion.")
                except Exception: # Path resolution or other errors
                    pass # Skip problematic paths


        content_output_lines = self._generate_file_contents_markdown(self._root_folder, valid_selected_paths_for_content)
        
        full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)
        
        final_prompt_parts = []
        if documentation_content and documentation_content.strip(): final_prompt_parts.append("## Imported Documentation\n\n" + documentation_content.strip())
        if custom_prompt and custom_prompt.strip(): final_prompt_parts.append("## Custom Instructions\n\n" + custom_prompt.strip())
        
        if final_prompt_parts: full_output += "\n\n---\n\n" + "\n\n---\n\n".join(final_prompt_parts)
        
        return full_output.strip()

app = FastAPI(title="Folder Structure Extractor Web App", version="2.8.1") # Version bump for the change
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
folder_processor = FolderProcessor()

class FilterSettings(BaseModel):
    selected_presets: List[str] = []
    custom_folders: str = ""
    custom_extensions: str = ""
    custom_patterns: str = ""
    dynamic_patterns: str = ""
    custom_inclusions: str = ""
    max_file_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB

class LoadTreeRequest(BaseModel):
    folder_path: str
    filters: FilterSettings

class GenerateRequest(BaseModel):
    folder_path: str
    filters: FilterSettings
    selected_paths_abs: List[str]
    custom_prompt: str
    loaded_doc_paths: List[str]

class EnvironmentSettings(BaseModel):
    folder_path: str; selected_presets: List[str]; custom_folders: str; custom_extensions: str; custom_patterns: str
    dynamic_patterns: str; custom_inclusions: str; max_file_size_mb: float; save_output_checked: bool
    custom_prompt: str; current_theme_file: str = "default_light.qss"; prompt_templates: List[Template]
    loaded_doc_paths: List[str]; checked_tree_paths_str_abs: List[str]; version: str = "2.8.1"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        with open("static/index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())
    except FileNotFoundError: raise HTTPException(status_code=404, detail="index.html not found.")
    except Exception as e: print(f"Error serving index.html: {e}"); raise HTTPException(status_code=500, detail=f"Could not serve frontend: {e}")

async def asyncio_to_thread(func, *args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(executor, functools.partial(func, *args, **kwargs))

@app.post("/api/load_project_tree")
async def load_project_tree(request: LoadTreeRequest):
    if not request.folder_path: raise HTTPException(status_code=400, detail="Folder path empty.")
    folder_path = Path(request.folder_path)
    if not folder_path.exists(): raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
    if not folder_path.is_dir(): raise HTTPException(status_code=400, detail=f"Not a directory: {request.folder_path}")
    try:
        tree_data = await asyncio_to_thread(folder_processor.build_file_tree_json, request.folder_path, request.filters.model_dump())
        return JSONResponse(content={"tree": tree_data})
    except ValueError as ve: print(f"Value error loading tree: {ve}\n{traceback.format_exc()}"); raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e: print(f"Error loading tree: {e}\n{traceback.format_exc()}"); raise HTTPException(status_code=500, detail=f"Failed to load tree: {e}")

def _get_folder_path_from_pyqt5_dialog():
    app_instance = QApplication.instance() # Try to get existing instance
    if app_instance is None: # If no instance exists, create one
        # Check if sys.argv is empty or only contains the script name
        # This can happen if launched in certain environments (e.g. some debuggers)
        # PyQt needs at least one argument in sys.argv, typically the program name.
        if not sys.argv or len(sys.argv) == 0:
            app_argv = [''] # Provide a dummy program name
        else:
            app_argv = sys.argv
        app_instance = QApplication(app_argv)

    selected_path = QFileDialog.getExistingDirectory(None, "Select Project Folder on Server", os.path.expanduser("~"))
    # It's generally not a good practice to call app_instance.quit() or app_instance.exit() here
    # if the app_instance might be used by something else, or if this function is called multiple times.
    # For a simple utility function like this, it's often safer to let the main application control the QApplication lifecycle.
    # If this is the *only* use of QApplication, ensure it's properly managed.
    return selected_path

@app.post("/api/browse_server_folder")
async def browse_server_folder():
    if not _PYQT5_AVAILABLE: raise HTTPException(status_code=501, detail="PyQt5 not available on server.")
    try:
        path = await asyncio_to_thread(_get_folder_path_from_pyqt5_dialog)
        return {"status": "success" if path else "cancelled", "path": str(Path(path).as_posix()) if path else None}
    except Exception as e: print(f"PyQt5 dialog error: {e}\n{traceback.format_exc()}"); raise HTTPException(status_code=500, detail=f"Server dialog error: {e}")

@app.post("/api/generate_structure")
async def generate_structure(request: GenerateRequest):
    if not request.folder_path: raise HTTPException(status_code=400, detail="Folder path empty.")
    folder_path = Path(request.folder_path)
    if not folder_path.exists(): raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
    if not folder_path.is_dir(): raise HTTPException(status_code=400, detail=f"Not a directory: {request.folder_path}")
    try:
        doc_parts = []
        if request.loaded_doc_paths:
            for doc_path_str in request.loaded_doc_paths:
                doc_p = Path(doc_path_str)
                if doc_p.is_file():
                    try: doc_parts.append(f"\n---\n**Doc: `{doc_p.name}`**\n\n{doc_p.read_text(encoding='utf-8', errors='ignore').strip()}\n---")
                    except Exception as e_d: doc_parts.append(f"\n---\n**Doc: `{doc_p.name}` [Error: {e_d}]**\n---"); print(f"Doc read error {doc_path_str}: {e_d}")
                else: doc_parts.append(f"\n---\n**Doc: `{doc_p.name}` [Not found/not file]**\n---"); print(f"Doc not found/file: {doc_path_str}")
        full_doc_content = "\n".join(doc_parts)
        final_prompt = apply_placeholders(request.custom_prompt, request.folder_path)
        text = await asyncio_to_thread(folder_processor.generate_structure_text, request.folder_path, request.filters.model_dump(), final_prompt, full_doc_content, request.selected_paths_abs)
        return JSONResponse(content={"markdown": text})
    except ValueError as ve: print(f"Value error generating: {ve}\n{traceback.format_exc()}"); raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e: print(f"Error generating: {e}\n{traceback.format_exc()}"); raise HTTPException(status_code=500, detail=f"Failed to generate: {e}")

@app.get("/api/prompt_templates")
async def get_prompt_templates(): return JSONResponse(content=[t.model_dump() for t in _user_prompt_templates])

@app.post("/api/save_template")
async def save_template(template: Template):
    global _user_prompt_templates
    is_pristine = any(td_raw['name'] == template.name and td_raw['content'] == template.content for td_raw in DEFAULT_AI_PROMPT_TEMPLATES_RAW)
    idx = next((i for i, t_curr in enumerate(_user_prompt_templates) if t_curr.name == template.name), -1)
    if idx != -1:
        if is_pristine: _user_prompt_templates[idx] = Template(**next(item for item in DEFAULT_AI_PROMPT_TEMPLATES_RAW if item["name"] == template.name)); msg = "reverted"; stat = "reverted_to_default"
        else: _user_prompt_templates[idx] = template; msg = "updated"; stat = "success"
    else: _user_prompt_templates.append(template); msg = "saved new"; stat = "success"
    _user_prompt_templates.sort(key=lambda t: t.name.lower())
    return JSONResponse({"status": stat, "message": f"Template '{template.name}' {msg}.", "templates": [t.model_dump() for t in _user_prompt_templates]})

@app.post("/api/delete_template")
async def delete_template(template_data: Template):
    global _user_prompt_templates; name_del = template_data.name
    orig_def = next((td_raw for td_raw in DEFAULT_AI_PROMPT_TEMPLATES_RAW if td_raw['name'] == name_del), None)
    curr_idx = next((i for i, t in enumerate(_user_prompt_templates) if t.name == name_del), -1)
    if curr_idx == -1: raise HTTPException(status_code=404, detail=f"Template '{name_del}' not found.")
    if orig_def: _user_prompt_templates[curr_idx] = Template(**orig_def); msg = "reverted"; stat = "reverted_default"
    else: del _user_prompt_templates[curr_idx]; msg = "deleted"; stat = "deleted_custom"
    _user_prompt_templates.sort(key=lambda t: t.name.lower())
    return JSONResponse({"status": stat, "message": f"Template '{name_del}' {msg}.", "templates": [t.model_dump() for t in _user_prompt_templates]})

@app.post("/api/save_environment")
async def save_environment(settings: EnvironmentSettings):
    print(f"Env settings received (v: {settings.version}). Not saving persistently.")
    return JSONResponse(content={"status": "success", "message": "Env settings received by server.", "settings": settings.model_dump()})

@app.post("/api/load_documentation_content")
async def load_documentation_content(doc_paths_request: Dict[str, List[str]]):
    doc_paths = doc_paths_request.get("doc_paths", [])
    if not isinstance(doc_paths, list): raise HTTPException(status_code=400, detail="Invalid doc_paths format.")
    doc_parts = []
    for p_str in doc_paths:
        if not isinstance(p_str, str): doc_parts.append(f"\n---\n**Invalid Path Entry [{type(p_str)}]**\n---"); continue
        p = Path(p_str)
        if p.is_file():
            try: doc_parts.append(f"\n---\n**Doc: `{p.name}`**\n\n{p.read_text(encoding='utf-8',errors='ignore').strip()}\n---")
            except Exception as e: doc_parts.append(f"\n---\n**Doc: `{p.name}` [Error: {e}]**\n---")
        else: doc_parts.append(f"\n---\n**Doc: `{p.name}` [Not found/file at: {p_str}]**\n---")
    return JSONResponse(content={"content": "\n\n".join(doc_parts) if doc_parts else "No docs processed."})

def find_free_port(host="127.0.0.1", start_port=8000, max_tries=100):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            try: s.bind((host, port)); return port
            except OSError as e:
                if e.errno == socket.errno.EADDRINUSE: # Address already in use
                    if port == start_port + max_tries - 1: # Last try
                        raise
                    continue # Try next port
                else: # Other OSError
                    raise
    raise OSError(f"No free port found after {max_tries} tries, starting from port {start_port}.")


if __name__ == "__main__":
    import uvicorn
    if not _user_prompt_templates: # Ensure templates are loaded if script is run directly
        _user_prompt_templates.extend([Template(**td) for td in DEFAULT_AI_PROMPT_TEMPLATES_RAW])
        _user_prompt_templates.sort(key=lambda t: t.name.lower())

    host = "127.0.0.1"
    default_port = 8000
    port_to_use = default_port
    try:
        port_to_use = find_free_port(host, default_port)
        print(f"Using free port: {port_to_use}")
    except OSError as e:
        print(f"Warning: Port finding failed: {e}. Will attempt to use default port {default_port}.")
        # If find_free_port fails, uvicorn.run will try the default_port and fail if it's in use.
    
    url = f"http://{host}:{port_to_use}"
    print(f"Starting server on {url}")

    # Attempt to open browser only after confirming server is likely listening
    def open_browser_when_ready():
        time.sleep(2.0) # Give server a moment to start
        try:
            # Check if port is connectable
            with socket.create_connection((host, port_to_use), timeout=1.0):
                 print(f"Server seems to be listening. Opening {url} in browser.")
                 webbrowser.open_new_tab(url)
        except Exception as e_browser:
            print(f"Could not automatically open browser ({e_browser}). Please open {url} manually.")

    # Start browser opening in a separate thread so it doesn't block uvicorn
    threading.Timer(0.1, open_browser_when_ready).start() # Small delay before starting the timer thread

    try:
        uvicorn.run(app, host=host, port=port_to_use, log_level="info")
    except SystemExit:
        print("Server shutdown initiated.") # Or uvicorn's own message might appear
    except socket.error as e_sock:
        print(f"Socket error on starting uvicorn: {e_sock}" + (" (Is the port already in use?)" if e_sock.errno == socket.errno.EADDRINUSE else ""))
    except Exception as e_main:
        print(f"An unexpected error occurred while trying to run the server: {e_main}")
        traceback.print_exc()