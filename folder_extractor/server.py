# -*- coding: utf-8 -*-
# Project: folder_extractor
# Author: ParisNeo with gemini 2.5 (and significant user modifications)
# Description: A PyQt5 application that takes a folder path and generates a Markdown-formatted text representation,
#              including specific file/folder inclusions via an interactive tree, documentation integration,
#              and a custom stylesheet-based UI with theming.
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

# Ensure essential packages are present (user should handle this if pipmaster is removed)
try:
    import markdown
except ImportError:
    print("Error: 'markdown' package not found. Please install it: pip install markdown")
    sys.exit(1)

try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QListWidget, QDialogButtonBox, QLineEdit, QLabel, QFileDialog,
        QTextEdit, QComboBox, QGroupBox, QDialog, QListWidgetItem,
        QFormLayout, QDoubleSpinBox, QCheckBox, QMessageBox, QSplitter,
        QAction, QStatusBar, QMainWindow, QMenu, QTabWidget,
        QAbstractItemView, QInputDialog, QToolBox, QScrollArea,
        QTreeView, QHeaderView
    )
    from PyQt5.QtCore import Qt, QSettings, QSize, QCoreApplication, QModelIndex
    from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QTextCursor, QStandardItemModel, QStandardItem, QColor
except ImportError as e:
    print(f"Error: Missing required PyQt5 components. ({e})")
    print("Please ensure PyQt5 is installed correctly (e.g., pip install PyQt5).")
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
FOLDER_ICON_STR, FILE_ICON_STR = "📁", "📄"
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
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
THEMES_DIR = SCRIPT_DIR / "themes"
THEMES_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_THEME_FILE = "default_light.qss"


PATH_ROLE = Qt.UserRole + 1
IS_TEXT_FILE_ROLE = Qt.UserRole + 2
IS_DIR_ROLE = Qt.UserRole + 3

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
    "version": "2.6", # Updated version for theming
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
    "current_theme_file": DEFAULT_THEME_FILE, # New setting for theme file name
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
    asset_path_svg = ASSETS_DIR / f"{name}.svg"
    if asset_path_svg.exists():
        icon = QIcon(str(asset_path_svg))
        if not icon.isNull():
            return icon
    asset_path_png = ASSETS_DIR / f"{name}.png"
    if asset_path_png.exists():
        icon = QIcon(str(asset_path_png))
        if not icon.isNull():
            return icon

    if fallback_theme_name:
        icon = QIcon.fromTheme(fallback_theme_name)
        if not icon.isNull():
            return icon
    
    theme_name_guess = name.replace('_', '-') # e.g. folder-open
    if '-' not in theme_name_guess and fallback_theme_name is None: # Try common prefixes for actions
        prefixes = ["action-", "document-", "edit-", "go-", "list-", "system-", "view-", "preferences-", "application-"]
        for prefix in prefixes:
            icon = QIcon.fromTheme(prefix + theme_name_guess)
            if not icon.isNull(): return icon

    icon = QIcon.fromTheme(theme_name_guess) # Try direct guess
    if not icon.isNull():
        return icon
        
    # print(f"Warning: Icon '{name}' not found in assets or theme. Using empty icon.")
    return QIcon()

class ThemeManager:
    def __init__(self, app: QApplication, settings: QSettings, themes_dir: Path, assets_dir: Path, default_theme_file: str):
        self.app = app
        self.settings = settings
        self.themes_dir = themes_dir
        self.assets_dir = assets_dir
        self.default_theme_file = default_theme_file
        self.available_themes: Dict[str, Path] = {} # Display Name -> Path object
        self.current_theme_file_name: str = default_theme_file
        self.theme_actions: List[QAction] = []

        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self._scan_themes()

    def _scan_themes(self):
        self.available_themes.clear()
        for qss_file in self.themes_dir.glob("*.qss"):
            theme_display_name = qss_file.stem.replace("_", " ").replace("-", " ").title()
            self.available_themes[theme_display_name] = qss_file
        
        if not self.available_themes:
            print(f"Warning: No themes found in {self.themes_dir}. Application might have basic styling.")
            # Optionally create a default theme file here if it's missing and critical
            default_path = self.themes_dir / self.default_theme_file
            if not default_path.exists():
                 try:
                     # A very minimal QSS as an ultimate fallback
                     default_qss_content = "QWidget { background-color: #ececec; color: black; } QPushButton { background-color: lightgray; }"
                     default_path.write_text(default_qss_content)
                     print(f"Created minimal default theme: {default_path}")
                     self.available_themes[self.default_theme_file.replace('.qss','').title()] = default_path
                 except Exception as e:
                     print(f"Error creating minimal default theme: {e}")


    def apply_theme_from_file_name(self, theme_file_name: Optional[str]):
        if not theme_file_name:
            theme_file_name = self.default_theme_file
        
        chosen_path: Optional[Path] = None
        for display_name, path_obj in self.available_themes.items():
            if path_obj.name == theme_file_name:
                chosen_path = path_obj
                break
        
        if not chosen_path and (self.themes_dir / theme_file_name).exists(): # Fallback if name is direct filename
            chosen_path = self.themes_dir / theme_file_name
        elif not chosen_path: # If still not found, try default
            print(f"Warning: Theme file '{theme_file_name}' not found in available themes. Trying default '{self.default_theme_file}'.")
            theme_file_name = self.default_theme_file
            chosen_path = self.themes_dir / self.default_theme_file

        if chosen_path and chosen_path.exists():
            try:
                qss_content = chosen_path.read_text(encoding="utf-8")
                # Replace placeholder for assets directory
                qss_content = qss_content.replace("{ASSETS_DIR}", self.assets_dir.as_posix())
                
                self.app.setStyleSheet(qss_content)
                self.current_theme_file_name = chosen_path.name # Store the actual file name
                self.settings.setValue("currentThemeFileName", self.current_theme_file_name)
                self._update_theme_action_checks()
                # print(f"Applied theme: {chosen_path.name}")
            except Exception as e:
                print(f"Error applying theme '{chosen_path.name}': {e}")
                # Fallback if error during application
                if chosen_path.name != self.default_theme_file:
                    self.apply_theme_from_file_name(self.default_theme_file)
        else:
            print(f"Error: Ultimate fallback theme file '{self.default_theme_file}' not found at {self.themes_dir}. Applying basic Qt styling.")
            self.app.setStyleSheet("") # Clear stylesheet to revert to OS default


    def _update_theme_action_checks(self):
        for action in self.theme_actions:
            action_theme_file_name = action.data() # Store filename in action's data
            if isinstance(action_theme_file_name, str):
                action.setChecked(action_theme_file_name == self.current_theme_file_name)

    def create_theme_menu_actions(self, parent_menu: QMenu):
        self.theme_actions.clear()
        parent_menu.clear()

        sorted_theme_names = sorted(self.available_themes.keys())

        for theme_display_name in sorted_theme_names:
            theme_path = self.available_themes[theme_display_name]
            action = QAction(theme_display_name, self.app.activeWindow(), checkable=True)
            action.setData(theme_path.name) # Store the file name (e.g., "default_light.qss")
            action.triggered.connect(functools.partial(self.apply_theme_from_file_name, theme_path.name))
            self.theme_actions.append(action)
            parent_menu.addAction(action)
        
        self._update_theme_action_checks()

    def get_current_theme_file_name(self) -> str:
        return self.settings.value("currentThemeFileName", self.default_theme_file)


