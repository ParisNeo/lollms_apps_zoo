# -*- coding: utf-8 -*-
# Project: folder_extractor
# Author: ParisNeo with gemini 2.5
# Description: A PyQt5 application that takes a folder path and generates a Markdown-formatted text representation, including specific file/folder inclusions, documentation integration, and refined UI elements.
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

try:
    import pipmaster as pm
    pm.ensure_packages(["PyQt5", "markdown", "qt_material", "qtawesome"])
except ImportError:
    print("Error: pipmaster not found. Please install it: pip install pipmaster")
    print("Then install required packages: pip install PyQt5 qt_material")
    sys.exit(1)
except Exception as e:
    print(f"Error ensuring packages: {e}")
    sys.exit(1)

try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QListWidget, QDialogButtonBox, QLineEdit, QLabel, QFileDialog,
        QTextEdit, QComboBox, QGroupBox, QDialog, QListWidgetItem,
        QFormLayout, QDoubleSpinBox, QCheckBox, QMessageBox, QSplitter,
        QAction, QStatusBar, QMainWindow, QMenu, QTabWidget,
        QAbstractItemView, QInputDialog, QToolBox, QScrollArea
    )
    from PyQt5.QtCore import Qt, QSettings, QSize, QCoreApplication
    from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QTextCursor
    # --- Import qt_material AFTER PyQt ---
    import qt_material

    # --- Import qtawesome ---
    import qtawesome as qta

except ImportError as e:
    print(f"Error: Missing required PyQt5 components or qt_material. ({e})")
    print("Please ensure PyQt5 and qt_material are installed correctly.")
    sys.exit(1)


DEFAULT_EXCLUDED_FOLDERS: Set[str] = {
    ".git", "__pycache__", "node_modules", "target", "dist", "build", "venv",
    ".venv", "env", ".env", ".vscode", ".idea", "logs", "temp", "tmp", "bin", "obj",
    "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", "*.egg-info"
}
DEFAULT_EXCLUDED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".o", ".obj", ".class", ".dll", ".so", ".exe", ".bin",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".war", ".ear", ".png", ".jpg",
    ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".ico", ".mp3", ".wav", ".ogg", ".mp4",
    ".avi", ".mov", ".webm", ".db", ".sqlite", ".sqlite3", ".lock", ".pdf", ".doc",
    ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".ttf", ".otf",
    ".woff", ".woff2", ".DS_Store", ".ipynb_checkpoints",
}
ALLOWED_TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".markdown", ".rst", ".adoc", ".asciidoc", ".py", ".java", ".js", ".ts",
    ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass", ".less", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".go", ".rs", ".swift", ".kt", ".kts", ".php", ".rb", ".pl", ".pm", ".lua",
    ".sh", ".bash", ".zsh", ".bat", ".ps1", ".psm1", ".sql", ".r", ".dart", ".groovy", ".scala",
    ".clj", ".cljs", ".cljc", ".edn", ".vb", ".vbs", ".f", ".for", ".f90", ".f95", ".json",
    ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".csv", ".tsv",
    ".env", ".dockerfile", "dockerfile", ".tf", ".tfvars", ".hcl", ".gradle", ".pom",
    ".csproj", ".vbproj", ".sln", ".gitignore", ".gitattributes", ".npmrc", ".yarnrc",
    ".editorconfig", ".babelrc", ".eslintrc", ".prettierrc", ".stylelintrc", ".makefile",
    "makefile", "Makefile", "CMakeLists.txt", ".tex", ".bib", ".sty", ".graphql", ".gql",
    ".vue", ".svelte", ".astro", ".liquid", ".njk", ".jinja", ".jinja2", ".patch", ".diff",
}
TREE_BRANCH, TREE_LAST, TREE_VLINE, TREE_SPACE = "├─ ", "└─ ", "│  ", "   "
FOLDER_ICON, FILE_ICON = "📁", "📄"
DEFAULT_MAX_FILE_SIZE_MB = 1.0

PRESET_EXCLUSIONS: Dict[str, List[str]] = {
    "Python Project": [
        "*.pyc", "*.pyo", "*.pyd", "__pycache__/", "venv/", ".venv/", "env/", ".env/",
        ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".hypothesis/", "build/",
        "dist/", "*.egg-info/", "htmlcov/", ".coverage", "instance/", "*.sqlite3", "*.db",
    ],
    "Node.js Project": [
        "node_modules/", "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*", ".npm",
        ".yarn", "dist/", "build/", "out/", ".env*", "*.local", "coverage/", ".DS_Store",
    ],
    "C/C++ Project": [
        "*.o", "*.obj", "*.a", "*.lib", "*.so", "*.dylib", "*.dll", "*.exe", "build/",
        "bin/", "obj/", "Debug/", "Release/", "*.out", "*.gch", "*.stackdump", ".vscode/",
        ".ccls-cache/", ".cache/", "CMakeCache.txt", "CMakeFiles/", "cmake_install.cmake",
        "CTestTestfile.cmake", "compile_commands.json",
    ],
    "Rust Project": ["target/", "*.rlib", "*.so", "*.dylib", "*.dll", "*.a", "*.exe"],
    "Java Project": [
        "*.class", "*.jar", "*.war", "*.ear", "target/", "build/", "bin/", "out/",
        ".gradle/", ".mvn/", "hs_err_pid*.log", ".project", ".classpath", ".settings/",
        "*.iml", ".idea/",
    ],
}
PRESET_OPTIONS = sorted(PRESET_EXCLUSIONS.keys())

SCRIPT_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = SCRIPT_DIR / "assets"

PLACEHOLDERS = {
    "{FOLDER_NAME}": lambda app: Path(app.folder_path_edit.text()).name if app.folder_path_edit.text() and Path(app.folder_path_edit.text()).exists() else "UnknownProject",
    "{FOLDER_PATH}": lambda app: app.folder_path_edit.text() or "N/A",
    "{DATE}": lambda app: datetime.datetime.now().strftime('%Y-%m-%d'),
    "{TIME}": lambda app: datetime.datetime.now().strftime('%H:%M:%S'),
    "{DATETIME}": lambda app: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "{AUTHOR}": lambda app: os.getenv('USERNAME') or os.getenv('USER', 'Unknown Author'),
}

INTERACTIVE_PROMPT_HEADER = """
You are an expert AI programmer assisting with modifications to the codebase provided in the context above. Follow these steps precisely:

1.  **Plan:** Analyze the user's request ({USER_REQUEST}) and the provided code context. Create a concise plan listing the full paths (relative to `{FOLDER_NAME}/`) of all files you will:
    *   Create (specify if new)
    *   Modify (specify if existing)
    *   Delete (specify if existing)
    Include a brief reason for each action. Format this as a bulleted list under a `## Plan` heading.
2.  **Confirm Plan:** After presenting the plan, STOP and output the exact phrase: `[CONFIRM_PLAN]`
3.  **Await Confirmation:** Do not proceed until the user explicitly confirms the plan.
4.  **Execute (One File at a Time):** If the plan is confirmed, proceed to generate the *full content* for the *first* file listed in your plan (whether creating or modifying).
    *   **Code Header:** For all code files (e.g., .py, .js, .java, .cpp, etc.), add a header comment block at the very top:
        ```
        # -*- coding: utf-8 -*-
        # Project: {FOLDER_NAME}
        # Author: {AUTHOR}
        # Creation Date: {DATE} (or Modification Date if appropriate)
        # Description: [Brief description of the file's purpose]
        ```
        Adjust the comment style (#, //, /* */) based on the file's language.
    *   **Quality:** Ensure the code is well-structured, uses type hinting and docstrings where applicable (especially for Python), and directly addresses the user's request.
    *   **Output:** Present the full file content within a Markdown code block, clearly indicating the file path (e.g., `### File: path/to/your/file.py`).
5.  **Confirm File:** After presenting the *complete* content for *one* file, STOP and output the exact phrase: `[CONFIRM_FILE: path/to/your/file.py]` (replace with the actual path).
6.  **Await Confirmation:** Do not proceed to the next file until the user confirms the current file.
7.  **Repeat:** Repeat steps 4-6 for each subsequent file in your plan. If deleting a file, simply state `Action: Deleting path/to/file.ext` and output `[CONFIRM_FILE: path/to/file.ext]` for confirmation.
8.  **Completion:** Once all planned files are processed and confirmed, output `## Completion\n\nAll planned changes have been processed.`.

**Important:** Adhere strictly to the interactive confirmation steps (`[CONFIRM_PLAN]`, `[CONFIRM_FILE: ...]`). Do not generate multiple files or skip confirmation. Use the provided placeholders in headers and planning paths.
"""

DEFAULT_AI_PROMPT_TEMPLATES = [
    {
        "name": "AI: Add New Feature",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Add a new feature: [*** YOUR DETAILED FEATURE DESCRIPTION HERE ***]"
    },
    {
        "name": "AI: Refactor Function/Class",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Refactor the function/class: [*** SPECIFY FUNCTION/CLASS & REFACTORING GOALS HERE ***]"
    },
    {
        "name": "AI: Add Unit Tests",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Add unit tests for: [*** SPECIFY TARGET FOR TESTS & TESTING FRAMEWORK HERE ***]"
    },
    {
        "name": "AI: Fix Bug",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Fix the bug described: [*** YOUR DETAILED BUG REPORT HERE ***]"
    },
    {
        "name": "AI: Add Documentation (Docstrings)",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Add docstrings to: [*** SPECIFY FILES/FUNCTIONS/CLASSES TO DOCUMENT HERE ***]"
    },
    {
        "name": "AI: Add Documentation (README)",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Create or update the README.md file with: [*** SPECIFY README CONTENT (e.g., project overview, installation, usage) HERE ***]"
    },
    {
        "name": "AI: Improve Error Handling",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Improve error handling in: [*** SPECIFY LOCATION AND TYPE OF ERROR HANDLING NEEDED HERE ***]"
    },
    {
        "name": "AI: Update Dependency Usage",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Update dependency usage: [*** SPECIFY DEPENDENCY AND NECESSARY CODE CHANGES HERE ***]"
    },
    {
        "name": "AI: Convert Class to Functional",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Convert Class to Functional: [*** SPECIFY CLASS AND FILE HERE ***]"
    },
    {
        "name": "AI: Add Configuration File Handling",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Add Configuration File Handling: [*** SPECIFY CONFIG FORMAT AND SETTINGS HERE ***]"
    },
     {
        "name": "AI: Implement Logging",
        "content": f"{INTERACTIVE_PROMPT_HEADER}\n\nUser Request: Implement Logging: [*** SPECIFY LOGGING REQUIREMENTS HERE ***]"
    },
]

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": "2.3",
    "folder_path": "",
    "selected_presets": [],
    "custom_folders": "",
    "custom_extensions": "",
    "custom_patterns": "",
    "dynamic_patterns": "",
    "custom_inclusions": "",
    "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
    "save_output_checked": False,
    "custom_prompt": "",
    "selected_theme": "light_cyan_500.xml",
    "prompt_templates": [],
    "loaded_doc_paths": [],
}
MAX_RECENT_ENVS = 10


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip(' _.')
    return sanitized or "default_filename"

def apply_placeholders(text: str, app_instance: 'FolderStructureApp') -> str:
    text = text.replace("{USER_REQUEST}", "[User-defined request should go here]")
    for key, func in PLACEHOLDERS.items():
        try:
            value = str(func(app_instance))
            text = text.replace(key, value)
        except Exception as e:
            print(f"Warning: Could not apply placeholder {key}: {e}")
    return text

def load_icon(name: str, fallback_theme_name: Optional[str] = None) -> QIcon:
    asset_path = ASSETS_DIR / f"{name}.svg"
    if asset_path.exists():
        icon = QIcon(str(asset_path))
        if not icon.isNull():
            return icon
        else:
            print(f"Warning: Could not load icon from asset: {asset_path}")
    if fallback_theme_name:
        return QIcon.fromTheme(fallback_theme_name)
    else:
        theme_name_guess = name.replace('_', '-')
        return QIcon.fromTheme(theme_name_guess, QIcon())


class FolderProcessor:
    def __init__(self, status_callback=print, warning_callback=print, error_callback=print):
        self.status_callback = status_callback
        self.warning_callback = warning_callback
        self.error_callback = error_callback
        self._active_excluded_folders: Set[str] = set()
        self._active_excluded_extensions: Set[str] = set()
        self._active_excluded_patterns: List[str] = []
        self._active_include_patterns: List[str] = []
        self._max_file_size_bytes: int = 0
        self._root_folder: Path = Path()

    def setup_exclusions_and_limits(
        self,
        selected_preset_names: List[str],
        custom_folders_str: str,
        custom_exts_str: str,
        custom_patterns_str: str,
        dynamic_patterns_list: List[str],
        custom_inclusions_str: str,
        max_size_mb: float
    ):
        self._active_excluded_folders = set(DEFAULT_EXCLUDED_FOLDERS)
        self._active_excluded_extensions = set(DEFAULT_EXCLUDED_EXTENSIONS)
        self._active_excluded_patterns = []
        self._active_include_patterns = []

        collected_preset_patterns: List[str] = []
        for preset_name in selected_preset_names:
            if preset_name in PRESET_EXCLUSIONS:
                collected_preset_patterns.extend(PRESET_EXCLUSIONS[preset_name])
            else:
                self.warning_callback(f"Unknown preset '{preset_name}' selected. Ignoring.")
        self._active_excluded_patterns.extend(collected_preset_patterns)

        custom_folders_set = {f.strip().lower() for f in custom_folders_str.split(',') if f.strip()}
        custom_exts_set = {e.strip().lower() for e in custom_exts_str.split(',') if e.strip() and e.strip().startswith('.')}
        custom_patterns_list = [p.strip() for p in custom_patterns_str.split(',') if p.strip()]

        self._active_excluded_folders.update(custom_folders_set)
        self._active_excluded_extensions.update(custom_exts_set)
        self._active_excluded_patterns.extend(custom_patterns_list)

        if dynamic_patterns_list:
            self._active_excluded_patterns.extend(dynamic_patterns_list)

        self._active_excluded_patterns = sorted(list(set(self._active_excluded_patterns)))

        self._active_include_patterns = [p.strip().replace("\\", "/") for p in custom_inclusions_str.split(',') if p.strip()]

        self._max_file_size_bytes = int(max(0.01, max_size_mb) * 1024 * 1024)

    def _is_excluded(self, item: Path) -> bool:
        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower() if item.is_file() else ""

        if item.is_dir() and item_name_lower in self._active_excluded_folders:
            return True
        if item.is_file() and item_suffix_lower in self._active_excluded_extensions:
            return True

        item_relative_path_str = str(item.relative_to(self._root_folder).as_posix())

        for pattern in self._active_excluded_patterns:
            match = False
            # Handle patterns ending with '/' for directories specifically
            if pattern.endswith('/'):
                if item.is_dir() and fnmatch.fnmatchcase(item.name, pattern[:-1]):
                    match = True
                # Match subdirectory content if pattern is like 'dir/*'
                elif item_relative_path_str.startswith(pattern[:-1]):
                     match = True
            # Handle general file/directory name patterns
            elif fnmatch.fnmatchcase(item.name, pattern):
                match = True
            # Handle patterns matching relative paths (e.g., src/*.temp)
            elif fnmatch.fnmatchcase(item_relative_path_str, pattern):
                match = True

            if match:
                return True
        return False

    def _is_included(self, item: Path) -> bool:
        if not self._active_include_patterns:
            return True

        try:
            item_rel_path = item.relative_to(self._root_folder)
            item_rel_path_str = item_rel_path.as_posix()
        except ValueError:
            return False

        for pattern in self._active_include_patterns:
            # Direct match for the item itself
            if fnmatch.fnmatchcase(item_rel_path_str, pattern):
                return True
            # If the item is inside an included directory
            if item.is_file() or item.is_dir():
                 # Check if any parent part of the path matches a directory include pattern
                for parent_part in item_rel_path.parents:
                    parent_str = parent_part.as_posix()
                    # Match exact directory name or pattern ending in /
                    if fnmatch.fnmatchcase(parent_str, pattern):
                         return True
                    if pattern.endswith('/') and fnmatch.fnmatchcase(parent_str, pattern[:-1]):
                        return True
                    # Check for wildcard directory includes like 'docs/*'
                    if parent_str.startswith(pattern.replace('*','').replace('/','')):
                         return True

        # Special case: if a directory is explicitly included, include its direct children
        # unless they are specifically excluded later. This check is tricky here,
        # better handled in the traversal logic. For now, if it doesn't match directly
        # or isn't inside a matched parent, it's not explicitly included.
        return False

    def _is_text_file(self, file: Path) -> bool:
        return file.suffix.lower() in ALLOWED_TEXT_EXTENSIONS

    def _read_file_content(self, file: Path) -> str:
        try:
            file_size = file.stat().st_size
            if file_size > self._max_file_size_bytes:
                max_size_mb = self._max_file_size_bytes / (1024 * 1024)
                return f"[File content omitted: Exceeds size limit ({max_size_mb:.2f} MB)]"
            if file_size == 0:
                return "[Empty file]"

            try:
                with open(file, "r", encoding="utf-8", errors='strict') as f:
                    content = f.read()
            except UnicodeDecodeError:
                encodings_to_try = ['latin-1', 'cp1252']
                content = None
                for enc in encodings_to_try:
                    try:
                        with open(file, "r", encoding=enc) as f:
                            content = f.read()
                        self.warning_callback(f"File {file.name} decoded using {enc} after UTF-8 failed.")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as read_err:
                        self.warning_callback(f"Error reading file {file.name} with {enc}: {str(read_err)}")
                        return f"[Error reading file: {str(read_err)}]"

                if content is None:
                    self.warning_callback(f"Could not decode file {file.name} with tested encodings.")
                    return f"[Error reading file: Could not decode]"

            except Exception as read_err:
                self.warning_callback(f"Error reading file {file.name}: {str(read_err)}")
                return f"[Error reading file: {str(read_err)}]"

            lines = content.splitlines()
            if lines and any(len(line) > 5000 for line in lines):
                self.warning_callback(f"File {file.name} contains very long lines (>5000 chars). Content included.")

            return content if content else "[File appears empty after read]"

        except OSError as os_err:
            self.warning_callback(f"OS error accessing file {file.name}: {str(os_err)}")
            return f"[Error accessing file: {str(os_err)}]"
        except Exception as e:
            self.error_callback(f"Unexpected error reading file {file.name}: {str(e)}\n{traceback.format_exc()}")
            return f"[Unexpected error reading file]"

    def _build_tree_and_collect_files(
        self,
        current_folder: Path,
        prefix: str = ""
    ) -> Tuple[List[str], List[Path]]:
        tree_lines: List[str] = []
        found_files: List[Path] = []
        included_items_paths = set()

        try:
            # First pass: Iterate and filter based on exclusion and inclusion rules
            items_to_consider = []
            for item in current_folder.iterdir():
                if self._is_excluded(item):
                    continue
                if self._is_included(item):
                     items_to_consider.append(item)
                     included_items_paths.add(item) # Mark this specific item
                     # If a directory is included, mark its direct children path for potential inclusion check later
                     if item.is_dir():
                         try:
                            for child in item.iterdir():
                                if self._is_included(child): # Re-check child based on parent inclusion logic? Simpler to rely on _is_included pattern matching.
                                    included_items_paths.add(child)
                         except (PermissionError, OSError):
                             pass # Ignore errors listing children here


            # Filter items_to_consider again: only keep those explicitly marked or inside a marked dir
            # This might be redundant if _is_included correctly handles parent paths.
            # Let's rely on _is_included for simplicity first.
            # final_items = items_to_consider

            # Sort the filtered items
            items = sorted(items_to_consider, key=lambda x: (x.is_file(), x.name.lower()))

        except PermissionError:
            tree_lines.append(f"{prefix}[Error: Permission denied]")
            self.warning_callback(f"Permission denied listing directory: {current_folder}")
            return tree_lines, found_files
        except OSError as e:
            tree_lines.append(f"{prefix}[Error: {e.strerror}]")
            self.warning_callback(f"OS error listing directory {current_folder}: {e}")
            return tree_lines, found_files

        num_items = len(items)
        for i, item in enumerate(items):
            is_last = (i == num_items - 1)
            connector = TREE_LAST if is_last else TREE_BRANCH
            line_prefix = prefix + connector
            child_prefix = prefix + (TREE_SPACE if is_last else TREE_VLINE)

            if item.is_dir():
                tree_lines.append(f"{line_prefix}{FOLDER_ICON} {item.name}/")
                sub_tree_lines, sub_found_files = self._build_tree_and_collect_files(item, child_prefix)
                tree_lines.extend(sub_tree_lines)
                found_files.extend(sub_found_files)
            elif item.is_file():
                if self._is_text_file(item):
                    tree_lines.append(f"{line_prefix}{FILE_ICON} {item.name}")
                    found_files.append(item)
                else:
                     if self._active_include_patterns: # Only show skip message if inclusions are active and this file wasn't filtered earlier
                         tree_lines.append(f"{line_prefix}{FILE_ICON} {item.name} [Skipped: Non-text/Binary]")
                     # Otherwise, if no includes, it was already filtered by the initial pass

        return tree_lines, found_files

    def _generate_file_contents_markdown(self, root_folder: Path, file_paths: List[Path]) -> List[str]:
        content_lines = ["", "---", "", "## File Contents"]
        if not file_paths:
            content_lines.append("\n*No text files found or included based on filters, inclusions, and size limits.*")
            return content_lines

        file_paths.sort(key=lambda p: str(p.relative_to(root_folder)).lower() if root_folder in p.parents or root_folder == p.parent else p.name.lower())

        for file_path in file_paths:
            try:
                relative_path = file_path.relative_to(root_folder)
            except ValueError:
                relative_path = file_path.name
                self.warning_callback(f"Could not determine relative path for {file_path}. Using filename.")

            relative_path_str = str(relative_path).replace("\\", "/")
            content_lines.append(f"\n### `{relative_path_str}`")

            file_content = self._read_file_content(file_path)

            lang = file_path.suffix[1:].lower() if file_path.suffix else "text"
            lang = "".join(c for c in lang if c.isalnum()) or "text"
            aliases = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript',
                'jsx': 'javascript', 'md': 'markdown', 'sh': 'bash', 'yml': 'yaml', 'yaml': 'yaml',
                'dockerfile': 'docker', 'h': 'c', 'hpp': 'cpp', 'cs': 'csharp',
                'rb': 'ruby', 'pl': 'perl', 'kt': 'kotlin', 'rs': 'rust', 'go': 'golang',
                'html': 'html', 'css': 'css', 'scss': 'scss', 'vue': 'vue', 'java': 'java',
                'xml': 'xml', 'json': 'json', 'sql': 'sql', 'php': 'php'
            }
            lang = aliases.get(lang, lang)

            content_lines.append(f"```{lang}")
            content_lines.extend(file_content.splitlines() if file_content else [""])
            content_lines.append("```")

        return content_lines

    def generate_structure_text(
        self,
        folder_path_str: str,
        selected_preset_names: List[str],
        custom_folders_str: str,
        custom_exts_str: str,
        custom_patterns_str: str,
        dynamic_exclude_str: str,
        custom_inclusions_str: str,
        max_size_mb: float,
        custom_prompt: str = "",
        documentation_prompt: str = ""
    ) -> str:
        if not folder_path_str:
            self.error_callback("No folder path specified.")
            return "```error\nError: No folder path specified.\n```"

        try:
            self._root_folder = Path(folder_path_str).resolve()
            if not self._root_folder.exists():
                self.error_callback(f"Folder not found: {self._root_folder}")
                return f"```error\nError: Folder not found: {self._root_folder}\n```"
            if not self._root_folder.is_dir():
                self.error_callback(f"Path is not a directory: {self._root_folder}")
                return f"```error\nError: Path is not a directory: {self._root_folder}\n```"
        except Exception as e:
            self.error_callback(f"Error resolving path '{folder_path_str}': {e}")
            return f"```error\nError resolving path: {e}\n```"

        dynamic_patterns = [p.strip() for p in dynamic_exclude_str.split(',') if p.strip()]

        try:
            self.setup_exclusions_and_limits(
                selected_preset_names, custom_folders_str, custom_exts_str,
                custom_patterns_str, dynamic_patterns, custom_inclusions_str, max_size_mb
            )
        except Exception as e:
            self.error_callback(f"Error setting up exclusions/inclusions: {e}\n{traceback.format_exc()}")
            return f"```error\nError setting up filters: {e}\n```"

        self.status_callback(f"Starting analysis for: {self._root_folder}...")
        try:
            tree_lines, found_files = self._build_tree_and_collect_files(self._root_folder, prefix="")

            structure_output_lines = [
                f"# Folder Structure: {self._root_folder.name}",
                f"*(Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*",
                "",
                "```text",
                f"{FOLDER_ICON} {self._root_folder.name}/"
            ]
            structure_output_lines.extend(tree_lines)
            structure_output_lines.append("```")

            content_output_lines = self._generate_file_contents_markdown(self._root_folder, found_files)

            full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)

            final_prompt = ""
            if documentation_prompt:
                final_prompt += "## Imported Documentation\n\n" + documentation_prompt.strip() + "\n\n---\n\n"
            if custom_prompt and custom_prompt.strip():
                 final_prompt += "## Custom Instructions\n\n" + custom_prompt.strip()

            if final_prompt:
                 full_output += "\n\n---\n\n" + final_prompt

            self.status_callback(f"Analysis complete. Included {len(found_files)} text files.")
            return full_output.strip()

        except PermissionError as pe:
            self.error_callback(f"Permission error during processing of {self._root_folder}: {str(pe)}")
            return f"```error\nError: Permission denied accessing folder contents: {str(pe)}\n```"
        except Exception as e:
            self.error_callback(f"An unexpected error occurred during processing: {str(e)}\n{traceback.format_exc()}")
            return f"```error\nError: An unexpected error occurred: {str(e)}\n```"