class FolderProcessor:
    # ... (FolderProcessor class remains largely the same as in the previous version) ...
    # Minor adjustment: Ensure _root_folder is initialized if not passed in setup_exclusions
    def __init__(self, status_callback=print, warning_callback=print, error_callback=print):
        self.status_callback = status_callback
        self.warning_callback = warning_callback
        self.error_callback = error_callback
        self._active_excluded_folders: Set[str] = set()
        self._active_excluded_extensions: Set[str] = set()
        self._active_excluded_patterns: List[str] = []
        self._active_include_patterns: List[str] = []
        self._max_file_size_bytes: int = 0
        self._root_folder: Path = Path(".") # Initialize to a valid Path

    def setup_exclusions_and_limits(
        self,
        selected_preset_names: List[str],
        custom_folders_str: str,
        custom_exts_str: str,
        custom_patterns_str: str,
        dynamic_patterns_list: List[str],
        custom_inclusions_str: str,
        max_size_mb: float,
        root_folder_for_context: Optional[Path] = None 
    ):
        if root_folder_for_context and root_folder_for_context.is_dir():
            self._root_folder = root_folder_for_context.resolve()
        elif not (hasattr(self, '_root_folder') and self._root_folder.is_dir()):
            # If no context root given and self._root_folder is not a valid dir,
            # set to current working directory as a fallback.
            # This might happen if called before folder_path_edit is set.
            self._root_folder = Path(".").resolve()
            # self.warning_callback(f"Root folder for exclusion context not set or invalid, using CWD: {self._root_folder}")

        
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

    def _is_excluded(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        context_root = current_root_override if current_root_override and current_root_override.is_dir() else self._root_folder
        if not context_root.is_dir(): # If no valid root, can't determine relative path based exclusions
            if item.is_dir() and item.name.lower() in self._active_excluded_folders: return True
            if item.is_file() and item.suffix.lower() in self._active_excluded_extensions: return True
            for pattern in self._active_excluded_patterns:
                if pattern.endswith('/') and item.is_dir() and fnmatch.fnmatchcase(item.name, pattern[:-1]): return True
                if not pattern.endswith('/') and fnmatch.fnmatchcase(item.name, pattern): return True 
            return False

        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower() if item.is_file() else ""

        if item.is_dir() and item_name_lower in self._active_excluded_folders:
            return True
        if item.is_file() and item_suffix_lower in self._active_excluded_extensions:
            return True

        try:
            # Ensure item is actually under context_root before trying relative_to
            if item.is_relative_to(context_root):
                 item_relative_path_str = str(item.relative_to(context_root).as_posix())
            else: # Item is not under context_root, only match by name
                item_relative_path_str = item.name
        except AttributeError: # For Python < 3.9 (no is_relative_to)
            try:
                item_relative_path_str = str(item.relative_to(context_root).as_posix())
            except ValueError:
                item_relative_path_str = item.name


        for pattern in self._active_excluded_patterns:
            match = False
            if pattern.endswith('/'):
                if item.is_dir() and fnmatch.fnmatchcase(item.name, pattern[:-1]): 
                    match = True
                elif item_relative_path_str.startswith(pattern[:-1] + "/"):
                     match = True
            elif fnmatch.fnmatchcase(item.name, pattern): 
                match = True
            elif "/" in pattern and fnmatch.fnmatchcase(item_relative_path_str, pattern): 
                match = True
            
            if match:
                return True
        return False

    def _is_included_by_filter(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        context_root = current_root_override if current_root_override and current_root_override.is_dir() else self._root_folder
        if not context_root.is_dir(): 
            return not self._active_include_patterns

        if not self._active_include_patterns: 
            return True

        try:
            if item.is_relative_to(context_root):
                item_rel_path_str = item.relative_to(context_root).as_posix()
            else:
                item_rel_path_str = item.name 
        except AttributeError: # Python < 3.9
            try:
                item_rel_path_str = item.relative_to(context_root).as_posix()
            except ValueError:
                item_rel_path_str = item.name

        for pattern in self._active_include_patterns:
            if fnmatch.fnmatchcase(item_rel_path_str, pattern):
                return True
            
            if "/" in item_rel_path_str: 
                try:
                    current_path_obj = Path(item_rel_path_str)
                    for parent_part_path in current_path_obj.parents:
                        if str(parent_part_path) == ".": continue 
                        if fnmatch.fnmatchcase(str(parent_part_path), pattern):
                            return True
                        if pattern.endswith("/") and fnmatch.fnmatchcase(str(parent_part_path), pattern[:-1]):
                            return True
                except Exception: 
                    pass
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

    def _build_filtered_file_list_and_tree(
        self,
        current_folder: Path,
        prefix: str = ""
    ) -> Tuple[List[str], List[Path]]:
        tree_lines: List[str] = []
        found_files: List[Path] = []

        try:
            items_in_dir = sorted(
                [item for item in current_folder.iterdir()],
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except (PermissionError, OSError) as e:
            msg = f"[Error: Permission denied accessing {current_folder.name}]" if isinstance(e, PermissionError) else f"[Error: OS error accessing {current_folder.name}]"
            tree_lines.append(f"{prefix}{msg}")
            self.warning_callback(f"Error listing directory {current_folder}: {e}")
            return tree_lines, found_files

        items_to_process = []
        for item in items_in_dir:
            if self._is_excluded(item, self._root_folder):
                continue
            if self._is_included_by_filter(item, self._root_folder):
                items_to_process.append(item)

        num_items = len(items_to_process)
        for i, item in enumerate(items_to_process):
            is_last = (i == num_items - 1)
            connector = TREE_LAST if is_last else TREE_BRANCH
            line_prefix = prefix + connector
            child_prefix = prefix + (TREE_SPACE if is_last else TREE_VLINE)

            if item.is_dir():
                tree_lines.append(f"{line_prefix}{FOLDER_ICON_STR} {item.name}/")
                sub_tree_lines, sub_found_files = self._build_filtered_file_list_and_tree(item, child_prefix)
                tree_lines.extend(sub_tree_lines)
                found_files.extend(sub_found_files)
            elif item.is_file():
                if self._is_text_file(item):
                    tree_lines.append(f"{line_prefix}{FILE_ICON_STR} {item.name}")
                    found_files.append(item)
        return tree_lines, found_files

    def _generate_tree_markdown_from_paths(self, root_path: Path, selected_paths: List[Path]) -> List[str]:
        if not selected_paths:
            return ["*No items selected in the file tree.*"]

        hierarchy: Dict[str, Any] = {}
        all_nodes_to_represent = set(selected_paths)
        for p in selected_paths:
            try:
                # Ensure p is under root_path for relative_to to work
                if p.is_relative_to(root_path):
                    relative_p = p.relative_to(root_path)
                    for i in range(len(relative_p.parts) -1): 
                        parent_path_in_root = root_path.joinpath(*relative_p.parts[:i+1])
                        all_nodes_to_represent.add(parent_path_in_root)
                else: # p might be the root_path itself or outside; treat as top-level
                     all_nodes_to_represent.add(p)
            except AttributeError: # Python < 3.9
                try:
                    relative_p = p.relative_to(root_path)
                    for i in range(len(relative_p.parts) -1):
                        parent_path_in_root = root_path.joinpath(*relative_p.parts[:i+1])
                        all_nodes_to_represent.add(parent_path_in_root)
                except ValueError:
                    all_nodes_to_represent.add(p)
            except ValueError: # p is not under root_path
                 all_nodes_to_represent.add(p)


        def get_sort_key_for_nodes(x_path: Path):
            try:
                if x_path.is_relative_to(root_path):
                    return str(x_path.relative_to(root_path))
                return str(x_path) # For paths not under root (e.g. root itself)
            except AttributeError: # Python < 3.9
                try:
                    return str(x_path.relative_to(root_path))
                except ValueError:
                    return str(x_path)
            except ValueError:
                 return str(x_path)


        sorted_nodes = sorted(list(all_nodes_to_represent), key=get_sort_key_for_nodes)


        for node_path in sorted_nodes:
            try:
                if node_path.is_relative_to(root_path):
                    relative_node_path = node_path.relative_to(root_path)
                    parts = relative_node_path.parts
                else: # Node is not under root path (e.g. root itself)
                    parts = (node_path.name,) if node_path != root_path else () # Empty parts for root itself
            except AttributeError: # Python < 3.9
                 try:
                    relative_node_path = node_path.relative_to(root_path)
                    parts = relative_node_path.parts
                 except ValueError:
                    parts = (node_path.name,) if node_path != root_path else ()
            except ValueError:
                parts = (node_path.name,) if node_path != root_path else ()


            current_level = hierarchy
            for i, part in enumerate(parts):
                is_last_part = (i == len(parts) - 1)
                current_level = current_level.setdefault(part, {})
                if is_last_part and node_path != root_path : # This is the actual node (file or dir)
                    current_level["_isfile_"] = node_path.is_file()
                    current_level["_is_selected_explicitly_"] = node_path in selected_paths
        
        if not parts and root_path in selected_paths: # Handle case where only root is selected
            hierarchy["_isfile_"] = root_path.is_file() # Should be False for root dir
            hierarchy["_is_selected_explicitly_"] = True


        def format_level(level_dict: Dict[str, Any], current_prefix: str) -> List[str]:
            lines: List[str] = []
            
            valid_items_for_level = {k:v for k,v in level_dict.items() if not k.startswith("_")}

            sorted_item_names = sorted(
                valid_items_for_level.keys(),
                key=lambda name_key: (
                    valid_items_for_level[name_key].get("_isfile_", False), 
                    name_key.lower()
                )
            )

            for i, name in enumerate(sorted_item_names):
                node_data = valid_items_for_level[name]
                is_last_item_in_level = (i == len(sorted_item_names) - 1)
                connector = TREE_LAST if is_last_item_in_level else TREE_BRANCH
                
                is_file = node_data.get("_isfile_", False)
                icon = FILE_ICON_STR if is_file else FOLDER_ICON_STR
                                
                entry_name = f"{name}{'' if is_file else '/'}"
                lines.append(f"{current_prefix}{connector}{icon} {entry_name}")

                children_dict = {k_child: v_child for k_child, v_child in node_data.items() if not k_child.startswith("_")}
                if not is_file and children_dict:
                    new_prefix = current_prefix + (TREE_SPACE if is_last_item_in_level else TREE_VLINE)
                    lines.extend(format_level(children_dict, new_prefix))
            return lines

        final_tree_lines = [f"{FOLDER_ICON_STR} {root_path.name}/"]
        final_tree_lines.extend(format_level(hierarchy, "")) # Start with empty prefix for root children

        return final_tree_lines


    def _generate_file_contents_markdown(self, root_folder: Path, file_paths: List[Path]) -> List[str]:
        content_lines = ["", "---", "", "## File Contents"]
        if not file_paths:
            content_lines.append("\n*No text files selected or included based on filters and size limits.*")
            return content_lines

        def get_sort_key(p: Path):
            try:
                # Check if p is under root_folder before calling relative_to
                if p.is_relative_to(root_folder):
                    return str(p.relative_to(root_folder)).lower()
                return p.name.lower() # Fallback for paths not under root (should be rare)
            except AttributeError: # For Python < 3.9
                try:
                    return str(p.relative_to(root_folder)).lower()
                except ValueError:
                    return p.name.lower()
            except ValueError: # p is not a subpath of root_folder
                return p.name.lower()


        file_paths.sort(key=get_sort_key)

        for file_path in file_paths:
            try:
                if file_path.is_relative_to(root_folder):
                    relative_path = file_path.relative_to(root_folder)
                else:
                    relative_path = Path(file_path.name)
                    self.warning_callback(f"Could not determine relative path for {file_path}. Using filename.")
            except AttributeError: # Python < 3.9
                try:
                    relative_path = file_path.relative_to(root_folder)
                except ValueError:
                    relative_path = Path(file_path.name)
                    self.warning_callback(f"Could not determine relative path for {file_path}. Using filename.")
            except ValueError:
                relative_path = Path(file_path.name)
                self.warning_callback(f"Could not determine relative path for {file_path}. Using filename.")


            relative_path_str = str(relative_path).replace("\\", "/")
            content_lines.append(f"\n### `{relative_path_str}`")

            file_content = self._read_file_content(file_path)

            lang = file_path.suffix[1:].lower() if file_path.suffix else "text"
            lang = "".join(c for c in lang if c.isalnum()) or "text" 
            aliases = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript',
                'jsx': 'javascript', 'md': 'markdown', 'sh': 'bash', 'yml': 'yaml',
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
        documentation_prompt: str = "",
        selected_file_paths: Optional[List[Path]] = None 
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
                custom_patterns_str, dynamic_patterns, custom_inclusions_str, max_size_mb,
                root_folder_for_context=self._root_folder 
            )
        except Exception as e:
            self.error_callback(f"Error setting up exclusions/inclusions: {e}\n{traceback.format_exc()}")
            return f"```error\nError setting up filters: {e}\n```"

        self.status_callback(f"Starting analysis for: {self._root_folder}...")
        
        tree_lines: List[str]
        found_files_for_content: List[Path]

        if selected_file_paths is not None: # Note: selected_file_paths can be an empty list
            self.status_callback(f"Using {len(selected_file_paths)} items from interactive tree selection.")
            # Filter selected_file_paths to only include files for content generation that are text files
            # and respect size limits (though size limit is checked again in _read_file_content)
            found_files_for_content = [
                p for p in selected_file_paths 
                if p.is_file() and self._is_text_file(p) and p.stat().st_size <= self._max_file_size_bytes
            ]
            tree_lines = self._generate_tree_markdown_from_paths(self._root_folder, selected_file_paths)
        else: 
            self.status_callback("Using filter-based selection (interactive tree selection not provided or empty).")
            tree_lines_from_scan, found_files_for_content_from_scan = self._build_filtered_file_list_and_tree(self._root_folder, prefix="")
            tree_lines = [f"{FOLDER_ICON_STR} {self._root_folder.name}/"] + tree_lines_from_scan
            # Filter for size limit here too for consistency, though _read_file_content is the final check
            found_files_for_content = [
                p for p in found_files_for_content_from_scan if p.stat().st_size <= self._max_file_size_bytes
            ]


        structure_output_lines = [
            f"# Folder Structure: {self._root_folder.name}",
            f"*(Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*",
            "",
            "```text"
        ]
        structure_output_lines.extend(tree_lines)
        structure_output_lines.append("```")

        content_output_lines = self._generate_file_contents_markdown(self._root_folder, found_files_for_content)

        full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)

        final_prompt_parts = []
        if documentation_prompt and documentation_prompt.strip():
            final_prompt_parts.append("## Imported Documentation\n\n" + documentation_prompt.strip())
        if custom_prompt and custom_prompt.strip():
             final_prompt_parts.append("## Custom Instructions\n\n" + custom_prompt.strip())

        if final_prompt_parts:
             full_output += "\n\n---\n\n" + "\n\n---\n\n".join(final_prompt_parts)


        self.status_callback(f"Analysis complete. Included content from {len(found_files_for_content)} text files.")
        return full_output.strip()


class ManageRecentDialog(QDialog):
    # ... (remains the same)
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

        remove_button = QPushButton(load_icon("edit-delete", "edit-delete"), " Remove Selected")
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
    # ... (remains the same)
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
    # ... (remains the same)
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
        add_button = QPushButton(load_icon("list-add", "list-add"), " Add...")
        edit_button = QPushButton(load_icon("document-edit", "document-edit"), " Edit...")
        remove_button = QPushButton(load_icon("list-remove", "list-remove"), " Remove")
        copy_button = QPushButton(load_icon("edit-copy", "edit-copy"), " Copy")
        
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
            index_in_sorted_list = item.data(Qt.UserRole) 
            
            if 0 <= index_in_sorted_list < len(self.templates):
                template_to_display = self.templates[index_in_sorted_list]
                self.preview_edit.setPlainText(template_to_display.get('content', ''))
            else:
                self.preview_edit.setPlainText("[Error: Template index out of bounds]")
                print(f"Error: Invalid index {index_in_sorted_list} for template list of size {len(self.templates)}")
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
            if self.parent_app: self.parent_app.show_status("Template added.")

    def edit_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to edit.")
            return
        
        item = selected_items[0]
        original_name = item.text()
        template_to_edit = None
        original_template_index = -1

        for idx, t in enumerate(self.templates):
            if t.get('name') == original_name:
                template_to_edit = t
                original_template_index = idx
                break
        
        if template_to_edit is None:
            QMessageBox.critical(self, "Error", "Could not find the selected template to edit.")
            return

        other_names = [t.get('name', '') for i, t in enumerate(self.templates) if i != original_template_index]

        dialog = EditTemplateDialog(
            template_name=template_to_edit.get('name', ''),
            template_content=template_to_edit.get('content', ''),
            existing_names=other_names,
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            updated_template_data = {
                "name": dialog.get_template_name(),
                "content": dialog.get_template_content()
            }
            self.templates[original_template_index] = updated_template_data 
            self.populate_list() 
            for i in range(self.list_widget.count()):
                list_item = self.list_widget.item(i)
                if list_item.text() == updated_template_data["name"]: 
                    self.list_widget.setCurrentItem(list_item)
                    break
            if self.parent_app: self.parent_app.show_status("Template updated.")


    def remove_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to remove.")
            return

        item_to_remove_text = selected_items[0].text()
        
        confirm = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove the template '{item_to_remove_text}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.templates = [t for t in self.templates if t.get('name') != item_to_remove_text]
            self.populate_list() 
            if self.parent_app: self.parent_app.show_status("Template removed.")

    def copy_template(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to copy.")
            return

        original_name = selected_items[0].text()
        original_template = None
        for t in self.templates:
            if t.get('name') == original_name:
                original_template = t
                break
        
        if not original_template:
            QMessageBox.critical(self, "Error", "Could not find the selected template to copy.")
            return

        copy_count = 1
        new_name_base = original_template.get('name', 'Unnamed')
        new_name = f"{new_name_base} (Copy)"
        existing_names = self.get_current_template_names()
        while new_name in existing_names:
            copy_count += 1
            new_name = f"{new_name_base} (Copy {copy_count})"

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
        if self.parent_app: self.parent_app.show_status(f"Template copied as '{new_name}'.")

    def get_updated_templates(self) -> List[Dict[str, str]]:
        return self.templates

class FileSelectionTab(QWidget):
    # ... (remains the same)
    def __init__(self, app_instance: 'FolderStructureApp', parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.processor = app_instance.processor 
        self._is_updating_checks = False 
        self._is_populating = False 

        self.folder_icon = load_icon("folder", "folder")
        self.file_icon = load_icon("text-x-generic", "text-x-generic") 
        self.binary_file_icon = load_icon("application-octet-stream", "application-octet-stream")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5) 

        controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton(load_icon("view-refresh", "view-refresh"), " Refresh Tree")
        self.refresh_button.clicked.connect(self.populate_tree)
        self.expand_all_button = QPushButton("Expand All")
        self.expand_all_button.clicked.connect(lambda: self.tree_view.expandAll())
        self.collapse_all_button = QPushButton("Collapse All")
        self.collapse_all_button.clicked.connect(lambda: self.tree_view.collapseAll())
        
        self.check_all_text_button = QPushButton("Check All Text")
        self.check_all_text_button.clicked.connect(self.check_all_text_files)
        self.uncheck_all_button = QPushButton("Uncheck All")
        self.uncheck_all_button.clicked.connect(self.uncheck_all_files)

        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.expand_all_button)
        controls_layout.addWidget(self.collapse_all_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.check_all_text_button)
        controls_layout.addWidget(self.uncheck_all_button)
        layout.addLayout(controls_layout)

        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['Name'])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.header().setSectionResizeMode(QHeaderView.Stretch) 
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        self.tree_view.setIndentation(15) 
        self.tree_view.setAlternatingRowColors(True)


        self.tree_model.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.tree_view)

    def populate_tree(self):
        if self._is_populating: return
        self._is_populating = True
        # Disconnect while populating to avoid massive signal emissions
        try:
            self.tree_model.itemChanged.disconnect(self.on_item_changed)
        except TypeError: # Was not connected
            pass


        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(['Name']) 
        
        root_folder_str = self.app.folder_path_edit.text()
        if not root_folder_str or not Path(root_folder_str).is_dir():
            # self.app.show_warning("Cannot populate tree: Select a valid project folder first.")
            try: # Reconnect if it was disconnected
                self.tree_model.itemChanged.connect(self.on_item_changed)
            except TypeError: pass
            self._is_populating = False
            return

        root_path = Path(root_folder_str).resolve()
        self.app.show_status(f"Populating file tree for {root_path.name}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        current_settings = self.app.get_settings_from_ui()
        self.processor.setup_exclusions_and_limits(
            current_settings["selected_presets"],
            current_settings["custom_folders"],
            current_settings["custom_extensions"],
            current_settings["custom_patterns"],
            [p.strip() for p in current_settings["dynamic_patterns"].split(',') if p.strip()],
            current_settings["custom_inclusions"],
            current_settings["max_file_size_mb"],
            root_folder_for_context=root_path 
        )

        try:
            self._populate_recursive(self.tree_model.invisibleRootItem(), root_path, root_path)
            self.app.show_status("File tree populated.")
        except Exception as e:
            self.app.show_error(f"Error populating tree: {e}")
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
            try: # Reconnect signals
                self.tree_model.itemChanged.connect(self.on_item_changed)
            except TypeError: pass # In case it was never connected or already reconnected
            self._is_populating = False


    def _populate_recursive(self, parent_item: QStandardItem, current_dir_path: Path, root_scan_path: Path):
        try:
            items_in_dir = sorted(
                list(current_dir_path.iterdir()),
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except PermissionError:
            error_item = QStandardItem(f"[Permission Denied: {current_dir_path.name}]")
            error_item.setEditable(False)
            error_item.setCheckable(False)
            error_item.setForeground(QColor("red")) # Or use style sheet for error items
            parent_item.appendRow(error_item)
            return
        except OSError as e:
            error_item = QStandardItem(f"[OS Error: {current_dir_path.name} - {e.strerror}]")
            error_item.setEditable(False)
            error_item.setCheckable(False)
            error_item.setForeground(QColor("red"))
            parent_item.appendRow(error_item)
            return


        for path_obj in items_in_dir:
            item_name = path_obj.name
            item = QStandardItem(item_name)
            item.setEditable(False)
            item.setData(path_obj, PATH_ROLE)
            item.setData(path_obj.is_dir(), IS_DIR_ROLE)

            is_excluded = self.processor._is_excluded(path_obj, root_scan_path)
            is_included_by_filter = self.processor._is_included_by_filter(path_obj, root_scan_path)
            
            should_be_checked_initially = not is_excluded and is_included_by_filter

            if path_obj.is_dir():
                item.setIcon(self.folder_icon)
                item.setCheckable(True)
                item.setCheckState(Qt.Checked if should_be_checked_initially else Qt.Unchecked)
                self._populate_recursive(item, path_obj, root_scan_path)
                if should_be_checked_initially: # After children populated, update parent based on them
                    self._update_parent_check_state_from_children(item) # Triggered by children changes during recursion

            elif path_obj.is_file():
                is_text = self.processor._is_text_file(path_obj)
                item.setData(is_text, IS_TEXT_FILE_ROLE)
                item.setIcon(self.file_icon if is_text else self.binary_file_icon)

                if is_text:
                    item.setCheckable(True)
                    item.setCheckState(Qt.Checked if should_be_checked_initially else Qt.Unchecked)
                else:
                    item.setCheckable(False) 
                    item.setEnabled(False) 
                    item.setCheckState(Qt.Unchecked) 

            parent_item.appendRow(item)
            
        # After all children of parent_item are added, if parent_item itself was a directory
        # that was initially checked, its state might need to be re-evaluated based on its children.
        # This is particularly for the case where a dir is included by filter but all its children are excluded.
        if parent_item != self.tree_model.invisibleRootItem() and parent_item.data(IS_DIR_ROLE):
            self._update_parent_check_state_from_children(parent_item)


    def on_item_changed(self, item: QStandardItem):
        if self._is_updating_checks or self._is_populating:
            return
        
        self._is_updating_checks = True
        try:
            path_obj = item.data(PATH_ROLE)
            if not path_obj: 
                self._is_updating_checks = False
                return

            is_dir = item.data(IS_DIR_ROLE)
            current_check_state = item.checkState()

            if is_dir:
                self._update_child_checks(item, current_check_state)
            
            parent = item.parent()
            if parent and parent != self.tree_model.invisibleRootItem(): # Ensure parent is valid and not root
                self._update_parent_check_state_from_children(parent)

        except Exception as e:
            print(f"Error in on_item_changed: {e}")
            traceback.print_exc()
        finally:
            self._is_updating_checks = False

    def _update_child_checks(self, parent_item: QStandardItem, state: Qt.CheckState):
        if state == Qt.PartiallyChecked: 
            return

        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row)
            if child_item and child_item.isCheckable() and child_item.isEnabled():
                # Only change if different, to prevent recursion loops if already set
                if child_item.checkState() != state:
                    child_item.setCheckState(state) 
    
    def _update_parent_check_state_from_children(self, parent_item: QStandardItem):
        if not parent_item or parent_item == self.tree_model.invisibleRootItem() or not parent_item.isCheckable():
            return

        num_children = parent_item.rowCount()
        if num_children == 0:
            # If a dir has no checkable children, its state is its own (likely Unchecked or as set by filter).
            # If it was checked by filter but has no valid children, it might become Unchecked here.
            # This depends on desired behavior. For now, if no children, its explicit state holds.
            # If it was checked initially by filter, we probably want it to stay checked (or become unchecked if no valid content)
            is_dir_included_by_filter = self.processor._is_included_by_filter(parent_item.data(PATH_ROLE), self.app.folder_path_edit.text())
            is_dir_excluded = self.processor._is_excluded(parent_item.data(PATH_ROLE), self.app.folder_path_edit.text())
            if not is_dir_excluded and is_dir_included_by_filter:
                 # if parent_item.checkState() != Qt.Checked: parent_item.setCheckState(Qt.Checked) # No, this would re-check empty dirs
                 pass # Let its current state (from filter or manual check) persist if no children
            else: # If it was excluded or not included by filter, and has no children to make it partial
                 if parent_item.checkState() != Qt.Unchecked: parent_item.setCheckState(Qt.Unchecked)
            return


        checked_children = 0
        partially_checked_children = 0
        checkable_enabled_children = 0

        for row in range(num_children):
            child_item = parent_item.child(row)
            if child_item and child_item.isCheckable() and child_item.isEnabled(): 
                checkable_enabled_children +=1
                child_state = child_item.checkState()
                if child_state == Qt.Checked:
                    checked_children += 1
                elif child_state == Qt.PartiallyChecked:
                    partially_checked_children += 1
        
        new_parent_state = Qt.Unchecked
        if checkable_enabled_children == 0 : # No effectively checkable children
            # If dir was explicitly included by filter, keep it checked? Or uncheck?
            # For now, if no checkable children, it becomes unchecked unless it was manually set.
            # This path is complex due to initial filter population.
            # Let's assume if no checkable_enabled_children, it should be unchecked.
            pass # Will default to Unchecked unless already set otherwise manually.
        elif checked_children == checkable_enabled_children : 
            new_parent_state = Qt.Checked
        elif checked_children > 0 or partially_checked_children > 0: 
            new_parent_state = Qt.PartiallyChecked
        
        if parent_item.checkState() != new_parent_state:
             parent_item.setCheckState(new_parent_state)
        
        grandparent = parent_item.parent()
        if grandparent and grandparent != self.tree_model.invisibleRootItem(): # Check grandparent too
            self._update_parent_check_state_from_children(grandparent)


    def get_selected_file_paths(self) -> List[Path]:
        selected_paths: List[Path] = []
        
        # Add root path if it's selected explicitly (though tree doesn't show root as checkable item)
        # This logic might be better handled by checking if the invisibleRootItem's children imply root selection.
        # For now, selected_paths will contain children of root.
        
        def recurse_items(parent_item: QStandardItem):
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)
                if item:
                    path_obj = item.data(PATH_ROLE)
                    # Include if checked, or if partially checked (for directories that contain selections)
                    if path_obj and item.checkState() != Qt.Unchecked: 
                        selected_paths.append(path_obj)
                    
                    # Only recurse into children if the parent directory item itself is part of the selection
                    # (i.e., it's checked or partially checked). No need to look into fully unchecked dirs.
                    if item.hasChildren() and item.data(IS_DIR_ROLE) and item.checkState() != Qt.Unchecked:
                         recurse_items(item) 

        recurse_items(self.tree_model.invisibleRootItem())
        
        unique_paths = sorted(list(set(selected_paths)), key=lambda p: str(p))
        return unique_paths

    def _set_all_checks(self, state: Qt.CheckState, only_text_files: bool = False):
        # Disconnect signals during bulk update
        try:
            self.tree_model.itemChanged.disconnect(self.on_item_changed)
        except TypeError: # was not connected
            pass
        self._is_updating_checks = True 
        
        try:
            # Iterate over top-level items
            for i in range(self.tree_model.rowCount()):
                item = self.tree_model.item(i)
                self._set_item_check_recursive(item, state, only_text_files)
            
            # After all individual items are set, update parent states from bottom up
            # This is critical to get correct tri-state for directories
            for i in range(self.tree_model.rowCount()):
                top_item = self.tree_model.item(i)
                if top_item and top_item.data(IS_DIR_ROLE):
                    self._update_all_parent_states_recursive(top_item)

        finally:
            self._is_updating_checks = False
            try:
                self.tree_model.itemChanged.connect(self.on_item_changed)
            except TypeError: # if it was already connected by mistake
                pass

    def _set_item_check_recursive(self, item: QStandardItem, state: Qt.CheckState, only_text_files: bool):
        if not item: return

        is_dir = item.data(IS_DIR_ROLE)
        is_text = item.data(IS_TEXT_FILE_ROLE) if not is_dir else False 

        apply_state = False
        if item.isCheckable() and item.isEnabled():
            if only_text_files:
                if is_dir: # For directories, always apply state to allow children to be checked
                    apply_state = True
                elif is_text: # For text files, apply state
                    apply_state = True
            else: # Not only_text_files, apply to all checkable & enabled
                apply_state = True
        
        if apply_state and item.checkState() != state :
            item.setCheckState(state)
        
        if is_dir:
            for row in range(item.rowCount()):
                self._set_item_check_recursive(item.child(row), state, only_text_files)

    def _update_all_parent_states_recursive(self, item: QStandardItem):
        """Helper for _set_all_checks to correctly update parent states after bulk changes."""
        if not item or not item.data(IS_DIR_ROLE):
            return
        
        for row in range(item.rowCount()):
            child = item.child(row)
            if child and child.data(IS_DIR_ROLE):
                self._update_all_parent_states_recursive(child) # Recurse to deepest children first
        
        # Now update this item based on its children
        self._update_parent_check_state_from_children(item)


    def check_all_text_files(self):
        self.app.show_status("Checking all text files in tree...")
        self._set_all_checks(Qt.Checked, only_text_files=True)
        self.app.show_status("All text files checked.")

    def uncheck_all_files(self):
        self.app.show_status("Unchecking all items in tree...")
        self._set_all_checks(Qt.Unchecked)
        self.app.show_status("All items unchecked.")


class FolderStructureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        QCoreApplication.setOrganizationName("AICodeHelper")
        QCoreApplication.setApplicationName("FolderStructureAppV2.6") # Updated
        self.settings = QSettings()
        
        self.theme_manager = ThemeManager(QApplication.instance(), self.settings, THEMES_DIR, ASSETS_DIR, DEFAULT_THEME_FILE)
        
        self.processor = FolderProcessor(
            status_callback=self.show_status,
            warning_callback=self.show_warning,
            error_callback=self.show_error
        )
        self.current_environment_file: Optional[Path] = None
        self.recent_environments: List[Dict[str, str]] = []
        self.prompt_templates: List[Dict[str, str]] = []
        self.loaded_doc_paths: List[str] = []

        self.initUI() 
        self.load_persistent_settings() 
        
        self.create_actions()
        self.create_menus() 
        self.create_status_bar()

        self._update_recent_menu()
        self._update_template_combo()
        self._update_doc_list_widget()
        
        # Apply initial theme after UI is set up and settings loaded
        initial_theme_file = self.theme_manager.get_current_theme_file_name()
        self.theme_manager.apply_theme_from_file_name(initial_theme_file)

        self.load_initial_environment()

    # ... (show_status, show_warning, show_error remain the same) ...
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
        self.setWindowTitle('Folder Structure to Text v2.6') 
        self.setGeometry(100, 100, 1200, 900) 
        self.setWindowIcon(load_icon("application-x-executable", "application-x-executable")) # Generic app icon

        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)

        settings_widget = QWidget()
        settings_widget.setObjectName("SettingsTabWidget") # For potential specific styling
        settings_outer_layout = QVBoxLayout(settings_widget)
        settings_outer_layout.setSpacing(10)
        self._create_settings_tab_content(settings_outer_layout)
        self.main_tabs.addTab(
            settings_widget,
            load_icon("preferences-system", "preferences-system"), 
            "Settings & Filters"
        )
        
        self.file_selection_tab = FileSelectionTab(self)
        self.file_selection_tab.setObjectName("FileSelectionTabWidget")
        self.main_tabs.addTab(
            self.file_selection_tab,
            load_icon("edit-select-all", "edit-select-all"), 
            "File Selection"
        )

        output_widget = QWidget()
        output_widget.setObjectName("OutputTabWidget") # Name for finding it
        output_layout = QVBoxLayout(output_widget)
        output_layout.setSpacing(10)
        self._create_output_tab_content(output_layout)
        self.main_tabs.addTab(
            output_widget,
            load_icon("text-x-generic", "text-x-generic"), 
            "Output"
        )
        
        self.folder_path_edit.editingFinished.connect(self.handle_folder_path_changed_for_tree)

    # ... (_create_settings_tab_content, _create_output_tab_content remain largely same, check icon names)
    def _create_settings_tab_content(self, layout: QVBoxLayout):
        folder_group = QGroupBox("Target Project Folder")
        folder_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("Select the target folder...")
        self.folder_path_edit.textChanged.connect(self._handle_folder_change_for_title)
        browse_button = QPushButton(load_icon("folder-open", "document-open"), " Browse...") # Fallback for folder-open
        browse_button.setToolTip("Select the root folder of the project")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_path_edit, 1)
        folder_layout.addWidget(browse_button)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content_widget = QWidget() 
        scroll_layout = QVBoxLayout(scroll_content_widget)

        self.settings_toolbox = QToolBox()
        self.settings_toolbox.layout().setSpacing(6) 

        preset_widget = QWidget()
        preset_layout = QVBoxLayout(preset_widget)
        preset_layout.setContentsMargins(9,9,9,9) 
        preset_label = QLabel("Exclusion Presets (Ctrl/Shift + Click for multiple):")
        preset_layout.addWidget(preset_label)
        self.preset_list_widget = QListWidget()
        self.preset_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.preset_list_widget.addItems(PRESET_OPTIONS)
        self.preset_list_widget.setFixedHeight(130) 
        self.preset_list_widget.setToolTip("Combine presets. Select none to use only defaults + custom.")
        preset_layout.addWidget(self.preset_list_widget)
        self.settings_toolbox.addItem(preset_widget, load_icon("preferences-exclude", "view-filter-rtl"), "Exclusion Presets")

        custom_filter_widget = QWidget()
        custom_filter_layout = QVBoxLayout(custom_filter_widget)
        custom_filter_layout.setContentsMargins(9,9,9,9)
        custom_group = QGroupBox("Custom Filtering Rules (Comma-separated)")
        custom_form_layout = QFormLayout(custom_group) 
        
        self.custom_folders_edit = QLineEdit()
        self.custom_folders_edit.setPlaceholderText("e.g., docs,tests,temp")
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText("e.g., .log,.tmp,.bak")
        self.custom_patterns_edit = QLineEdit()
        self.custom_patterns_edit.setPlaceholderText("e.g., *.log,temp_*,cache_*/")
        self.dynamic_exclude_edit = QLineEdit() 
        self.dynamic_exclude_edit.setPlaceholderText("e.g., *.private,credentials.json (applied during tree build)")
        self.custom_inclusions_edit = QLineEdit()
        self.custom_inclusions_edit.setPlaceholderText("e.g., src/main/, README.md, docs/*.md")

        custom_form_layout.addRow("Exclude Folders:", self.custom_folders_edit)
        custom_form_layout.addRow("Exclude Exts:", self.custom_extensions_edit)
        custom_form_layout.addRow("Exclude Patterns:", self.custom_patterns_edit)
        custom_form_layout.addRow("Dynamic Exclude (Tree):", self.dynamic_exclude_edit)
        custom_form_layout.addRow("Include Paths/Patterns (Tree):", self.custom_inclusions_edit)
        custom_filter_layout.addWidget(custom_group)
        self.settings_toolbox.addItem(custom_filter_widget, load_icon("view-filter", "system-search"), "Custom Filtering (Initial Tree State)")

        options_widget = QWidget()
        options_layout = QFormLayout(options_widget) 
        options_layout.setContentsMargins(9,9,9,9)
        self.max_size_spinbox = QDoubleSpinBox()
        self.max_size_spinbox.setSuffix(" MB")
        self.max_size_spinbox.setMinimum(0.01)
        self.max_size_spinbox.setMaximum(500.0) 
        self.max_size_spinbox.setSingleStep(0.1)
        self.max_size_spinbox.setValue(DEFAULT_MAX_FILE_SIZE_MB)
        self.save_output_checkbox = QCheckBox("Save Markdown output automatically on Generate")
        options_layout.addRow("Max File Size (Content):", self.max_size_spinbox)
        options_layout.addRow(self.save_output_checkbox) 
        self.settings_toolbox.addItem(options_widget, load_icon("preferences-desktop-display", "video-display"), "Generation Options")

        doc_integration_widget = QWidget()
        doc_layout = QVBoxLayout(doc_integration_widget)
        doc_layout.setContentsMargins(9,9,9,9)
        doc_layout.addWidget(QLabel("Import Markdown documentation files (appended to prompt):"))
        self.doc_list_widget = QListWidget()
        self.doc_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.doc_list_widget.setToolTip("Content of these files will be added to the AI prompt.")
        self.doc_list_widget.setFixedHeight(100) 
        doc_layout.addWidget(self.doc_list_widget)
        
        doc_button_layout = QHBoxLayout()
        add_doc_button = QPushButton(load_icon("document-open", "document-open"), " Add Docs...")
        add_doc_button.clicked.connect(self.add_documentation)
        remove_doc_button = QPushButton(load_icon("list-remove", "edit-delete"), " Remove Selected")
        remove_doc_button.clicked.connect(self.remove_documentation)
        clear_docs_button = QPushButton(load_icon("edit-clear", "edit-clear-all"), " Clear All")
        clear_docs_button.clicked.connect(self.clear_documentation)
        doc_button_layout.addWidget(add_doc_button)
        doc_button_layout.addWidget(remove_doc_button)
        doc_button_layout.addWidget(clear_docs_button)
        doc_layout.addLayout(doc_button_layout)
        self.settings_toolbox.addItem(doc_integration_widget, load_icon("text-markdown", "text-x-markdown"), "Documentation Integration")

        scroll_layout.addWidget(self.settings_toolbox)
        scroll_area.setWidget(scroll_content_widget) 
        layout.addWidget(scroll_area, 1) 

        prompt_group = QGroupBox("Custom Instructions Prompt (appended after structure & docs)")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_template_layout = QHBoxLayout()
        prompt_template_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.setToolTip("Select a saved prompt template")
        self.template_combo.addItem("-- Select Template --") 
        
        load_template_button = QPushButton(load_icon("document-open", "document-open"), " Load")
        load_template_button.setToolTip("Load selected template into the text area below")
        load_template_button.clicked.connect(self.load_selected_template)
        save_template_button = QPushButton(load_icon("document-save-as", "document-save-as"), " Save As...")
        save_template_button.setToolTip("Save the current text below as a new template")
        save_template_button.clicked.connect(self.save_template_as)
        manage_template_button = QPushButton(load_icon("document-properties", "preferences-other"), " Manage...")
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

        self.generate_button = QPushButton(load_icon("system-run", "media-playback-start"), " Generate Structure Text")
        self.generate_button.setToolTip("Analyze selection and generate the output")
        self.generate_button.clicked.connect(self.generate_structure)
        self.generate_button.setFixedHeight(35) 
        layout.addWidget(self.generate_button, 0, Qt.AlignCenter)

    def _create_output_tab_content(self, layout: QVBoxLayout):
        self.output_tabs = QTabWidget()

        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_layout.setContentsMargins(0,0,0,0) 
        self.raw_output_textedit = QTextEdit()
        self.raw_output_textedit.setReadOnly(True)
        self.raw_output_textedit.setFont(QFont("Courier New", 10)) 
        self.raw_output_textedit.setLineWrapMode(QTextEdit.NoWrap) 
        self.raw_output_textedit.setPlaceholderText("Generated Markdown output will appear here.")
        raw_layout.addWidget(self.raw_output_textedit)
        self.output_tabs.addTab(raw_widget, load_icon("text-plain", "text-x-generic"), "Raw Markdown")

        rendered_widget = QWidget()
        render_layout = QVBoxLayout(rendered_widget)
        render_layout.setContentsMargins(0,0,0,0)
        self.rendered_output_view = QTextEdit()
        self.rendered_output_view.setReadOnly(True)
        self.rendered_output_view.setPlaceholderText("A basic rendered preview of the Markdown will appear here.")
        render_layout.addWidget(self.rendered_output_view)
        self.output_tabs.addTab(rendered_widget, load_icon("text-html", "text-html"), "Rendered Preview")
        
        layout.addWidget(self.output_tabs)

        output_button_layout = QHBoxLayout()
        self.copy_raw_button = QPushButton(load_icon("edit-copy", "edit-copy"), " Copy Raw Markdown")
        self.copy_raw_button.setToolTip("Copy the full raw Markdown output to the clipboard")
        self.copy_raw_button.clicked.connect(self.copy_raw_output)
        self.copy_raw_button.setEnabled(False) 

        clear_output_button = QPushButton(load_icon("edit-clear", "edit-clear-all"), " Clear Output")
        clear_output_button.clicked.connect(self.clear_output)

        output_button_layout.addWidget(self.copy_raw_button)
        output_button_layout.addStretch(1) 
        output_button_layout.addWidget(clear_output_button)
        layout.addLayout(output_button_layout)


    def handle_folder_path_changed_for_tree(self):
        folder_path = self.folder_path_edit.text()
        if folder_path and Path(folder_path).is_dir():
            self.file_selection_tab.populate_tree()
        elif folder_path: # Path entered but not valid dir or empty
            if not folder_path: # If empty, clear tree
                self.file_selection_tab.tree_model.clear()
                self.file_selection_tab.tree_model.setHorizontalHeaderLabels(['Name'])
            else: # Invalid path
                QMessageBox.warning(self, "Invalid Folder", f"The path '{folder_path}' is not a valid directory. Tree not populated.")


    def create_actions(self):
        # ... (File/Edit actions remain similar, check icons)
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
            load_icon("document-open-recent", "document-open-recent"), 
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
            load_icon("edit-clear", "edit-clear-all"), "&Clear Output Area", self,
            shortcut="Ctrl+Shift+C", statusTip="Clear the output text area",
            triggered=self.clear_output
        )
        
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
        self.themes_menu = view_menu.addMenu(
            load_icon("preferences-desktop-theme", "preferences-desktop-theme"), # Example icon
            "&Themes"
        )
        self.theme_manager.create_theme_menu_actions(self.themes_menu) # Populate themes

    # ... (create_status_bar, browse_folder, new_project, clear_output, copy_raw_output, update_rendered_output remain largely same) ...
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
            self.file_selection_tab.populate_tree() 


    def new_project(self):
        confirm = QMessageBox.question(
            self, "New Project",
            "Clear the target folder path, output, and interactive tree selection?\nDisconnect current environment file (if any)?\n\nCurrent exclusion, inclusion, prompt, documentation, and other settings will be kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if confirm == QMessageBox.Yes:
            self.folder_path_edit.clear()
            self.clear_output()
            self.file_selection_tab.tree_model.clear() 
            self.file_selection_tab.tree_model.setHorizontalHeaderLabels(['Name'])

            self.current_environment_file = None
            self.save_env_action.setEnabled(False)
            self._update_window_title()
            self.show_status("New project started. Settings kept, folder and tree cleared.")
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
            try:
                html_output = markdown.markdown(raw_markdown, extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'])
                # For codehilite to work well, you might need Pygments installed and a CSS for it.
                # For now, basic fenced_code styling will come from QSS if defined for <pre> or <code>.
                self.rendered_output_view.setHtml(html_output)
            except Exception as e:
                self.show_warning(f"Markdown rendering error: {e}. Showing raw text.")
                self.rendered_output_view.setPlainText(raw_markdown)
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
            "Reset ALL settings (filters, inclusions, prompt, docs, templates, theme) to defaults and clear folder/output/tree?\nEnvironment association will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            default_settings_copy = DEFAULT_SETTINGS.copy() 
            default_settings_copy["prompt_templates"] = list(DEFAULT_AI_PROMPT_TEMPLATES) 
            default_settings_copy["loaded_doc_paths"] = []
            # Default theme is handled by ThemeManager and DEFAULT_SETTINGS["current_theme_file"]

            self.apply_settings_to_ui(default_settings_copy) 
            self.folder_path_edit.clear()
            self.clear_output()
            self.file_selection_tab.tree_model.clear() 
            self.file_selection_tab.tree_model.setHorizontalHeaderLabels(['Name'])

            self.prompt_templates = default_settings_copy["prompt_templates"]
            self.loaded_doc_paths = default_settings_copy["loaded_doc_paths"]
            self.current_environment_file = None

            self._update_template_combo()
            self._update_doc_list_widget()
            
            # Apply the default theme
            self.theme_manager.apply_theme_from_file_name(DEFAULT_SETTINGS["current_theme_file"])

            self._update_window_title()
            self.save_env_action.setEnabled(False)

            self.show_status("All settings reset to defaults.")

    # ... (get_settings_from_ui, apply_settings_to_ui are mostly the same, adjust for theme setting name)
    def get_settings_from_ui(self) -> Dict[str, Any]:
        selected_presets = [item.text() for item in self.preset_list_widget.selectedItems()]

        user_templates = [
            t for t in self.prompt_templates 
            if not any(d_t['name'] == t['name'] and d_t['content'] == t['content'] for d_t in DEFAULT_AI_PROMPT_TEMPLATES)
        ]

        settings = {
            "version": "2.6", 
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
            "current_theme_file": self.theme_manager.current_theme_file_name, # Get from theme manager
            "prompt_templates": user_templates, 
            "loaded_doc_paths": self.loaded_doc_paths,
        }
        return settings

    def apply_settings_to_ui(self, settings_dict: Dict[str, Any]):
        loaded_version = settings_dict.get("version", "1.0") 
        if not loaded_version.startswith("2."): 
             print(f"INFO: Loading settings from a legacy format (v{loaded_version}). Applying defaults for new features.")

        self.folder_path_edit.setText(settings_dict.get("folder_path", DEFAULT_SETTINGS["folder_path"]))

        self.preset_list_widget.clearSelection()
        selected_presets_from_file = settings_dict.get("selected_presets", [])
        if isinstance(selected_presets_from_file, list):
            for preset_name in selected_presets_from_file:
                items = self.preset_list_widget.findItems(preset_name, Qt.MatchExactly)
                if items:
                    items[0].setSelected(True)
        
        self.custom_folders_edit.setText(settings_dict.get("custom_folders", DEFAULT_SETTINGS["custom_folders"]))
        self.custom_extensions_edit.setText(settings_dict.get("custom_extensions", DEFAULT_SETTINGS["custom_extensions"]))
        self.custom_patterns_edit.setText(settings_dict.get("custom_patterns", DEFAULT_SETTINGS["custom_patterns"]))
        self.dynamic_exclude_edit.setText(settings_dict.get("dynamic_patterns", DEFAULT_SETTINGS["dynamic_patterns"]))
        self.custom_inclusions_edit.setText(settings_dict.get("custom_inclusions", DEFAULT_SETTINGS["custom_inclusions"]))

        self.max_size_spinbox.setValue(
            float(settings_dict.get("max_file_size_mb", DEFAULT_SETTINGS["max_file_size_mb"]))
        )
        self.save_output_checkbox.setChecked(
            bool(settings_dict.get("save_output_checked", DEFAULT_SETTINGS["save_output_checked"]))
        )
        self.custom_prompt_edit.setPlainText(
            settings_dict.get("custom_prompt", DEFAULT_SETTINGS["custom_prompt"])
        )

        loaded_user_templates = settings_dict.get("prompt_templates", [])
        combined_templates = list(DEFAULT_AI_PROMPT_TEMPLATES) 
        default_names = {t['name'] for t in DEFAULT_AI_PROMPT_TEMPLATES}
        if isinstance(loaded_user_templates, list):
            for t_user in loaded_user_templates:
                if isinstance(t_user, dict) and 'name' in t_user and 'content' in t_user:
                    if t_user['name'] not in default_names:
                        combined_templates.append(t_user)
                    else: 
                        for i, d_t in enumerate(DEFAULT_AI_PROMPT_TEMPLATES):
                            if d_t['name'] == t_user['name'] and d_t['content'] != t_user['content']:
                                combined_templates[i] = t_user 
                                break
                else:
                    self.show_warning(f"Invalid template format found in environment file: {t_user}. Skipping.")
        self.prompt_templates = combined_templates

        loaded_docs = settings_dict.get("loaded_doc_paths", [])
        if isinstance(loaded_docs, list) and all(isinstance(p, str) for p in loaded_docs):
             self.loaded_doc_paths = loaded_docs
        else:
             self.loaded_doc_paths = []
             if "loaded_doc_paths" in settings_dict:
                 self.show_warning("Loaded documentation paths have an invalid format. Clearing list.")
        
        # Theme is applied separately after settings are loaded if it's initial load
        # For subsequent loads via "Load Environment", theme should be applied.
        # The theme_manager.current_theme_file_name would have been updated from settings.
        loaded_theme_file = settings_dict.get("current_theme_file", DEFAULT_SETTINGS["current_theme_file"])
        if self.theme_manager.current_theme_file_name != loaded_theme_file: # Apply if different
            self.theme_manager.apply_theme_from_file_name(loaded_theme_file)


        self._update_template_combo()
        self._update_doc_list_widget()
        
        if self.folder_path_edit.text() and Path(self.folder_path_edit.text()).is_dir():
            self.file_selection_tab.populate_tree()
        else: 
            self.file_selection_tab.tree_model.clear()
            self.file_selection_tab.tree_model.setHorizontalHeaderLabels(['Name'])

    # ... (load_persistent_settings, load_initial_environment, _update_window_title, _handle_folder_change_for_title remain mostly same, adjust for theme)
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

        # Load theme preference - ThemeManager handles actual application
        # This call ensures theme_manager knows the persisted preference.
        self.theme_manager.current_theme_file_name = self.settings.value("currentThemeFileName", DEFAULT_THEME_FILE)


        user_templates_data = self.settings.value("promptTemplates", [])
        self.prompt_templates = list(DEFAULT_AI_PROMPT_TEMPLATES)
        default_names = {t['name'] for t in self.prompt_templates}

        if isinstance(user_templates_data, list):
            for t_user in user_templates_data:
                if isinstance(t_user, dict) and 'name' in t_user and 'content' in t_user:
                    is_customized_default = False
                    for i, d_t in enumerate(self.prompt_templates):
                        if d_t['name'] == t_user['name']:
                            if d_t['content'] != t_user['content']: 
                                self.prompt_templates[i] = t_user
                            is_customized_default = True
                            break
                    if not is_customized_default and t_user['name'] not in default_names:
                         self.prompt_templates.append(t_user) 
                else:
                    print("WARNING: Stored prompt template has invalid format. Skipping.")
        else:
            if user_templates_data: 
                print("WARNING: Stored prompt templates invalid format (not a list). Resetting.")
                self.settings.remove("promptTemplates")

        doc_paths_data = self.settings.value("loadedDocPaths", [])
        valid_doc_paths = []
        if isinstance(doc_paths_data, list) and all(isinstance(p, str) for p in doc_paths_data):
             for path_str in doc_paths_data:
                 if Path(path_str).exists() and Path(path_str).is_file():
                     valid_doc_paths.append(path_str)
                 else:
                      print(f"INFO: Pruning non-existent documentation path from persistent settings: {path_str}")
             self.loaded_doc_paths = valid_doc_paths
             if len(self.loaded_doc_paths) != len(doc_paths_data): 
                 self.settings.setValue("loadedDocPaths", self.loaded_doc_paths)
        else:
             self.loaded_doc_paths = []
             if doc_paths_data: 
                 print("WARNING: Stored documentation paths invalid format. Resetting.")
                 self.settings.remove("loadedDocPaths")

    def load_initial_environment(self):
        loaded_from_recent = False
        if self.recent_environments:
            most_recent_path_str = self.recent_environments[0].get('path')
            if most_recent_path_str:
                most_recent_path = Path(most_recent_path_str)
                if most_recent_path.exists():
                    if self._load_environment_from_path(most_recent_path):
                        loaded_from_recent = True
                    else: 
                        self.show_warning(f"Failed loading most recent env '{most_recent_path.name}'. Removing from list.")
                        self._remove_recent_environment(str(most_recent_path)) 
                else: 
                    self.show_warning(f"Most recent env file not found: '{most_recent_path.name}'. Removing from list.")
                    self._remove_recent_environment(str(most_recent_path))

        if not loaded_from_recent:
            settings_to_apply = DEFAULT_SETTINGS.copy()
            settings_to_apply['prompt_templates'] = self.prompt_templates 
            settings_to_apply['loaded_doc_paths'] = self.loaded_doc_paths 
            # Theme is already set by theme_manager based on its persistent setting
            settings_to_apply['current_theme_file'] = self.theme_manager.current_theme_file_name 
            
            self.apply_settings_to_ui(settings_to_apply) 
            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            self.show_status("Loaded default settings. No recent environment loaded or load failed.")

    def _update_window_title(self):
        base_title = "Folder Structure to Text v2.6"
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


    # ... (_load_environment_from_path, load_environment_dialog, save_current_environment, save_environment_as, recent env methods, template methods, doc methods, generate_structure, save_output_markdown_to_file remain largely same)
    def _load_environment_from_path(self, file_path: Path) -> bool:
        self.show_status(f"Loading environment: {file_path.name}...")
        try:
            with file_path.open('r', encoding='utf-8') as f:
                loaded_settings_dict = json.load(f) # Renamed for clarity
            if not isinstance(loaded_settings_dict, dict):
                raise TypeError("Invalid JSON format in environment file.")

            # Apply all settings from the file, including theme if present
            self.apply_settings_to_ui(loaded_settings_dict) 

            # apply_settings_to_ui now calls theme_manager.apply_theme_from_file_name
            # if the theme in the loaded_settings_dict is different from the current one.

            # Validate doc paths again after apply_settings_to_ui might have changed them
            valid_loaded_docs = []
            for path_str in self.loaded_doc_paths: 
                 if Path(path_str).exists() and Path(path_str).is_file():
                      valid_loaded_docs.append(path_str)
                 else:
                      self.show_warning(f"Documentation file from environment not found: {path_str}")
            self.loaded_doc_paths = valid_loaded_docs
            self._update_doc_list_widget() 

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
        except Exception as e:
            self.show_error(f"Failed saving environment: {e}")

    def save_environment_as(self):
        current_settings = self.get_settings_from_ui()
        start_dir = self.settings.value("lastEnvDir", str(Path.home()))

        folder_name = Path(self.folder_path_edit.text()).name
        sanitized_folder_name = sanitize_filename(folder_name) if folder_name else "untitled"
        default_name = f"{sanitized_folder_name}_fse_env.json"

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
                action_text = f"&{i+1} {env['name']}"
                if len(action_text) > 50: action_text = action_text[:47] + "..."
                
                action = QAction(
                    action_text, self,
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

        for template in sorted_templates: 
            self.template_combo.addItem(template.get('name', 'Unnamed Template'), userData=template)

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
            QMessageBox.warning(self, "Cannot Save Empty", "Prompt text area is empty. Cannot save as template.")
            return

        dialog = EditTemplateDialog(
            template_content=current_content, 
            existing_names=self.get_template_names(), 
            parent=self
        )
        dialog.setWindowTitle("Save Current Prompt as Template")

        if dialog.exec_() == QDialog.Accepted:
            new_template_name = dialog.get_template_name()
            new_template_content = dialog.get_template_content() 

            new_template = {
                "name": new_template_name,
                "content": new_template_content
            }
            
            is_exact_default_duplicate = any(
                t_def['name'] == new_template_name and t_def['content'] == new_template_content
                for t_def in DEFAULT_AI_PROMPT_TEMPLATES
            )

            if is_exact_default_duplicate:
                self.show_warning(f"Template '{new_template_name}' is identical to a default template and was not saved as a new user template.")
                idx = self.template_combo.findText(new_template_name)
                if idx != -1: self.template_combo.setCurrentIndex(idx)
                return

            existing_template_index = -1
            for i, t in enumerate(self.prompt_templates):
                if t['name'] == new_template_name:
                    existing_template_index = i
                    break
            
            if existing_template_index != -1: 
                self.prompt_templates[existing_template_index] = new_template
                self.show_status(f"Template '{new_template_name}' updated.")
            else: 
                self.prompt_templates.append(new_template)
                self.show_status(f"Prompt saved as new template '{new_template_name}'.")

            self.save_prompt_templates_to_settings() 
            self._update_template_combo() 
            idx = self.template_combo.findText(new_template_name)
            if idx != -1: self.template_combo.setCurrentIndex(idx)


    def manage_prompt_templates(self):
        dialog = PromptTemplateManagerDialog(self.prompt_templates, parent=self)
        dialog.exec_() 

        updated_templates_from_dialog = dialog.get_updated_templates()
        self.prompt_templates = updated_templates_from_dialog
        
        self.save_prompt_templates_to_settings() 
        self._update_template_combo() 
        self.show_status("Template management closed. Changes (if any) saved.")


    def get_template_names(self) -> List[str]: 
        return [t.get('name', '') for t in self.prompt_templates]

    def save_prompt_templates_to_settings(self):
        user_templates_to_save = [
            t for t in self.prompt_templates 
            if not any(d_t['name'] == t['name'] and d_t['content'] == t['content'] for d_t in DEFAULT_AI_PROMPT_TEMPLATES)
        ]
        self.settings.setValue("promptTemplates", user_templates_to_save)


    def add_documentation(self):
        start_dir = self.settings.value("lastDocDir", str(Path.home()))
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, "Add Markdown Documentation Files", start_dir,
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)"
        )
        added_count = 0
        if fileNames:
            current_dir_of_selection = ""
            for fileName in fileNames:
                path = Path(fileName)
                if path.is_file() and path.suffix.lower() in ['.md', '.markdown', '.txt']:
                    path_str = str(path.resolve()) 
                    if path_str not in self.loaded_doc_paths:
                        self.loaded_doc_paths.append(path_str)
                        added_count += 1
                        current_dir_of_selection = str(path.parent) 
                    else:
                        self.show_warning(f"Documentation file already added: {path.name}")
                else: 
                     self.show_warning(f"Skipping invalid or non-text file: {fileName}")
            
            if current_dir_of_selection: 
                self.settings.setValue("lastDocDir", current_dir_of_selection)
            
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
            "Are you sure you want to remove all loaded documentation files from the list?",
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
            item_text = f"{path.name}  ({path.parent.name})"
            if len(item_text) > 60 : item_text = item_text[:57] + "..." 

            item = QListWidgetItem(item_text)
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
                 combined_docs.append(f"---\n**Documentation: `{path.name}` (from `{path.parent.name}`)**\n\n{content.strip()}\n---")
             except Exception as e:
                  self.show_warning(f"Error reading documentation file '{path.name}': {e}")
                  combined_docs.append(f"---\n**Documentation: `{path.name}` [Error Reading File: {e}]**\n---")
        return "\n\n".join(combined_docs) if combined_docs else ""


    def generate_structure(self):
        settings = self.get_settings_from_ui() 
        folder_path = settings["folder_path"]

        if not folder_path or not Path(folder_path).is_dir():
            self.show_warning("Please select a valid target folder for generation.")
            self.browse_folder() 
            if not self.folder_path_edit.text() or not Path(self.folder_path_edit.text()).is_dir():
                return 

        self.settings.setValue("lastFolderPath", folder_path) 
        if not self.current_environment_file: 
            self._update_window_title()

        self.generate_button.setEnabled(False)
        self.copy_raw_button.setEnabled(False)
        self.raw_output_textedit.setPlainText("Generating, please wait...")
        self.rendered_output_view.setPlainText("Generating...")
        
        # Find output tab index robustly
        output_tab_widget = self.main_tabs.findChild(QWidget, "OutputTabWidget")
        if output_tab_widget:
            output_tab_index = self.main_tabs.indexOf(output_tab_widget)
            if output_tab_index != -1:
                self.main_tabs.setCurrentIndex(output_tab_index)
        else: # Fallback if name not set or found
            for i in range(self.main_tabs.count()):
                if self.main_tabs.tabText(i) == "Output":
                    self.main_tabs.setCurrentIndex(i)
                    break
        self.output_tabs.setCurrentIndex(0) 
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents() 

        final_custom_prompt = apply_placeholders(settings["custom_prompt"], self)
        if final_custom_prompt != settings["custom_prompt"]: 
            self.show_status("Applied placeholders to custom prompt for generation.")

        documentation_content = self._get_combined_documentation_content()
        if documentation_content:
            self.show_status(f"Including content from {len(self.loaded_doc_paths)} documentation file(s).")

        selected_paths_from_tree = self.file_selection_tab.get_selected_file_paths()
        
        # Handle case where tree is empty or no selections were made explicitly
        # If selected_paths_from_tree is empty, it means either tree was not populated,
        # or user unchecked everything. Processor will then fall back to filter-based.
        if not Path(folder_path).exists(): # Double check folder still exists
            self.show_error(f"Target folder '{folder_path}' no longer exists. Generation aborted.")
            QApplication.restoreOverrideCursor()
            self.generate_button.setEnabled(True)
            return

        if not selected_paths_from_tree and Path(folder_path).iterdir().__next__(None) is not None : # Folder has content but tree selection is empty
             reply = QMessageBox.question(self, "Empty Selection",
                                       "No files or folders are selected in the 'File Selection' tree. "
                                       "Do you want to proceed with filter-based processing (ignoring the tree selection)? This will process files based on the 'Settings & Filters' tab.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
             if reply == QMessageBox.No:
                QApplication.restoreOverrideCursor()
                self.generate_button.setEnabled(True)
                self.main_tabs.setCurrentWidget(self.file_selection_tab) 
                return
             # else: User chose Yes, so selected_paths_from_tree remains empty, processor will use filters

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
                documentation_content,
                selected_file_paths=selected_paths_from_tree # Pass possibly empty list
            )

            self.raw_output_textedit.setPlainText(generated_text)
            self.update_rendered_output() 

            is_error_output = generated_text.startswith("```error")
            self.copy_raw_button.setEnabled(not is_error_output and bool(generated_text)) 

            if settings["save_output_checked"] and not is_error_output and generated_text:
                self.save_output_markdown_to_file(generated_text, Path(folder_path).name)

        except Exception as e: 
            self.show_error(f"Critical error during generation: {e}\n{traceback.format_exc()}")
            error_msg = f"```error\nCritical error during generation: {e}\n{traceback.format_exc()}\n```"
            self.raw_output_textedit.setPlainText(error_msg)
            self.rendered_output_view.setPlainText(error_msg) 
            self.copy_raw_button.setEnabled(False)
        finally:
            QApplication.restoreOverrideCursor()
            self.generate_button.setEnabled(True)
            self.raw_output_textedit.moveCursor(QTextCursor.Start) 
            self.raw_output_textedit.ensureCursorVisible()


    def save_output_markdown_to_file(self, text_content: str, folder_name: str):
        current_project_folder = self.folder_path_edit.text()
        default_dir_str = str(Path(current_project_folder).parent) if current_project_folder and Path(current_project_folder).is_dir() else str(Path.home())
        
        save_dir_str = self.settings.value("lastMarkdownSaveDir", default_dir_str)
        save_dir = Path(save_dir_str)
        if not save_dir.exists() or not save_dir.is_dir(): 
            save_dir = Path(default_dir_str)
            if not save_dir.exists() or not save_dir.is_dir():
                save_dir = Path.home() 
            self.settings.remove("lastMarkdownSaveDir") 

        sanitized_folder_name = sanitize_filename(folder_name) if folder_name else "output"
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        suggested_name = f"fse_{sanitized_folder_name}_{timestamp}.md"

        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown Output", str(save_dir / suggested_name),
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


    def closeEvent(self, event: 'QCloseEvent'):
        self.settings.setValue("currentThemeFileName", self.theme_manager.current_theme_file_name)
        self.save_prompt_templates_to_settings() 
        self.settings.setValue("recentEnvironments", self.recent_environments)
        
        valid_doc_paths = [p for p in self.loaded_doc_paths if Path(p).exists() and Path(p).is_file()]
        self.settings.setValue("loadedDocPaths", valid_doc_paths)

        if self.folder_path_edit.text() and Path(self.folder_path_edit.text()).exists():
            self.settings.setValue("lastBrowseDir", self.folder_path_edit.text())
        
        if self.current_environment_file and self.current_environment_file.parent.exists():
            self.settings.setValue("lastEnvDir", str(self.current_environment_file.parent))
        
        for key in ["lastDocDir", "lastMarkdownSaveDir"]:
            path_val = self.settings.value(key)
            if path_val and (not Path(path_val).exists() or not Path(path_val).is_dir()):
                self.settings.remove(key) 

        self.settings.sync() 
        self.show_status("Settings saved. Exiting...")
        event.accept()


if __name__ == '__main__':
    if not ASSETS_DIR.exists():
        try:
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Created missing assets directory: {ASSETS_DIR}")
            check_svg_path = ASSETS_DIR / "check.svg"
            if not check_svg_path.exists():
                check_svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="white"><path d="M12.03.293a1 1 0 00-1.413 0L5 6.172 3.383 4.555a1 1 0 00-1.414 1.414l2.5 2.5a1 1 0 001.414 0L12.03 1.707a1 1 0 000-1.414z"/></svg>'
                try:
                    with open(check_svg_path, "w") as f:
                        f.write(check_svg_content)
                    print(f"Created dummy check.svg at {check_svg_path}")
                except IOError as ioe:
                    print(f"Warning: Could not create dummy check.svg: {ioe}")
        except OSError as e:
            print(f"Warning: Could not create assets directory or dummy files: {e}")
    
    if not THEMES_DIR.exists():
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created themes directory: {THEMES_DIR}")
        # Optionally, create default theme files here if they are missing
        # For example, themes/default_light.qss and themes/default_dark.qss
        # This is good for first-time run.


    app = QApplication(sys.argv)
    try:
        main_window = FolderStructureApp()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e: 
        print("\n--- Unhandled Exception During Application Startup ---")
        print(f"Error: {e}")
        print(traceback.format_exc())
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Application Startup Crash")
            msgBox.setText(f"An unexpected error occurred during startup:\n\n{e}\n\nPlease see console output for details.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
        except Exception as qe:
            print(f"Could not show Qt error dialog: {qe}")
        sys.exit(1)