class ManageRecentDialog(QDialog):
    def __init__(self, recent_envs: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Recent Environments")
        self.setMinimumWidth(450)
        self.recent_envs = recent_envs

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select environments to remove:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for env in self.recent_envs:
            item = QListWidgetItem(f"{env['name']} ({env['path']})")
            item.setData(Qt.UserRole, env['path'])
            item.setToolTip(env['path'])
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        remove_button = QPushButton(load_icon("edit-delete", "edit-delete"), "Remove Selected")
        remove_button.clicked.connect(self.remove_selected)
        layout.addWidget(remove_button)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more environments to remove.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove {len(selected_items)} selected environment(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            paths_to_remove = {item.data(Qt.UserRole) for item in selected_items}
            self.recent_envs[:] = [env for env in self.recent_envs if env['path'] not in paths_to_remove]
            self.list_widget.clear()
            for env in self.recent_envs:
                item = QListWidgetItem(f"{env['name']} ({env['path']})")
                item.setData(Qt.UserRole, env['path'])
                item.setToolTip(env['path'])
                self.list_widget.addItem(item)

    def get_updated_list(self) -> List[Dict[str, str]]:
        return self.recent_envs

class EditTemplateDialog(QDialog):
    def __init__(self, template_name="", template_content="", existing_names=None, parent=None):
        super().__init__(parent)
        self.existing_names = existing_names or []
        self.original_name = template_name

        self.setWindowTitle("Edit Prompt Template" if template_name else "Add Prompt Template")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit(template_name)
        self.name_edit.setPlaceholderText("Enter a unique name for the template")
        form_layout.addRow("Template Name:", self.name_edit)
        layout.addLayout(form_layout)

        layout.addWidget(QLabel("Template Content:"))
        self.content_edit = QTextEdit(template_content)
        self.content_edit.setPlaceholderText(
            "Enter the prompt template content. Use placeholders like {FOLDER_NAME}, {AUTHOR}, {DATE} etc."
        )
        self.content_edit.setAcceptRichText(False)
        layout.addWidget(self.content_edit)

        ai_placeholders_label = QLabel(
            "Standard AI interaction sequences: [CONFIRM_PLAN], [CONFIRM_FILE: path/to/file.ext]"
        )
        ai_placeholders_label.setWordWrap(True)
        ai_placeholders_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(ai_placeholders_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        name = self.get_template_name()
        if not name:
            QMessageBox.warning(self, "Input Error", "Template name cannot be empty.")
            self.name_edit.setFocus()
            return

        if name != self.original_name and name in self.existing_names:
            QMessageBox.warning(self, "Input Error", f"A template with the name '{name}' already exists.")
            self.name_edit.selectAll()
            self.name_edit.setFocus()
            return

        if not self.get_template_content():
            QMessageBox.warning(self, "Input Error", "Template content cannot be empty.")
            self.content_edit.setFocus()
            return

        self.accept()

    def get_template_name(self) -> str:
        return self.name_edit.text().strip()

    def get_template_content(self) -> str:
        return self.content_edit.toPlainText().strip()

class PromptTemplateManagerDialog(QDialog):
    def __init__(self, templates: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.templates = templates
        self.parent_app = parent

        self.setWindowTitle("Manage Prompt Templates")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addWidget(QLabel("Templates:"))
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.display_selected_template)
        self.populate_list()
        left_layout.addWidget(self.list_widget)

        button_hbox = QHBoxLayout()
        add_button = QPushButton(load_icon("list-add", "list-add"), "Add...")
        edit_button = QPushButton(load_icon("document-edit", "document-edit"), "Edit...")
        remove_button = QPushButton(load_icon("list-remove", "list-remove"), "Remove")
        copy_button = QPushButton(load_icon("edit-copy", "edit-copy"), "Copy")

        add_button.clicked.connect(self.add_template)
        edit_button.clicked.connect(self.edit_template)
        remove_button.clicked.connect(self.remove_template)
        copy_button.clicked.connect(self.copy_template)

        button_hbox.addWidget(add_button)
        button_hbox.addWidget(edit_button)
        button_hbox.addWidget(remove_button)
        button_hbox.addWidget(copy_button)
        left_layout.addLayout(button_hbox)

        right_layout.addWidget(QLabel("Selected Template Content Preview:"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setFont(QFont("Courier New", 9))
        self.preview_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        right_layout.addWidget(self.preview_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        right_layout.addWidget(button_box)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

    def populate_list(self):
        self.list_widget.clear()
        self.templates.sort(key=lambda t: t.get('name', '').lower())
        for i, template in enumerate(self.templates):
            item = QListWidgetItem(template.get('name', f'Unnamed Template {i+1}'))
            item.setData(Qt.UserRole, i)
            self.list_widget.addItem(item)
        self.preview_edit.clear()

    def display_selected_template(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            index = item.data(Qt.UserRole)
            if 0 <= index < len(self.templates):
                template = self.templates[index]
                self.preview_edit.setPlainText(template.get('content', ''))
            else:
                self.preview_edit.setPlainText("[Error: Template index out of bounds]")
                print(f"Error: Invalid index {index} for template list of size {len(self.templates)}")
        else:
            self.preview_edit.clear()

    def get_current_template_names(self) -> List[str]:
        return [t.get('name', '') for t in self.templates]

    def add_template(self):
        dialog = EditTemplateDialog(existing_names=self.get_current_template_names(), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_template = {
                "name": dialog.get_template_name(),
                "content": dialog.get_template_content()
            }
            self.templates.append(new_template)
            self.populate_list()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() == new_template["name"]:
                    self.list_widget.setCurrentItem(item)
                    break
            if self.parent_app:
                self.parent_app.show_status("Template added.")

    def edit_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to edit.")
            return

        item = selected_items[0]
        index = item.data(Qt.UserRole)
        if not (0 <= index < len(self.templates)):
            QMessageBox.critical(self, "Error", "Selected item has an invalid index.")
            return

        template_to_edit = self.templates[index]
        other_names = [t.get('name', '') for i, t in enumerate(self.templates) if i != index]

        dialog = EditTemplateDialog(
            template_name=template_to_edit.get('name', ''),
            template_content=template_to_edit.get('content', ''),
            existing_names=other_names,
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            updated_template = {
                "name": dialog.get_template_name(),
                "content": dialog.get_template_content()
            }
            self.templates[index] = updated_template
            self.populate_list()
            for i in range(self.list_widget.count()):
                list_item = self.list_widget.item(i)
                if list_item.data(Qt.UserRole) == index:
                    self.list_widget.setCurrentItem(list_item)
                    break
            if self.parent_app:
                self.parent_app.show_status("Template updated.")

    def remove_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to remove.")
            return

        item = selected_items[0]
        index = item.data(Qt.UserRole)
        if not (0 <= index < len(self.templates)):
            QMessageBox.critical(self, "Error", "Selected item has an invalid index.")
            return

        template_name = self.templates[index].get('name', 'this template')
        confirm = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove the template '{template_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            del self.templates[index]
            self.populate_list()
            if self.parent_app:
                self.parent_app.show_status("Template removed.")

    def copy_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to copy.")
            return

        item = selected_items[0]
        index = item.data(Qt.UserRole)
        if not (0 <= index < len(self.templates)):
            QMessageBox.critical(self, "Error", "Selected item has an invalid index.")
            return

        original_template = self.templates[index]
        original_name = original_template.get('name', 'Unnamed')

        copy_count = 1
        new_name = f"{original_name} (Copy)"
        existing_names = self.get_current_template_names()
        while new_name in existing_names:
            copy_count += 1
            new_name = f"{original_name} (Copy {copy_count})"

        new_template = {
            "name": new_name,
            "content": original_template.get('content', '')
        }
        self.templates.append(new_template)
        self.populate_list()

        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item.text() == new_name:
                self.list_widget.setCurrentItem(list_item)
                break
        if self.parent_app:
            self.parent_app.show_status(f"Template copied as '{new_name}'.")

    def get_updated_templates(self) -> List[Dict[str, str]]:
        return self.templates


class FolderStructureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        QCoreApplication.setOrganizationName("AICodeHelper")
        QCoreApplication.setApplicationName("FolderStructureAppV2")
        self.settings = QSettings()

        self.processor = FolderProcessor(
            status_callback=self.show_status,
            warning_callback=self.show_warning,
            error_callback=self.show_error
        )
        self.current_environment_file: Optional[Path] = None
        self.recent_environments: List[Dict[str, str]] = []
        self.prompt_templates: List[Dict[str, str]] = []
        self.loaded_doc_paths: List[str] = []
        self.current_theme: str = DEFAULT_SETTINGS['selected_theme']

        self.initUI()
        self.load_persistent_settings()
        self.create_actions()
        self.create_menus()
        self.create_status_bar()
        self._update_recent_menu()
        self._update_template_combo()
        self._update_doc_list_widget()

        self.apply_theme(self.current_theme, startup=True)
        self.load_initial_environment()

    def show_status(self, message: str):
        self.statusBar().showMessage(message, 5000)
        print(f"INFO: {message}")

    def show_warning(self, message: str):
        self.statusBar().showMessage(f"Warning: {message}", 8000)
        QMessageBox.warning(self, "Warning", message)
        print(f"WARNING: {message}")

    def show_error(self, message: str):
        self.statusBar().showMessage(f"Error: {message}", 10000)
        QMessageBox.critical(self, "Error", message)
        print(f"ERROR: {message}")

    def initUI(self):
        self.setWindowTitle('Folder Structure to Text v2.3')
        self.setGeometry(100, 100, 1100, 850)

        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)

        settings_widget = QWidget()
        settings_outer_layout = QVBoxLayout(settings_widget)
        settings_outer_layout.setSpacing(10)
        self._create_settings_tab_content(settings_outer_layout)
        self.main_tabs.addTab(
            settings_widget,
            load_icon("preferences-system", "preferences-system"),
            "Settings"
        )

        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setSpacing(10)
        self._create_output_tab_content(output_layout)
        self.main_tabs.addTab(
            output_widget,
            load_icon("text-x-generic", "text-x-generic"),
            "Output"
        )

    def _create_settings_tab_content(self, layout: QVBoxLayout):
        folder_group = QGroupBox("Target Project Folder")
        folder_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("Select the target folder...")
        self.folder_path_edit.textChanged.connect(self._handle_folder_change_for_title)
        browse_button = QPushButton(load_icon("folder-open", "folder-open"), "Browse...")
        browse_button.setToolTip("Select the root folder of the project")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_path_edit, 1)
        folder_layout.addWidget(browse_button)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        scroll_content_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_content_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        self.settings_toolbox = QToolBox()
        self.settings_toolbox.layout().setSpacing(6)

        preset_widget = QWidget()
        preset_layout = QVBoxLayout(preset_widget)
        preset_layout.setContentsMargins(9, 9, 9, 9)
        preset_label = QLabel("Exclusion Presets (Ctrl/Shift + Click for multiple):")
        preset_layout.addWidget(preset_label)
        self.preset_list_widget = QListWidget()
        self.preset_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.preset_list_widget.addItems(PRESET_OPTIONS)
        self.preset_list_widget.setFixedHeight(130)
        self.preset_list_widget.setToolTip("Combine presets. Select none to use only defaults + custom.")
        preset_layout.addWidget(self.preset_list_widget)
        self.settings_toolbox.addItem(
            preset_widget,
            load_icon("preferences-exclude", "preferences-exclude"),
            "Exclusion Presets"
        )

        custom_filter_widget = QWidget()
        custom_filter_layout = QVBoxLayout(custom_filter_widget)
        custom_filter_layout.setContentsMargins(9, 9, 9, 9)
        custom_group = QGroupBox("Custom Filtering Rules (Comma-separated)")
        custom_form_layout = QFormLayout(custom_group)
        self.custom_folders_edit = QLineEdit()
        self.custom_folders_edit.setPlaceholderText("e.g., docs,tests,temp")
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText("e.g., .log,.tmp,.bak")
        self.custom_patterns_edit = QLineEdit()
        self.custom_patterns_edit.setPlaceholderText("e.g., *.log,temp_*,cache_*/")
        self.dynamic_exclude_edit = QLineEdit()
        self.dynamic_exclude_edit.setPlaceholderText("e.g., *.private,credentials.json")
        self.custom_inclusions_edit = QLineEdit()
        self.custom_inclusions_edit.setPlaceholderText("e.g., src/main/, README.md, docs/*.md")

        custom_form_layout.addRow("Exclude Folders:", self.custom_folders_edit)
        custom_form_layout.addRow("Exclude Exts:", self.custom_extensions_edit)
        custom_form_layout.addRow("Exclude Patterns:", self.custom_patterns_edit)
        custom_form_layout.addRow("Dynamic Exclude:", self.dynamic_exclude_edit)
        custom_form_layout.addRow("Include Paths/Patterns:", self.custom_inclusions_edit)
        custom_filter_layout.addWidget(custom_group)
        self.settings_toolbox.addItem(
            custom_filter_widget,
            load_icon("view-filter", "view-filter"),
            "Custom Filtering (Exclusions & Inclusions)"
        )

        options_widget = QWidget()
        options_layout = QFormLayout(options_widget)
        options_layout.setContentsMargins(9, 9, 9, 9)
        self.max_size_spinbox = QDoubleSpinBox()
        self.max_size_spinbox.setSuffix(" MB")
        self.max_size_spinbox.setMinimum(0.01)
        self.max_size_spinbox.setMaximum(500.0)
        self.max_size_spinbox.setSingleStep(0.1)
        self.max_size_spinbox.setValue(DEFAULT_MAX_FILE_SIZE_MB)
        self.save_output_checkbox = QCheckBox("Save Markdown output automatically on Generate")
        options_layout.addRow("Max File Size:", self.max_size_spinbox)
        options_layout.addRow(self.save_output_checkbox)
        self.settings_toolbox.addItem(
            options_widget,
            load_icon("preferences-desktop-display", "preferences-desktop-display"),
            "Generation Options"
        )

        doc_integration_widget = QWidget()
        doc_layout = QVBoxLayout(doc_integration_widget)
        doc_layout.setContentsMargins(9, 9, 9, 9)
        doc_layout.addWidget(QLabel("Import Markdown documentation files:"))
        self.doc_list_widget = QListWidget()
        self.doc_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.doc_list_widget.setToolTip("Content of these files will be added to the prompt.")
        self.doc_list_widget.setFixedHeight(100)
        doc_layout.addWidget(self.doc_list_widget)
        doc_button_layout = QHBoxLayout()
        add_doc_button = QPushButton(load_icon("document-open", "document-open"), "Add Docs...")
        add_doc_button.clicked.connect(self.add_documentation)
        remove_doc_button = QPushButton(load_icon("list-remove", "list-remove"), "Remove Selected")
        remove_doc_button.clicked.connect(self.remove_documentation)
        clear_docs_button = QPushButton(load_icon("edit-clear", "edit-clear"), "Clear All")
        clear_docs_button.clicked.connect(self.clear_documentation)
        doc_button_layout.addWidget(add_doc_button)
        doc_button_layout.addWidget(remove_doc_button)
        doc_button_layout.addWidget(clear_docs_button)
        doc_layout.addLayout(doc_button_layout)
        self.settings_toolbox.addItem(
            doc_integration_widget,
            load_icon("text-markdown", "text-markdown"),
             "Documentation Integration"
        )

        scroll_layout.addWidget(self.settings_toolbox)
        scroll_area.setWidget(scroll_content_widget)
        layout.addWidget(scroll_area, 1)

        prompt_group = QGroupBox("Custom Instructions Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_template_layout = QHBoxLayout()
        prompt_template_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.setToolTip("Select a saved prompt template")
        self.template_combo.addItem("-- Select Template --")
        load_template_button = QPushButton(load_icon("document-open", "document-open"), "Load")
        load_template_button.setToolTip("Load selected template into the text area below")
        load_template_button.clicked.connect(self.load_selected_template)
        save_template_button = QPushButton(load_icon("document-save-as", "document-save-as"), "Save As...")
        save_template_button.setToolTip("Save the current text below as a new template")
        save_template_button.clicked.connect(self.save_template_as)
        manage_template_button = QPushButton(load_icon("document-properties", "document-properties"), "Manage...")
        manage_template_button.setToolTip("Add, edit, remove, or copy prompt templates")
        manage_template_button.clicked.connect(self.manage_prompt_templates)
        prompt_template_layout.addWidget(self.template_combo, 1)
        prompt_template_layout.addWidget(load_template_button)
        prompt_template_layout.addWidget(save_template_button)
        prompt_template_layout.addWidget(manage_template_button)
        prompt_layout.addLayout(prompt_template_layout)
        self.custom_prompt_edit = QTextEdit()
        self.custom_prompt_edit.setPlaceholderText(
            "Enter instructions for an AI, or load a template. Placeholders like {FOLDER_NAME} will be substituted. Imported documentation will be added above this."
        )
        self.custom_prompt_edit.setAcceptRichText(False)
        self.custom_prompt_edit.setMinimumHeight(120)
        prompt_layout.addWidget(self.custom_prompt_edit)
        layout.addWidget(prompt_group)

        self.generate_button = QPushButton(load_icon("system-run", "system-run"), "Generate Structure Text")
        self.generate_button.setToolTip("Analyze the selected folder and generate the output")
        self.generate_button.clicked.connect(self.generate_structure)
        layout.addWidget(self.generate_button, 0, Qt.AlignCenter)

    def _create_output_tab_content(self, layout: QVBoxLayout):
        self.output_tabs = QTabWidget()

        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        self.raw_output_textedit = QTextEdit()
        self.raw_output_textedit.setReadOnly(True)
        self.raw_output_textedit.setFont(QFont("Courier New", 10))
        self.raw_output_textedit.setLineWrapMode(QTextEdit.NoWrap)
        self.raw_output_textedit.setPlaceholderText("Generated Markdown output will appear here.")
        raw_layout.addWidget(self.raw_output_textedit)
        self.output_tabs.addTab(raw_widget, load_icon("text-plain", "text-plain"), "Raw Markdown")

        rendered_widget = QWidget()
        render_layout = QVBoxLayout(rendered_widget)
        render_layout.setContentsMargins(0, 0, 0, 0)
        self.rendered_output_view = QTextEdit()
        self.rendered_output_view.setReadOnly(True)
        self.rendered_output_view.setPlaceholderText("A basic rendered preview of the Markdown will appear here.")
        render_layout.addWidget(self.rendered_output_view)
        self.output_tabs.addTab(rendered_widget, load_icon("text-html", "text-html"), "Rendered Preview")

        layout.addWidget(self.output_tabs)

        output_button_layout = QHBoxLayout()
        self.copy_raw_button = QPushButton(load_icon("edit-copy", "edit-copy"), "Copy Raw Markdown")
        self.copy_raw_button.setToolTip("Copy the full raw Markdown output to the clipboard")
        self.copy_raw_button.clicked.connect(self.copy_raw_output)
        self.copy_raw_button.setEnabled(False)
        clear_output_button = QPushButton(load_icon("edit-clear", "edit-clear"), "Clear Output")
        clear_output_button.clicked.connect(self.clear_output)
        output_button_layout.addWidget(self.copy_raw_button)
        output_button_layout.addStretch(1)
        output_button_layout.addWidget(clear_output_button)
        layout.addLayout(output_button_layout)

    def create_actions(self):
        self.new_project_action = QAction(
            load_icon("document-new", "document-new"), "&New Project", self,
            shortcut="Ctrl+N", statusTip="Clear folder path and start new analysis (keeps current settings)",
            triggered=self.new_project
        )
        self.load_env_action = QAction(
            load_icon("document-open", "document-open"), "&Load Environment...", self,
            shortcut="Ctrl+L", statusTip="Load configuration from a JSON file",
            triggered=self.load_environment_dialog
        )
        self.save_env_action = QAction(
            load_icon("document-save", "document-save"), "&Save Environment", self,
            shortcut="Ctrl+S", statusTip="Save current configuration to the current file",
            triggered=self.save_current_environment
        )
        self.save_env_as_action = QAction(
            load_icon("document-save-as", "document-save-as"), "Save Environment &As...", self,
            shortcut="Ctrl+Shift+S", statusTip="Save current configuration to a new JSON file",
            triggered=self.save_environment_as
        )
        self.manage_recent_action = QAction(
            "&Manage Recent Environments...", self,
            statusTip="View and remove recent environment files",
            triggered=self.manage_recent_environments
        )
        self.exit_action = QAction(
            load_icon("application-exit", "application-exit"), "E&xit", self,
            shortcut="Ctrl+Q", statusTip="Exit the application",
            triggered=self.close
        )

        self.reset_settings_action = QAction(
            load_icon("view-refresh", "view-refresh"), "&Reset All Settings", self,
            shortcut="Ctrl+R", statusTip="Reset all settings to their defaults",
            triggered=self.reset_settings
        )
        self.clear_output_action = QAction(
            load_icon("edit-clear", "edit-clear"), "&Clear Output Area", self,
            shortcut="Ctrl+Shift+C", statusTip="Clear the output text area",
            triggered=self.clear_output
        )

        self.theme_actions = []
        available_themes = [
            'dark_blue.xml', 'dark_cyan.xml', 'dark_teal.xml', 'dark_amber.xml', 'dark_red.xml',
            'light_blue.xml', 'light_cyan.xml', 'light_cyan_500.xml', 'light_teal.xml', 'light_amber.xml', 'light_red.xml'
        ]
        for theme_file in sorted(available_themes):
            theme_name = theme_file.replace('.xml', '').replace('_', ' ').title()
            action = QAction(theme_name, self, checkable=True,
                             triggered=functools.partial(self.change_theme, theme_file))
            self.theme_actions.append(action)

        self.save_env_action.setEnabled(self.current_environment_file is not None)

    def create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.load_env_action)
        self.recent_env_menu = file_menu.addMenu(
            load_icon("document-open-recent", "document-open-recent"),
            "Load Recent Environment"
        )
        file_menu.addAction(self.manage_recent_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_env_action)
        file_menu.addAction(self.save_env_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.reset_settings_action)
        edit_menu.addAction(self.clear_output_action)

        view_menu = menu_bar.addMenu("&View")
        theme_menu = view_menu.addMenu(
            load_icon("preferences-desktop-theme", "preferences-desktop-theme"),
            "&Theme"
        )
        for action in self.theme_actions:
            theme_menu.addAction(action)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def browse_folder(self):
        start_dir = self.settings.value("lastBrowseDir", str(Path.home()))
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", self.folder_path_edit.text() or start_dir
        )
        if folder:
            self.folder_path_edit.setText(folder)
            self.settings.setValue("lastBrowseDir", folder)
            self.show_status(f"Selected folder: {folder}")
            self._update_window_title()

    def new_project(self):
        confirm = QMessageBox.question(
            self, "New Project",
            "Clear the target folder path and output, and disconnect the current environment file (if any)?\n\nCurrent exclusion, inclusion, prompt, documentation, and other settings will be kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if confirm == QMessageBox.Yes:
            self.folder_path_edit.clear()
            self.clear_output()
            self.current_environment_file = None
            self.save_env_action.setEnabled(False)
            self._update_window_title()
            self.show_status("New project started. Settings kept, folder cleared.")
            self.folder_path_edit.setFocus()

    def clear_output(self):
        self.raw_output_textedit.clear()
        self.rendered_output_view.clear()
        self.copy_raw_button.setEnabled(False)
        self.show_status("Output cleared.")

    def copy_raw_output(self):
        content = self.raw_output_textedit.toPlainText()
        if content:
            QApplication.clipboard().setText(content)
            self.show_status("Raw Markdown copied to clipboard.")
        else:
            self.show_warning("Output is empty, nothing to copy.")

    def update_rendered_output(self):
        raw_markdown = self.raw_output_textedit.toPlainText()
        if raw_markdown.startswith("```error"):
            self.rendered_output_view.setPlainText(raw_markdown)
        elif raw_markdown:
            self.rendered_output_view.setMarkdown(raw_markdown)
            self.rendered_output_view.moveCursor(QTextCursor.Start)
            self.rendered_output_view.ensureCursorVisible()
        else:
            self.rendered_output_view.clear()
            self.rendered_output_view.setPlaceholderText(
                "A basic rendered preview of the Markdown will appear here."
            )

    def reset_settings(self):
        confirm = QMessageBox.question(
            self, "Confirm Reset",
            "Reset ALL settings (filters, inclusions, prompt, docs, templates, theme) to defaults and clear folder/output?\nEnvironment association will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            default_settings_copy = DEFAULT_SETTINGS.copy()
            default_settings_copy["prompt_templates"] = list(DEFAULT_AI_PROMPT_TEMPLATES)
            default_settings_copy["loaded_doc_paths"] = []

            self.apply_settings_to_ui(default_settings_copy)
            self.folder_path_edit.clear()
            self.clear_output()

            self.prompt_templates = default_settings_copy["prompt_templates"]
            self.loaded_doc_paths = default_settings_copy["loaded_doc_paths"]
            self.current_theme = default_settings_copy["selected_theme"]
            self.current_environment_file = None

            self._update_template_combo()
            self._update_doc_list_widget()
            self.apply_theme(self.current_theme)
            self._update_window_title()
            self.save_env_action.setEnabled(False)

            self.show_status("All settings reset to defaults.")

    def apply_theme(self, theme_file: str, startup: bool = False):
        try:
            if not theme_file:
                theme_file = DEFAULT_SETTINGS['selected_theme']
                print(f"Warning: Invalid theme '{theme_file}' provided, falling back to default {DEFAULT_SETTINGS['selected_theme']}.")

            if not startup:
                self.show_status(f"Applying theme: {theme_file}...")

            qt_material.apply_stylesheet(
                QApplication.instance(),
                theme=theme_file,
                invert_secondary= ('dark' in theme_file) # Invert secondary for dark themes for better contrast sometimes
            )

            self.current_theme = theme_file
            self.settings.setValue("selectedTheme", theme_file)

            for action in self.theme_actions:
                action.setChecked(action.text().lower().replace(' ', '_') + ".xml" == theme_file)

            if not startup:
                self.show_status(f"Theme '{theme_file}' applied.")

        except Exception as e:
            self.show_error(f"Failed to apply theme '{theme_file}': {e}")
            if theme_file != DEFAULT_SETTINGS['selected_theme']:
                self.apply_theme(DEFAULT_SETTINGS['selected_theme'])

    def change_theme(self, theme_file: str):
        self.apply_theme(theme_file)

    def get_settings_from_ui(self) -> Dict[str, Any]:
        selected_presets = [item.text() for item in self.preset_list_widget.selectedItems()]

        user_templates = [
            t for t in self.prompt_templates if t not in DEFAULT_AI_PROMPT_TEMPLATES
        ]

        settings = {
            "version": "2.3",
            "folder_path": self.folder_path_edit.text(),
            "selected_presets": selected_presets,
            "custom_folders": self.custom_folders_edit.text(),
            "custom_extensions": self.custom_extensions_edit.text(),
            "custom_patterns": self.custom_patterns_edit.text(),
            "dynamic_patterns": self.dynamic_exclude_edit.text(),
            "custom_inclusions": self.custom_inclusions_edit.text(),
            "max_file_size_mb": self.max_size_spinbox.value(),
            "save_output_checked": self.save_output_checkbox.isChecked(),
            "custom_prompt": self.custom_prompt_edit.toPlainText(),
            "selected_theme": self.current_theme,
            "prompt_templates": user_templates,
            "loaded_doc_paths": self.loaded_doc_paths,
        }
        return settings

    def apply_settings_to_ui(self, settings_dict: Dict[str, Any]):
        loaded_version = settings_dict.get("version", "1.0")
        is_legacy_v1 = loaded_version.startswith("1.")
        is_legacy_v2_2 = loaded_version == "2.2"

        if is_legacy_v1 or is_legacy_v2_2:
             print(f"INFO: Loading settings from a legacy format (v{loaded_version}). Applying defaults for new features.")

        self.folder_path_edit.setText(settings_dict.get("folder_path", DEFAULT_SETTINGS["folder_path"]))

        self.preset_list_widget.clearSelection()
        selected_presets = []
        if "selected_presets" in settings_dict and isinstance(settings_dict["selected_presets"], list):
            selected_presets = settings_dict["selected_presets"]
        elif is_legacy_v1 and "preset" in settings_dict:
            legacy_preset = settings_dict.get("preset")
            if legacy_preset and legacy_preset not in ["Custom", "None/Defaults"]:
                selected_presets = [legacy_preset]
        for preset_name in selected_presets:
            items = self.preset_list_widget.findItems(preset_name, Qt.MatchExactly)
            if items:
                items[0].setSelected(True)

        self.custom_folders_edit.setText(settings_dict.get("custom_folders") or "")
        self.custom_extensions_edit.setText(settings_dict.get("custom_extensions") or "")
        self.custom_patterns_edit.setText(settings_dict.get("custom_patterns") or "")
        self.dynamic_exclude_edit.setText(settings_dict.get("dynamic_patterns") or "")
        self.custom_inclusions_edit.setText(settings_dict.get("custom_inclusions", DEFAULT_SETTINGS["custom_inclusions"])) # New field

        self.max_size_spinbox.setValue(
            float(settings_dict.get("max_file_size_mb", DEFAULT_SETTINGS["max_file_size_mb"]))
        )
        self.save_output_checkbox.setChecked(
            bool(settings_dict.get("save_output_checked", DEFAULT_SETTINGS["save_output_checked"]))
        )

        self.custom_prompt_edit.setPlainText(
            settings_dict.get("custom_prompt", DEFAULT_SETTINGS["custom_prompt"])
        )

        loaded_user_templates = settings_dict.get("prompt_templates", None)
        if loaded_user_templates is not None and isinstance(loaded_user_templates, list):
            if all(isinstance(t, dict) and 'name' in t and 'content' in t for t in loaded_user_templates):
                current_default_names = {t['name'] for t in DEFAULT_AI_PROMPT_TEMPLATES}
                combined_templates = list(DEFAULT_AI_PROMPT_TEMPLATES)
                for t in loaded_user_templates:
                    if t['name'] not in current_default_names:
                        combined_templates.append(t)
                self.prompt_templates = combined_templates
                print(f"INFO: Loaded {len(loaded_user_templates)} user templates from environment.")
            else:
                self.show_warning("Loaded prompt templates have an invalid format. Ignoring them.")
        elif is_legacy_v1 or is_legacy_v2_2:
             if not any(t in DEFAULT_AI_PROMPT_TEMPLATES for t in self.prompt_templates):
                  self.prompt_templates.extend(list(DEFAULT_AI_PROMPT_TEMPLATES))

        loaded_docs = settings_dict.get("loaded_doc_paths", DEFAULT_SETTINGS["loaded_doc_paths"])
        if isinstance(loaded_docs, list) and all(isinstance(p, str) for p in loaded_docs):
             self.loaded_doc_paths = loaded_docs
        else:
             self.loaded_doc_paths = []
             if "loaded_doc_paths" in settings_dict: # Warn if it existed but was invalid
                 self.show_warning("Loaded documentation paths have an invalid format. Clearing list.")


        self.current_theme = settings_dict.get("selected_theme", DEFAULT_SETTINGS["selected_theme"])

        self._update_template_combo()
        self._update_doc_list_widget()

    def load_persistent_settings(self):
        recent_data = self.settings.value("recentEnvironments", [])
        valid_recent = []
        if isinstance(recent_data, list):
            for item in recent_data:
                if isinstance(item, dict) and 'name' in item and 'path' in item:
                    if Path(item['path']).exists():
                        valid_recent.append(item)
                    else:
                        print(f"INFO: Pruning non-existent recent environment: {item['path']}")
            self.recent_environments = valid_recent
            if len(self.recent_environments) != len(recent_data):
                self.settings.setValue("recentEnvironments", self.recent_environments)
        else:
            self.recent_environments = []

        self.current_theme = self.settings.value("selectedTheme", DEFAULT_SETTINGS["selected_theme"])

        templates_data = self.settings.value("promptTemplates", [])
        user_templates = []
        if isinstance(templates_data, list) and all(isinstance(t, dict) and 'name' in t and 'content' in t for t in templates_data):
            user_templates = templates_data
            print(f"INFO: Loaded {len(user_templates)} user-saved prompt templates from persistent settings.")
        else:
            if templates_data:
                print("WARNING: Stored prompt templates invalid format. Resetting.")
                self.settings.remove("promptTemplates")

        final_templates = list(DEFAULT_AI_PROMPT_TEMPLATES)
        user_template_names = {t['name'] for t in user_templates}
        final_templates = [t for t in final_templates if t['name'] not in user_template_names]
        final_templates.extend(user_templates)
        self.prompt_templates = final_templates

        doc_paths_data = self.settings.value("loadedDocPaths", [])
        valid_doc_paths = []
        if isinstance(doc_paths_data, list) and all(isinstance(p, str) for p in doc_paths_data):
             for path_str in doc_paths_data:
                 if Path(path_str).exists() and Path(path_str).is_file():
                     valid_doc_paths.append(path_str)
                 else:
                      print(f"INFO: Pruning non-existent documentation path: {path_str}")
             self.loaded_doc_paths = valid_doc_paths
             if len(self.loaded_doc_paths) != len(doc_paths_data):
                 self.settings.setValue("loadedDocPaths", self.loaded_doc_paths)
        else:
             self.loaded_doc_paths = []
             if doc_paths_data:
                 print("WARNING: Stored documentation paths invalid format. Resetting.")
                 self.settings.remove("loadedDocPaths")


    def load_initial_environment(self):
        loaded = False
        if self.recent_environments:
            most_recent_path_str = self.recent_environments[0].get('path')
            if most_recent_path_str:
                most_recent_path = Path(most_recent_path_str)
                if most_recent_path.exists():
                    if self._load_environment_from_path(most_recent_path):
                        loaded = True
                    else:
                        self.show_warning(f"Failed loading recent env '{most_recent_path.name}'. Removing from list.")
                        self._remove_recent_environment(str(most_recent_path))
                else:
                    self.show_warning(f"Recent env file not found: '{most_recent_path.name}'. Removing from list.")
                    self._remove_recent_environment(str(most_recent_path))

        if not loaded:
            settings_to_apply = DEFAULT_SETTINGS.copy()
            settings_to_apply['prompt_templates'] = self.prompt_templates # Keep persistent templates
            settings_to_apply['loaded_doc_paths'] = self.loaded_doc_paths # Keep persistent docs
            self.apply_settings_to_ui(settings_to_apply)
            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            self.show_status("Loaded default settings. No recent environment loaded.")

    def _update_window_title(self):
        base_title = "Folder Structure to Text v2.3"
        if self.current_environment_file:
            self.setWindowTitle(f"{base_title} - [{self.current_environment_file.name}]")
        else:
            folder_name = Path(self.folder_path_edit.text()).name if self.folder_path_edit.text() else ""
            if folder_name:
                self.setWindowTitle(f"{base_title} - [Unsaved: {folder_name}]")
            else:
                self.setWindowTitle(base_title)

    def _handle_folder_change_for_title(self):
        if not self.current_environment_file:
            self._update_window_title()

    def _load_environment_from_path(self, file_path: Path) -> bool:
        self.show_status(f"Loading environment: {file_path.name}...")
        try:
            with file_path.open('r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            if not isinstance(loaded_settings, dict):
                raise TypeError("Invalid JSON format in environment file.")

            # Combine persistent/default templates+docs with loaded settings
            # Apply loaded settings first, potentially overwriting templates/docs temporarily
            self.apply_settings_to_ui(loaded_settings)

            # Now, ensure persistent data (if any) overrides loaded if necessary, or defaults fill gaps
            # This logic is tricky. Let's prioritize loaded environment's templates/docs.
            # apply_settings_to_ui already handles merging/loading templates.
            # We just need to ensure the doc paths are validated after load.
            valid_loaded_docs = []
            for path_str in self.loaded_doc_paths:
                 if Path(path_str).exists() and Path(path_str).is_file():
                      valid_loaded_docs.append(path_str)
                 else:
                      self.show_warning(f"Documentation file from environment not found: {path_str}")
            self.loaded_doc_paths = valid_loaded_docs
            self._update_doc_list_widget() # Refresh UI list

            self.apply_theme(self.current_theme)

            self.current_environment_file = file_path
            self.settings.setValue("lastEnvDir", str(file_path.parent))
            self._add_recent_environment(file_path.name, str(file_path))
            self._update_window_title()
            self.save_env_action.setEnabled(True)
            self.show_status(f"Environment loaded successfully: {file_path.name}")
            return True

        except (IOError, json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
            self.show_error(f"Failed loading environment '{file_path.name}': {e}")
            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            return False
        except Exception as e:
            self.show_error(f"Unexpected error loading env '{file_path.name}': {e}\n{traceback.format_exc()}")
            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            return False

    def load_environment_dialog(self):
        start_dir = self.settings.value("lastEnvDir", str(Path.home()))
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Load Environment", start_dir, "JSON Files (*.json);;All Files (*)"
        )
        if fileName:
            self._load_environment_from_path(Path(fileName))

    def save_current_environment(self):
        if not self.current_environment_file:
            self.save_environment_as()
            return

        if not self.current_environment_file.parent.exists():
            self.show_error(f"Directory '{self.current_environment_file.parent}' no longer exists. Cannot save.")
            return

        current_settings = self.get_settings_from_ui()
        try:
            with self.current_environment_file.open('w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=4, ensure_ascii=False)
            self.show_status(f"Environment saved: {self.current_environment_file.name}")
            self._update_window_title()
        except Exception as e:
            self.show_error(f"Failed saving environment: {e}")

    def save_environment_as(self):
        current_settings = self.get_settings_from_ui()
        start_dir = self.settings.value("lastEnvDir", str(Path.home()))

        folder_name = Path(self.folder_path_edit.text()).name
        sanitized_folder_name = sanitize_filename(folder_name)
        default_name = f"{sanitized_folder_name}_fse_env.json" if sanitized_folder_name else "folder_structure_env.json"

        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Environment As...", str(Path(start_dir) / default_name),
            "JSON Files (*.json);;All Files (*)"
        )

        if fileName:
            file_path = Path(fileName)
            if file_path.suffix.lower() != '.json':
                file_path = file_path.with_suffix('.json')

            try:
                with file_path.open('w', encoding='utf-8') as f:
                    json.dump(current_settings, f, indent=4, ensure_ascii=False)

                self.current_environment_file = file_path
                self.settings.setValue("lastEnvDir", str(file_path.parent))
                self._add_recent_environment(file_path.name, str(file_path))
                self._update_window_title()
                self.save_env_action.setEnabled(True)
                self.show_status(f"Environment saved as: {file_path.name}")
            except Exception as e:
                self.show_error(f"Failed saving environment as: {e}")

    def _add_recent_environment(self, name: str, path_str: str):
        self.recent_environments = [env for env in self.recent_environments if env['path'] != path_str]
        self.recent_environments.insert(0, {'name': name, 'path': path_str})
        self.recent_environments = self.recent_environments[:MAX_RECENT_ENVS]
        self.settings.setValue("recentEnvironments", self.recent_environments)
        self._update_recent_menu()

    def _remove_recent_environment(self, path_str: str):
        initial_len = len(self.recent_environments)
        self.recent_environments = [env for env in self.recent_environments if env['path'] != path_str]
        if len(self.recent_environments) < initial_len:
            self.settings.setValue("recentEnvironments", self.recent_environments)
            self._update_recent_menu()

    def _update_recent_menu(self):
        self.recent_env_menu.clear()
        actions = []
        if self.recent_environments:
            for i, env in enumerate(self.recent_environments):
                action = QAction(
                    f"&{i+1} {env['name']}", self,
                    triggered=functools.partial(self.load_specific_recent_environment, env['path'])
                )
                action.setStatusTip(f"Load {env['path']}")
                action.setToolTip(env['path'])
                actions.append(action)
            self.recent_env_menu.setEnabled(True)
        else:
            no_recent_action = QAction("No Recent Environments", self)
            no_recent_action.setEnabled(False)
            actions.append(no_recent_action)
            self.recent_env_menu.setEnabled(False)

        self.recent_env_menu.addActions(actions)

    def load_specific_recent_environment(self, path_str: str):
        file_path = Path(path_str)
        if not file_path.exists():
            self.show_warning(f"Recent environment file not found: {path_str}. Removing from list.")
            self._remove_recent_environment(path_str)
            return
        self._load_environment_from_path(file_path)

    def manage_recent_environments(self):
        dialog = ManageRecentDialog(list(self.recent_environments), self)
        if dialog.exec_() == QDialog.Accepted:
            updated_list = dialog.get_updated_list()
            if updated_list != self.recent_environments:
                self.recent_environments = updated_list
                self.settings.setValue("recentEnvironments", self.recent_environments)
                self._update_recent_menu()
                self.show_status("Recent environments list updated.")

    def _update_template_combo(self):
        current_selection_text = self.template_combo.currentText()
        self.template_combo.clear()
        self.template_combo.addItem("-- Select Template --", userData=None)

        sorted_templates = sorted(self.prompt_templates, key=lambda t: t.get('name', '').lower())

        for i, template in enumerate(sorted_templates):
            self.template_combo.addItem(template.get('name', f'Unnamed {i+1}'), userData=template)

        index = self.template_combo.findText(current_selection_text)
        if index != -1:
            self.template_combo.setCurrentIndex(index)
        else:
            self.template_combo.setCurrentIndex(0)

    def load_selected_template(self):
        index = self.template_combo.currentIndex()
        if index > 0:
            template_data = self.template_combo.itemData(index)
            if template_data and isinstance(template_data, dict):
                content = template_data.get('content', '')
                processed_content = apply_placeholders(content, self)
                self.custom_prompt_edit.setPlainText(processed_content)
                self.show_status(f"Loaded template '{template_data.get('name', 'N/A')}' and applied placeholders.")
            else:
                self.show_warning("Selected template data is invalid.")
        elif self.template_combo.count() > 1 :
            self.show_status("No template selected to load.")

    def save_template_as(self):
        current_content = self.custom_prompt_edit.toPlainText().strip()
        if not current_content:
            QMessageBox.warning(self, "Cannot Save Empty", "Prompt text area is empty.")
            return

        dialog = EditTemplateDialog(
            template_content=current_content,
            existing_names=self.get_template_names(),
            parent=self
        )
        dialog.setWindowTitle("Save Current Prompt as Template")

        if dialog.exec_() == QDialog.Accepted:
            new_template = {
                "name": dialog.get_template_name(),
                "content": dialog.get_template_content()
            }

            is_default_duplicate = any(
                t['name'] == new_template['name'] and t['content'] == new_template['content']
                for t in DEFAULT_AI_PROMPT_TEMPLATES
            )

            if not is_default_duplicate:
                self.prompt_templates.append(new_template)
                self.save_prompt_templates()
                self._update_template_combo()
                self.template_combo.setCurrentText(new_template["name"])
                self.show_status(f"Prompt saved as template '{new_template['name']}'.")
            else:
                self.show_warning(f"Template '{new_template['name']}' is identical to a default template and was not saved.")
                self.template_combo.setCurrentText(new_template["name"])

    def manage_prompt_templates(self):
        dialog = PromptTemplateManagerDialog(list(self.prompt_templates), parent=self)
        dialog.exec_()

        updated_templates = dialog.get_updated_templates()
        updated_user_templates = [t for t in updated_templates if t not in DEFAULT_AI_PROMPT_TEMPLATES]
        current_user_templates = [t for t in self.prompt_templates if t not in DEFAULT_AI_PROMPT_TEMPLATES]

        if updated_user_templates != current_user_templates:
            self.prompt_templates = list(DEFAULT_AI_PROMPT_TEMPLATES)
            default_names = {t['name'] for t in DEFAULT_AI_PROMPT_TEMPLATES}
            for t in updated_user_templates:
                if t['name'] not in default_names:
                    self.prompt_templates.append(t)

            self.save_prompt_templates()
            self._update_template_combo()
            self.show_status("Template management closed. Changes saved.")
        else:
            self.show_status("Template management closed. No changes made to user templates.")

    def get_template_names(self) -> List[str]:
        return [t.get('name', '') for t in self.prompt_templates]

    def save_prompt_templates(self):
        user_templates = [
            t for t in self.prompt_templates if t not in DEFAULT_AI_PROMPT_TEMPLATES
        ]
        self.settings.setValue("promptTemplates", user_templates)

    def add_documentation(self):
        start_dir = self.settings.value("lastDocDir", str(Path.home()))
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, "Add Markdown Documentation Files", start_dir,
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)"
        )
        added_count = 0
        if fileNames:
            current_dir = ""
            for fileName in fileNames:
                path = Path(fileName)
                if path.is_file() and path.suffix.lower() in ['.md', '.markdown', '.txt']:
                    path_str = str(path.resolve())
                    if path_str not in self.loaded_doc_paths:
                        self.loaded_doc_paths.append(path_str)
                        added_count += 1
                        current_dir = str(path.parent) # Remember last used directory
                    else:
                        self.show_warning(f"Documentation file already added: {path.name}")
                else:
                     self.show_warning(f"Skipping invalid file: {fileName}")
            if current_dir:
                self.settings.setValue("lastDocDir", current_dir)
            if added_count > 0:
                self._update_doc_list_widget()
                self.show_status(f"Added {added_count} documentation file(s).")

    def remove_documentation(self):
        selected_items = self.doc_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more documentation files to remove.")
            return

        paths_to_remove = {item.data(Qt.UserRole) for item in selected_items}
        initial_len = len(self.loaded_doc_paths)
        self.loaded_doc_paths = [p for p in self.loaded_doc_paths if p not in paths_to_remove]

        if len(self.loaded_doc_paths) < initial_len:
            self._update_doc_list_widget()
            self.show_status(f"Removed {initial_len - len(self.loaded_doc_paths)} documentation file(s).")

    def clear_documentation(self):
        if not self.loaded_doc_paths:
            self.show_status("Documentation list is already empty.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to remove all loaded documentation files?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.loaded_doc_paths.clear()
            self._update_doc_list_widget()
            self.show_status("Cleared all documentation files.")

    def _update_doc_list_widget(self):
        self.doc_list_widget.clear()
        for path_str in self.loaded_doc_paths:
            path = Path(path_str)
            item = QListWidgetItem(f"{path.name} ({path.parent.name})")
            item.setData(Qt.UserRole, path_str)
            item.setToolTip(path_str)
            self.doc_list_widget.addItem(item)

    def _get_combined_documentation_content(self) -> str:
        combined_docs = []
        for path_str in self.loaded_doc_paths:
             path = Path(path_str)
             try:
                 with path.open('r', encoding='utf-8') as f:
                     content = f.read()
                 combined_docs.append(f"---\n**Documentation: `{path.name}`**\n\n{content.strip()}\n---")
             except Exception as e:
                  self.show_warning(f"Error reading documentation file '{path.name}': {e}")
                  combined_docs.append(f"---\n**Documentation: `{path.name}` [Error Reading File]**\n---")
        return "\n\n".join(combined_docs)

    def generate_structure(self):
        settings = self.get_settings_from_ui()
        folder_path = settings["folder_path"]

        if not folder_path or not Path(folder_path).is_dir():
            self.show_warning("Please select a valid target folder.")
            self.browse_folder()
            return

        self.settings.setValue("lastFolderPath", folder_path)
        if not self.current_environment_file:
            self._update_window_title()

        self.generate_button.setEnabled(False)
        self.copy_raw_button.setEnabled(False)
        self.raw_output_textedit.setPlainText("Generating, please wait...")
        self.rendered_output_view.setPlainText("Generating...")
        self.main_tabs.setCurrentIndex(1)
        self.output_tabs.setCurrentIndex(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        final_custom_prompt = apply_placeholders(settings["custom_prompt"], self)
        if final_custom_prompt != settings["custom_prompt"]:
            self.show_status("Applied placeholders to custom prompt for generation.")

        documentation_content = self._get_combined_documentation_content()
        if documentation_content:
            self.show_status(f"Including content from {len(self.loaded_doc_paths)} documentation file(s).")

        try:
            generated_text = self.processor.generate_structure_text(
                folder_path,
                settings["selected_presets"],
                settings["custom_folders"],
                settings["custom_extensions"],
                settings["custom_patterns"],
                settings["dynamic_patterns"],
                settings["custom_inclusions"],
                settings["max_file_size_mb"],
                final_custom_prompt,
                documentation_content
            )

            self.raw_output_textedit.setPlainText(generated_text)
            self.update_rendered_output()

            is_error = generated_text.startswith("```error")
            self.copy_raw_button.setEnabled(not is_error)

            if settings["save_output_checked"] and not is_error:
                self.save_output_markdown_to_file(generated_text, Path(folder_path).name)

        except Exception as e:
            self.show_error(f"Critical error during generation: {e}\n{traceback.format_exc()}")
            error_msg = f"```error\nCritical error during generation: {e}\n```"
            self.raw_output_textedit.setPlainText(error_msg)
            self.rendered_output_view.setPlainText(error_msg)
            self.copy_raw_button.setEnabled(False)

        finally:
            QApplication.restoreOverrideCursor()
            self.generate_button.setEnabled(True)
            self.raw_output_textedit.moveCursor(QTextCursor.Start)
            self.raw_output_textedit.ensureCursorVisible()

    def save_output_markdown_to_file(self, text_content: str, folder_name: str):
        default_dir = str(Path(self.folder_path_edit.text()).parent)
        save_dir = self.settings.value("lastMarkdownSaveDir", default_dir)

        if not Path(save_dir).exists():
            save_dir = str(Path.home())
            self.settings.remove("lastMarkdownSaveDir")

        sanitized_folder_name = sanitize_filename(folder_name)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        suggested_name = f"fse_{sanitized_folder_name}_{timestamp}.md"

        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown Output", str(Path(save_dir) / suggested_name),
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)"
        )

        if fileName:
            try:
                file_path = Path(fileName)
                file_path.write_text(text_content, encoding='utf-8')
                self.settings.setValue("lastMarkdownSaveDir", str(file_path.parent))
                self.show_status(f"Markdown output saved to: {file_path.name}")
            except Exception as e:
                self.show_error(f"Failed to save Markdown file: {e}")

    def closeEvent(self, event):
        self.settings.setValue("selectedTheme", self.current_theme)
        self.save_prompt_templates()
        self.settings.setValue("recentEnvironments", self.recent_environments)
        # Save validated doc paths
        valid_doc_paths = [p for p in self.loaded_doc_paths if Path(p).exists()]
        self.settings.setValue("loadedDocPaths", valid_doc_paths)


        if self.folder_path_edit.text() and Path(self.folder_path_edit.text()).exists():
            self.settings.setValue("lastBrowseDir", self.folder_path_edit.text())
        if self.current_environment_file:
            self.settings.setValue("lastEnvDir", str(self.current_environment_file.parent))
        # Persist last doc dir only if it exists
        last_doc_dir = self.settings.value("lastDocDir")
        if last_doc_dir and not Path(last_doc_dir).exists():
            self.settings.remove("lastDocDir")
        # Persist last markdown save dir similarly
        last_md_dir = self.settings.value("lastMarkdownSaveDir")
        if last_md_dir and not Path(last_md_dir).exists():
             self.settings.remove("lastMarkdownSaveDir")


        self.settings.sync()
        self.show_status("Settings saved. Exiting...")
        event.accept()


if __name__ == '__main__':
    if not ASSETS_DIR.exists():
        try:
            ASSETS_DIR.mkdir()
            print(f"Created missing assets directory: {ASSETS_DIR}")
        except OSError as e:
            print(f"Warning: Could not create assets directory: {e}")

    app = QApplication(sys.argv)
    try:
        main_window = FolderStructureApp()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("\n--- Unhandled Exception ---")
        print(f"Error: {e}")
        print(traceback.format_exc())
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Application Crash")
            msgBox.setText(f"An unexpected error occurred:\n\n{e}\n\nPlease see console output for details.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
        except:
            pass
        sys.exit(1)