# -*- coding: utf-8 -*-
# Project: folder_extractor
# Author: ParisNeo with gemini 2.5 (and significant user modifications)
# Description: A PyQt5 application that takes a folder path and generates a Markdown-formatted text representation,
#              including specific file/folder inclusions via an interactive tree, documentation integration,
#              and a custom stylesheet-based UI with theming and threading for intensive tasks.
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
    from PyQt5.QtCore import Qt, QSettings, QSize, QCoreApplication, QModelIndex, QObject, pyqtSignal, QThread, pyqtSlot
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
ASSETS_DIR.mkdir(parents=True, exist_ok=True) # Ensure assets dir exists
THEMES_DIR = SCRIPT_DIR / "themes"
THEMES_DIR.mkdir(parents=True, exist_ok=True) # Ensure themes dir exists
DEFAULT_THEME_FILE = "default_light.qss" 

PATH_ROLE = Qt.UserRole + 1
IS_TEXT_FILE_ROLE = Qt.UserRole + 2
IS_DIR_ROLE = Qt.UserRole + 3

PLACEHOLDERS = {
    "{FOLDER_NAME}": lambda app: Path(app.folder_path_edit.text()).name if app.folder_path_edit and app.folder_path_edit.text() and Path(app.folder_path_edit.text()).exists() else "UnknownProject",
    "{FOLDER_PATH}": lambda app: app.folder_path_edit.text() if app.folder_path_edit else "N/A",
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
    "version": "2.7.1", # Updated version for tabbed UI
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
    "current_theme_file": DEFAULT_THEME_FILE,
    "prompt_templates": [], 
    "loaded_doc_paths": [],
    "checked_tree_paths_str_abs": [],
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
    
    theme_name_guess = name.replace('_', '-') 
    
    if '-' not in theme_name_guess and fallback_theme_name is None: 
        prefixes = ["action-", "document-", "edit-", "go-", "list-", "system-", "view-", "preferences-", "application-", "view-"]
        for prefix in prefixes:
            icon = QIcon.fromTheme(prefix + theme_name_guess)
            if not icon.isNull(): return icon

    icon = QIcon.fromTheme(theme_name_guess) 
    if not icon.isNull():
        return icon
        
    return QIcon()


class ThemeManager:
    def __init__(self, app: QApplication, settings: QSettings, themes_dir: Path, assets_dir: Path, default_theme_file: str):
        self.app = app
        self.settings = settings
        self.themes_dir = themes_dir
        self.assets_dir = assets_dir
        self.default_theme_file = default_theme_file
        self.available_themes: Dict[str, Path] = {} 
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
            default_path = self.themes_dir / self.default_theme_file
            if not default_path.exists():
                 try:
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
        
        if not chosen_path and (self.themes_dir / theme_file_name).exists(): 
            chosen_path = self.themes_dir / theme_file_name
        elif not chosen_path: 
            print(f"Warning: Theme file '{theme_file_name}' not found in available themes. Trying default '{self.default_theme_file}'.")
            theme_file_name = self.default_theme_file
            chosen_path = self.themes_dir / self.default_theme_file

        if chosen_path and chosen_path.exists():
            try:
                qss_content = chosen_path.read_text(encoding="utf-8")
                qss_content = qss_content.replace("{ASSETS_DIR}", self.assets_dir.as_posix())
                
                self.app.setStyleSheet(qss_content)
                self.current_theme_file_name = chosen_path.name 
                self.settings.setValue("currentThemeFileName", self.current_theme_file_name)
                self._update_theme_action_checks()
            except Exception as e:
                print(f"Error applying theme '{chosen_path.name}': {e}")
                if chosen_path.name != self.default_theme_file:
                    self.apply_theme_from_file_name(self.default_theme_file)
        else:
            print(f"Error: Ultimate fallback theme file '{self.default_theme_file}' not found at {self.themes_dir}. Applying basic Qt styling.")
            self.app.setStyleSheet("") 


    def _update_theme_action_checks(self):
        for action in self.theme_actions:
            action_theme_file_name = action.data() 
            if isinstance(action_theme_file_name, str):
                action.setChecked(action_theme_file_name == self.current_theme_file_name)

    def create_theme_menu_actions(self, parent_menu: QMenu):
        self.theme_actions.clear()
        parent_menu.clear()
        sorted_theme_names = sorted(self.available_themes.keys())

        for theme_display_name in sorted_theme_names:
            theme_path = self.available_themes[theme_display_name]
            action = QAction(theme_display_name, self.app.activeWindow(), checkable=True)
            action.setData(theme_path.name) 
            action.triggered.connect(functools.partial(self.apply_theme_from_file_name, theme_path.name))
            self.theme_actions.append(action)
            parent_menu.addAction(action)
        
        self._update_theme_action_checks()

    def get_current_theme_file_name(self) -> str:
        return self.settings.value("currentThemeFileName", self.default_theme_file)


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
        self._root_folder: Path = Path(".") 

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
            self._root_folder = Path(".").resolve() 
        
        self._active_excluded_folders = set(DEFAULT_EXCLUDED_FOLDERS)
        self._active_excluded_extensions = set(DEFAULT_EXCLUDED_EXTENSIONS)
        self._active_excluded_patterns = [] 
        self._active_include_patterns = []  

        collected_preset_patterns: List[str] = []
        for preset_name in selected_preset_names:
            if preset_name in PRESET_EXCLUSIONS:
                collected_preset_patterns.extend(PRESET_EXCLUSIONS[preset_name])
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
        
        if not context_root.is_dir(): 
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
            resolved_item = item.resolve()
            if resolved_item.is_relative_to(context_root):
                 item_relative_path_str = str(resolved_item.relative_to(context_root).as_posix())
            else: 
                item_relative_path_str = item.name 
        except (AttributeError, ValueError): 
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
            resolved_item = item.resolve()
            if resolved_item.is_relative_to(context_root):
                item_rel_path_str = resolved_item.relative_to(context_root).as_posix()
            else:
                item_rel_path_str = item.name 
        except (AttributeError, ValueError): 
            item_rel_path_str = item.name

        for pattern in self._active_include_patterns:
            if fnmatch.fnmatchcase(item_rel_path_str, pattern):
                return True
            
            if item.is_dir() and "/" in item_rel_path_str: 
                try:
                    current_path_obj = Path(item_rel_path_str) 
                    if fnmatch.fnmatchcase(str(current_path_obj), pattern): return True
                    if pattern.endswith("/") and fnmatch.fnmatchcase(str(current_path_obj), pattern[:-1]): return True

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

    def _read_file_content(self, file: Path, for_worker: bool = False) -> str:
        warning_cb = print if for_worker else self.warning_callback
        error_cb = print if for_worker else self.error_callback

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
                        warning_cb(f"File {file.name} decoded using {enc} after UTF-8 failed.")
                        break
                    except UnicodeDecodeError:
                        continue 
                    except Exception as read_err: 
                        warning_cb(f"Error reading file {file.name} with {enc}: {str(read_err)}")
                        return f"[Error reading file: {str(read_err)}]"

                if content is None: 
                    warning_cb(f"Could not decode file {file.name} with tested encodings.")
                    return f"[Error reading file: Could not decode]"
            except Exception as read_err: 
                warning_cb(f"Error reading file {file.name}: {str(read_err)}")
                return f"[Error reading file: {str(read_err)}]"

            lines = content.splitlines()
            if lines and any(len(line) > 5000 for line in lines): 
                warning_cb(f"File {file.name} contains very long lines (>5000 chars). Content included.")
            
            return content if content else "[File appears empty after read]" 
        except OSError as os_err: 
            warning_cb(f"OS error accessing file {file.name}: {str(os_err)}")
            return f"[Error accessing file: {str(os_err)}]"
        except Exception as e: 
            error_cb(f"Unexpected error reading file {file.name}: {str(e)}\n{traceback.format_exc()}")
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
            (print if hasattr(self, 'is_worker_context') and self.is_worker_context else self.warning_callback)(
                f"Error listing directory {current_folder}: {e}"
            )
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

        resolved_root_path = root_path.resolve()
        
        hierarchy: Dict[str, Any] = {} 
        
        all_nodes_to_represent = set()
        for p_raw in selected_paths:
            p = p_raw.resolve() 
            all_nodes_to_represent.add(p)
            try:
                if p.is_relative_to(resolved_root_path) and p != resolved_root_path:
                    relative_p = p.relative_to(resolved_root_path)
                    for i in range(len(relative_p.parts) -1): 
                        parent_path_in_root = resolved_root_path.joinpath(*relative_p.parts[:i+1])
                        all_nodes_to_represent.add(parent_path_in_root)
            except (ValueError, AttributeError): 
                 pass 

        def get_sort_key_for_nodes(x_path: Path):
            try:
                if x_path.is_relative_to(resolved_root_path):
                    return str(x_path.relative_to(resolved_root_path)) 
                return str(x_path) 
            except (ValueError, AttributeError):
                 return str(x_path) 
        
        sorted_nodes = sorted(list(all_nodes_to_represent), key=get_sort_key_for_nodes)

        for node_path_resolved in sorted_nodes: 
            try:
                if node_path_resolved.is_relative_to(resolved_root_path):
                    relative_node_path = node_path_resolved.relative_to(resolved_root_path)
                    parts = relative_node_path.parts
                else: 
                    parts = (node_path_resolved.name,) if node_path_resolved != resolved_root_path else () 
            except (ValueError, AttributeError): 
                parts = (node_path_resolved.name,) if node_path_resolved != resolved_root_path else ()

            current_level = hierarchy
            for i, part in enumerate(parts):
                is_last_part = (i == len(parts) - 1)
                current_level = current_level.setdefault(part, {})
                if is_last_part and node_path_resolved != resolved_root_path : 
                    current_level["_isfile_"] = node_path_resolved.is_file()
        
        if not parts and resolved_root_path in all_nodes_to_represent: 
            hierarchy["_isfile_"] = resolved_root_path.is_file() 


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

        final_tree_lines = [f"{FOLDER_ICON_STR} {resolved_root_path.name}/"] 
        final_tree_lines.extend(format_level(hierarchy, "")) 
        
        return final_tree_lines

    def _generate_file_contents_markdown(self, root_folder: Path, file_paths: List[Path], for_worker:bool=False) -> List[str]:
        content_lines = ["", "---", "", "## File Contents"]
        if not file_paths:
            content_lines.append("\n*No text files selected or included based on filters and size limits.*")
            return content_lines

        resolved_root_folder = root_folder.resolve()

        def get_sort_key(p: Path):
            p_resolved = p.resolve()
            try:
                if p_resolved.is_relative_to(resolved_root_folder):
                    return str(p_resolved.relative_to(resolved_root_folder)).lower()
                return p_resolved.name.lower() 
            except (ValueError, AttributeError): 
                return p_resolved.name.lower()
        
        file_paths.sort(key=get_sort_key)

        for file_path_raw in file_paths:
            file_path = file_path_raw.resolve() 
            try:
                if file_path.is_relative_to(resolved_root_folder):
                    relative_path = file_path.relative_to(resolved_root_folder)
                else:
                    relative_path = Path(file_path.name) 
                    (print if for_worker else self.warning_callback)(
                        f"Could not determine relative path for {file_path} against root {resolved_root_folder}. Using filename only."
                    )
            except (ValueError, AttributeError):
                relative_path = Path(file_path.name)
                (print if for_worker else self.warning_callback)(
                    f"Error getting relative path for {file_path}. Using filename only."
                )

            relative_path_str = str(relative_path).replace("\\", "/") 
            content_lines.append(f"\n### `{relative_path_str}`")
            
            file_content = self._read_file_content(file_path, for_worker=for_worker)
            
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
        selected_file_paths: Optional[List[Path]] = None, 
        for_worker: bool = False 
    ) -> str:
        status_cb = print if for_worker else self.status_callback
        error_cb = print if for_worker else self.error_callback
        
        if not folder_path_str:
            error_cb("No folder path specified.")
            return "```error\nError: No folder path specified.\n```"
        
        try:
            current_root_folder = Path(folder_path_str).resolve() 
            if not current_root_folder.exists():
                error_cb(f"Folder not found: {current_root_folder}")
                return f"```error\nError: Folder not found: {current_root_folder}\n```"
            if not current_root_folder.is_dir():
                error_cb(f"Path is not a directory: {current_root_folder}")
                return f"```error\nError: Path is not a directory: {current_root_folder}\n```"
            self._root_folder = current_root_folder 
        except Exception as e: 
            error_cb(f"Error resolving path '{folder_path_str}': {e}")
            return f"```error\nError resolving path: {e}\n```"

        dynamic_patterns = [p.strip() for p in dynamic_exclude_str.split(',') if p.strip()]
        try:
            self.setup_exclusions_and_limits(
                selected_preset_names, custom_folders_str, custom_exts_str,
                custom_patterns_str, dynamic_patterns, custom_inclusions_str, max_size_mb,
                root_folder_for_context=self._root_folder 
            )
        except Exception as e:
            error_cb(f"Error setting up exclusions/inclusions: {e}\n{traceback.format_exc()}")
            return f"```error\nError setting up filters: {e}\n```"

        status_cb(f"Starting analysis for: {self._root_folder}...")
        tree_lines: List[str]
        found_files_for_content: List[Path]

        if selected_file_paths is not None: 
            status_cb(f"Using {len(selected_file_paths)} items from interactive tree selection.")
            valid_selected_files = []
            for p_raw in selected_file_paths:
                try:
                    p = p_raw.resolve()
                    if p.is_file() and self._is_text_file(p) and p.exists():
                        if p.stat().st_size <= self._max_file_size_bytes:
                            valid_selected_files.append(p)
                    
                except Exception as e:
                    (print if for_worker else self.warning_callback)(f"Skipping invalid path from selection: {p_raw} ({e})")
            
            found_files_for_content = valid_selected_files
            tree_lines = self._generate_tree_markdown_from_paths(self._root_folder, selected_file_paths)
        else: 
            status_cb("Using filter-based selection (interactive tree selection not provided or empty).")
            tree_lines_from_scan, found_files_for_content_from_scan = self._build_filtered_file_list_and_tree(self._root_folder, prefix="")
            tree_lines = [f"{FOLDER_ICON_STR} {self._root_folder.name}/"] + tree_lines_from_scan
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

        content_output_lines = self._generate_file_contents_markdown(self._root_folder, found_files_for_content, for_worker=for_worker)
        
        full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)

        final_prompt_parts = []
        if documentation_prompt and documentation_prompt.strip():
            final_prompt_parts.append("## Imported Documentation\n\n" + documentation_prompt.strip())
        
        if custom_prompt and custom_prompt.strip():
             final_prompt_parts.append("## Custom Instructions\n\n" + custom_prompt.strip())

        if final_prompt_parts:
             full_output += "\n\n---\n\n" + "\n\n---\n\n".join(final_prompt_parts)
        
        status_cb(f"Analysis complete. Included content from {len(found_files_for_content)} text files.")
        return full_output.strip()


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
        self.content_edit.setPlaceholderText("Enter the prompt template content. Use placeholders like {FOLDER_NAME}, {AUTHOR}, {DATE} etc.")
        self.content_edit.setAcceptRichText(False) 
        layout.addWidget(self.content_edit)
        
        ai_placeholders_label = QLabel("Standard AI interaction sequences: [CONFIRM_PLAN], [CONFIRM_FILE: path/to/file.ext]")
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
    def __init__(self, templates: List[Dict[str, str]], parent=None): 
        super().__init__(parent)
        self.templates = templates 
        self.parent_app = parent 
        
        self.setWindowTitle("Manage Prompt Templates")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        main_layout = QHBoxLayout(self)
        
        left_layout = QVBoxLayout()
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

        right_layout = QVBoxLayout()
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
            item_text = template.get('name', f'Unnamed Template {i+1}')
            item = QListWidgetItem(item_text)
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
        else:
            self.preview_edit.clear()

    def get_current_template_names(self) -> List[str]: 
        return [t.get('name', '') for t in self.templates]

    def add_template(self):
        dialog = EditTemplateDialog(existing_names=self.get_current_template_names(), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_template = {"name": dialog.get_template_name(), "content": dialog.get_template_content()}
            self.templates.append(new_template)
            self.populate_list() 
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() == new_template["name"]:
                    self.list_widget.setCurrentItem(item); break
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
            updated_template_data = {"name": dialog.get_template_name(), "content": dialog.get_template_content()}
            self.templates[original_template_index] = updated_template_data 
            self.populate_list() 
            for i in range(self.list_widget.count()):
                list_item = self.list_widget.item(i)
                if list_item.text() == updated_template_data["name"]: 
                    self.list_widget.setCurrentItem(list_item); break
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
            self.templates[:] = [t for t in self.templates if t.get('name') != item_to_remove_text]
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
        
        new_template = {"name": new_name, "content": original_template.get('content', '')}
        self.templates.append(new_template)
        self.populate_list() 
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item.text() == new_name:
                self.list_widget.setCurrentItem(list_item); break
        if self.parent_app: self.parent_app.show_status(f"Template copied as '{new_name}'.")

    def get_updated_templates(self) -> List[Dict[str, str]]:
        return self.templates


class ProjectExplorerTab(QWidget): # Renamed from FileSelectionTab
    class FileTreePopulationWorker(QObject):
        tree_data_ready = pyqtSignal(list) 
        error_occurred = pyqtSignal(str)
        finished = pyqtSignal()

        def __init__(self, root_path: Path, processor: FolderProcessor, filter_settings: dict):
            super().__init__()
            self.root_path = root_path
            self.processor = processor 
            self.filter_settings = filter_settings 

        @pyqtSlot()
        def run(self):
            try:
                dynamic_patterns_list = [
                    p.strip() for p in self.filter_settings.get("dynamic_patterns", "").split(',') if p.strip()
                ]
                self.processor.setup_exclusions_and_limits(
                    self.filter_settings.get("selected_presets", []),
                    self.filter_settings.get("custom_folders", ""),
                    self.filter_settings.get("custom_extensions", ""),
                    self.filter_settings.get("custom_patterns", ""),
                    dynamic_patterns_list, 
                    self.filter_settings.get("custom_inclusions", ""),
                    self.filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB),
                    root_folder_for_context=self.root_path
                )
                data = self._collect_tree_data_recursive(self.root_path, self.root_path)
                self.tree_data_ready.emit(data)
            except Exception as e:
                self.error_occurred.emit(f"Error collecting tree data: {e}\n{traceback.format_exc()}")
            finally:
                self.finished.emit()

        def _collect_tree_data_recursive(self, current_dir_path: Path, root_scan_path: Path) -> List[Dict[str, Any]]:
            items_data = []
            try:
                paths_in_dir = sorted(
                    list(current_dir_path.iterdir()),
                    key=lambda x: (x.is_file(), x.name.lower())
                )
            except (PermissionError, OSError) as e:
                items_data.append({
                    "name": f"[{'Permission Denied' if isinstance(e, PermissionError) else 'OS Error'}: {current_dir_path.name}]",
                    "path": current_dir_path, "is_dir": True, "is_text": False, 
                    "icon_type": "error", "check_state": Qt.Unchecked, "children": [], "error": True, "disabled": True
                })
                return items_data

            for path_obj in paths_in_dir:
                item_name = path_obj.name
                is_dir = path_obj.is_dir()
                
                is_excluded = self.processor._is_excluded(path_obj, root_scan_path)
                is_included_by_filter = self.processor._is_included_by_filter(path_obj, root_scan_path)
                
                item_data: Dict[str, Any] = {
                    "name": item_name, "path": path_obj, "is_dir": is_dir,
                    "children": [], "error": False, "disabled": False
                }

                can_be_checked = False
                should_be_checked_initially = False

                if is_dir:
                    item_data["icon_type"] = "folder"
                    item_data["is_text"] = False 
                    can_be_checked = True 
                    if not is_excluded and is_included_by_filter:
                        should_be_checked_initially = True 
                    item_data["children"] = self._collect_tree_data_recursive(path_obj, root_scan_path)
                else: 
                    is_text = self.processor._is_text_file(path_obj)
                    item_data["is_text"] = is_text
                    item_data["icon_type"] = "text" if is_text else "binary"
                    if is_text:
                        can_be_checked = True
                        if not is_excluded and is_included_by_filter:
                            try:
                                if path_obj.stat().st_size <= self.processor._max_file_size_bytes:
                                    should_be_checked_initially = True
                            except OSError: 
                                should_be_checked_initially = False 
                    else: 
                        can_be_checked = False 
                
                item_data["check_state"] = Qt.Checked if should_be_checked_initially and can_be_checked else Qt.Unchecked
                item_data["disabled"] = not can_be_checked 
                
                items_data.append(item_data)
            return items_data

    def __init__(self, app_instance: 'FolderStructureApp', parent=None):
        super().__init__(parent)
        self.app = app_instance 
        self.processor = app_instance.processor 
        self._is_updating_checks = False 
        self._is_populating_model = False 
        self.current_tree_population_thread: Optional[QThread] = None
        self.current_tree_worker: Optional[ProjectExplorerTab.FileTreePopulationWorker] = None

        self.folder_icon = load_icon("folder", "folder")
        self.file_icon = load_icon("text-x-generic", "text-x-generic") 
        self.binary_file_icon = load_icon("application-octet-stream", "application-octet-stream")
        self.error_icon = load_icon("dialog-error", "dialog-error")

        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(5,5,5,5) 

        # Project Folder selection is now in Tab 1 (Setup & Filters)

        self.main_splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)

        tree_controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton(load_icon("view-refresh", "view-refresh"), " Refresh Tree")
        self.refresh_button.setToolTip("Reloads the tree based on current folder and filter settings (from Tab 1)")
        self.refresh_button.clicked.connect(self.start_populate_tree_worker) 
        self.expand_all_button = QPushButton("Expand All")
        self.expand_all_button.clicked.connect(lambda: self.tree_view.expandAll())
        self.collapse_all_button = QPushButton("Collapse All")
        self.collapse_all_button.clicked.connect(lambda: self.tree_view.collapseAll())
        
        self.check_all_text_button = QPushButton("Check All Text")
        self.check_all_text_button.clicked.connect(self.check_all_text_files)
        self.uncheck_all_button = QPushButton("Uncheck All")
        self.uncheck_all_button.clicked.connect(self.uncheck_all_files)

        tree_controls_layout.addWidget(self.refresh_button)
        tree_controls_layout.addWidget(self.expand_all_button)
        tree_controls_layout.addWidget(self.collapse_all_button)
        tree_controls_layout.addStretch(1)
        tree_controls_layout.addWidget(self.check_all_text_button)
        tree_controls_layout.addWidget(self.uncheck_all_button)
        left_layout.addLayout(tree_controls_layout)

        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['Name'])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.header().setSectionResizeMode(QHeaderView.Stretch) 
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        self.tree_view.setIndentation(15) 
        self.tree_view.setAlternatingRowColors(True)
        self.tree_model.itemChanged.connect(self.on_item_changed)
        left_layout.addWidget(self.tree_view)
        
        self.main_splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5,5,5,5) 

        prompt_group = QGroupBox("Custom Instructions Prompt")
        prompt_group_layout = QVBoxLayout(prompt_group)
        
        prompt_template_layout = QHBoxLayout()
        prompt_template_layout.addWidget(QLabel("Template:"))
        self.app.template_combo = QComboBox() 
        self.app.template_combo.setToolTip("Select a saved prompt template")
        self.app.template_combo.addItem("-- Select Template --") 
        
        load_template_button = QPushButton(load_icon("document-open", "document-open"), " Load")
        load_template_button.setToolTip("Load selected template into the text area below")
        load_template_button.clicked.connect(self.app.load_selected_template) 
        
        save_template_button = QPushButton(load_icon("document-save-as", "document-save-as"), " Save As...")
        save_template_button.setToolTip("Save the current text below as a new template")
        save_template_button.clicked.connect(self.app.save_template_as) 

        manage_template_button = QPushButton(load_icon("document-properties", "preferences-other"), " Manage...")
        manage_template_button.setToolTip("Add, edit, remove, or copy prompt templates")
        manage_template_button.clicked.connect(self.app.manage_prompt_templates) 

        prompt_template_layout.addWidget(self.app.template_combo, 1) 
        prompt_template_layout.addWidget(load_template_button)
        prompt_template_layout.addWidget(save_template_button)
        prompt_template_layout.addWidget(manage_template_button)
        prompt_group_layout.addLayout(prompt_template_layout)

        self.app.custom_prompt_edit = QTextEdit() 
        self.app.custom_prompt_edit.setPlaceholderText("Enter instructions for an AI, or load a template. Placeholders like {FOLDER_NAME} will be substituted. Imported documentation will be added above this.")
        self.app.custom_prompt_edit.setAcceptRichText(False)
        self.app.custom_prompt_edit.setMinimumHeight(120) 
        prompt_group_layout.addWidget(self.app.custom_prompt_edit)
        right_layout.addWidget(prompt_group)
        
        right_layout.addStretch(1) 

        self.app.generate_button = QPushButton(load_icon("system-run", "media-playback-start"), " Generate Structure Text")
        self.app.generate_button.setToolTip("Analyze selection and generate the output")
        self.app.generate_button.clicked.connect(self.app.start_generate_structure_worker) 
        self.app.generate_button.setFixedHeight(35)
        right_layout.addWidget(self.app.generate_button, 0, Qt.AlignBottom | Qt.AlignHCenter)
        
        self.main_splitter.addWidget(right_widget)
        self.main_splitter.setSizes([300, 200]) 

        tab_layout.addWidget(self.main_splitter)


    def start_populate_tree_worker(self):
        if self.current_tree_population_thread and self.current_tree_population_thread.isRunning():
            self.app.show_warning("Tree population is already in progress.")
            return

        # Folder path is now taken from app.folder_path_edit (on Tab 1)
        root_folder_str = self.app.folder_path_edit.text() if self.app.folder_path_edit else ""
        if not root_folder_str or not Path(root_folder_str).is_dir():
            # This button (Refresh Tree in Tab 2) should ideally only be active if a tree is loaded.
            # If somehow clicked when no valid folder is set in Tab 1, warn.
            self.app.show_warning("Cannot populate tree: Valid project folder not set in 'Project & Filters' tab.")
            self.tree_model.clear() 
            self.tree_model.setHorizontalHeaderLabels(['Name'])
            return

        self.refresh_button.setEnabled(False)
        # Status update will be handled by app.trigger_tree_population or directly in start_populate_tree_worker
        # self.app.show_status(f"Populating tree for {Path(root_folder_str).name}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.tree_model.clear() 
        self.tree_model.setHorizontalHeaderLabels(['Name'])

        current_filter_settings = self.app.get_settings_from_ui_for_filters()

        self.current_tree_worker = ProjectExplorerTab.FileTreePopulationWorker(
            Path(root_folder_str).resolve(),
            self.processor, 
            current_filter_settings 
        )
        self.current_tree_population_thread = QThread()
        self.current_tree_worker.moveToThread(self.current_tree_population_thread)

        self.current_tree_worker.tree_data_ready.connect(self._build_tree_model_from_data)
        self.current_tree_worker.error_occurred.connect(self._on_tree_population_error)
        self.current_tree_worker.finished.connect(self._on_tree_population_finished_from_tab_worker) # Renamed signal handler
        
        self.current_tree_population_thread.started.connect(self.current_tree_worker.run)
        self.current_tree_population_thread.start()

    def _on_tree_population_error(self, error_message: str):
        self.app.show_error(f"Tree Population Error: {error_message}")
        if not (self.current_tree_population_thread and self.current_tree_population_thread.isRunning()):
             self._on_tree_population_finished_from_tab_worker(success=False) # Call with success=False


    def _on_tree_population_finished_from_tab_worker(self, success: bool = True): # Modified to accept success status
        QApplication.restoreOverrideCursor()
        self.refresh_button.setEnabled(True)
        
        if self.current_tree_population_thread:
            if self.current_tree_population_thread.isRunning():
                self.current_tree_population_thread.quit()
                self.current_tree_population_thread.wait(1000) 
            self.current_tree_population_thread.deleteLater() 
            self.current_tree_population_thread = None
        if self.current_tree_worker:
            self.current_tree_worker.deleteLater()
            self.current_tree_worker = None
        
        # This method is now primarily for cleaning up the worker/thread from this tab's perspective.
        # The main app's _on_project_tree_load_finished handles tab enabling and status.
        self.app._on_project_tree_load_finished(success) # Notify the main app


    def _build_tree_model_from_data(self, tree_items_data: List[Dict[str, Any]]):
        if self._is_populating_model: return 
        self._is_populating_model = True
        
        try: 
            self.tree_model.itemChanged.disconnect(self.on_item_changed)
        except TypeError: pass 

        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(['Name'])
        
        root_item = self.tree_model.invisibleRootItem()
        for item_data in tree_items_data:
            self._add_item_to_model_recursive(root_item, item_data)
        
        self._is_updating_checks = True 
        try:
            for i in range(root_item.rowCount()):
                top_level_item = root_item.child(i)
                if top_level_item and top_level_item.data(IS_DIR_ROLE):
                    self._update_all_parent_states_recursive(top_level_item) 
        finally:
            self._is_updating_checks = False

        # Status update is now handled by the main app after successful tree load
        # self.app.show_status("File tree model populated.")
        try: 
            self.tree_model.itemChanged.connect(self.on_item_changed)
        except TypeError: 
            pass 
        
        self._is_populating_model = False


    def _add_item_to_model_recursive(self, parent_q_item: QStandardItem, item_data: Dict[str, Any]):
        q_item = QStandardItem(item_data["name"])
        q_item.setEditable(False)
        q_item.setData(item_data["path"], PATH_ROLE)
        q_item.setData(item_data["is_dir"], IS_DIR_ROLE)
        q_item.setData(item_data.get("is_text", False), IS_TEXT_FILE_ROLE)

        if item_data.get("error", False):
            q_item.setIcon(self.error_icon)
            q_item.setCheckable(False) 
            q_item.setForeground(QColor("red")) 
            q_item.setEnabled(False) 
        else:
            icon_type = item_data.get("icon_type", "binary" if not item_data["is_dir"] else "folder")
            if icon_type == "folder": q_item.setIcon(self.folder_icon)
            elif icon_type == "text": q_item.setIcon(self.file_icon)
            else: q_item.setIcon(self.binary_file_icon)

            if item_data.get("disabled", False): 
                q_item.setCheckable(False)
                q_item.setEnabled(False) 
                q_item.setCheckState(Qt.Unchecked)
            else: 
                q_item.setCheckable(True)
                q_item.setCheckState(item_data.get("check_state", Qt.Unchecked))
        
        parent_q_item.appendRow(q_item)

        if item_data["is_dir"] and item_data["children"]:
            for child_data in item_data["children"]:
                self._add_item_to_model_recursive(q_item, child_data)
    
    def on_item_changed(self, item: QStandardItem):
        if self._is_updating_checks or self._is_populating_model:
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
            if parent and parent != self.tree_model.invisibleRootItem(): 
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
                if child_item.checkState() != state: 
                    child_item.setCheckState(state) 
    
    def _update_parent_check_state_from_children(self, parent_item: QStandardItem):
        if not parent_item or parent_item == self.tree_model.invisibleRootItem() or not parent_item.isCheckable():
            return 

        num_children = parent_item.rowCount()
        if num_children == 0:
            if parent_item.checkState() == Qt.PartiallyChecked:
                parent_item.setCheckState(Qt.Unchecked) 
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
        if checkable_enabled_children == 0 : 
             pass 
        elif checked_children == checkable_enabled_children : 
            new_parent_state = Qt.Checked
        elif checked_children > 0 or partially_checked_children > 0: 
            new_parent_state = Qt.PartiallyChecked
        
        if parent_item.checkState() != new_parent_state: 
             parent_item.setCheckState(new_parent_state)
        
        grandparent = parent_item.parent()
        if grandparent and grandparent != self.tree_model.invisibleRootItem(): 
            self._update_parent_check_state_from_children(grandparent) 


    def get_selected_file_paths(self) -> List[Path]:
        selected_paths: List[Path] = []
        def recurse_items(parent_item: Union[QStandardItem, QStandardItemModel]):
            num_rows = parent_item.rowCount() if isinstance(parent_item, QStandardItemModel) else parent_item.rowCount()
            
            for row in range(num_rows):
                item = parent_item.item(row) if isinstance(parent_item, QStandardItemModel) else parent_item.child(row)
                
                if item:
                    path_obj = item.data(PATH_ROLE)
                    if path_obj and item.isCheckable() and item.isEnabled() and item.checkState() != Qt.Unchecked:
                        selected_paths.append(path_obj)
                    
                    if item.hasChildren() and item.data(IS_DIR_ROLE) and item.checkState() != Qt.Unchecked:
                         recurse_items(item) 
        
        recurse_items(self.tree_model.invisibleRootItem())
        
        unique_paths = sorted(list(set(selected_paths)), key=lambda p: str(p.resolve()))
        return unique_paths

    def _set_all_checks(self, state: Qt.CheckState, only_text_files: bool = False):
        if self._is_populating_model: return

        try: 
            self.tree_model.itemChanged.disconnect(self.on_item_changed)
        except TypeError: pass 
        
        self._is_updating_checks = True 
        try:
            for i in range(self.tree_model.rowCount()):
                item = self.tree_model.item(i)
                self._set_item_check_recursive(item, state, only_text_files)
            
            for i in range(self.tree_model.rowCount()):
                top_item = self.tree_model.item(i)
                if top_item and top_item.data(IS_DIR_ROLE): 
                    self._update_all_parent_states_recursive(top_item)
        finally:
            self._is_updating_checks = False 
            try: 
                self.tree_model.itemChanged.connect(self.on_item_changed)
            except TypeError: pass 

    def _set_item_check_recursive(self, item: QStandardItem, state: Qt.CheckState, only_text_files: bool):
        if not item: return

        is_dir = item.data(IS_DIR_ROLE)
        is_text = item.data(IS_TEXT_FILE_ROLE) if not is_dir else False 
        
        apply_state = False
        if item.isCheckable() and item.isEnabled(): 
            if only_text_files:
                if is_dir: apply_state = True 
                elif is_text: apply_state = True
            else: 
                apply_state = True
        
        if apply_state and item.checkState() != state : 
            item.setCheckState(state)

        if is_dir:
            for row in range(item.rowCount()):
                self._set_item_check_recursive(item.child(row), state, only_text_files)

    def _update_all_parent_states_recursive(self, item: QStandardItem):
        if not item or not item.data(IS_DIR_ROLE): return 

        for row in range(item.rowCount()):
            child = item.child(row)
            if child and child.data(IS_DIR_ROLE): 
                self._update_all_parent_states_recursive(child) 
        
        self._update_parent_check_state_from_children(item)


    def check_all_text_files(self):
        self.app.show_status("Checking all text files in tree...")
        self._set_all_checks(Qt.Checked, only_text_files=True)
        self.app.show_status("All text files checked.")

    def uncheck_all_files(self):
        self.app.show_status("Unchecking all items in tree...")
        self._set_all_checks(Qt.Unchecked) 
        self.app.show_status("All items unchecked.")

    def apply_explicit_checks(self, paths_to_check_str_abs: List[str]):
        if self._is_populating_model:
            self.app.show_warning("Cannot apply explicit checks while model is populating.")
            return

        self.app.show_status("Applying explicit check states from saved environment...")
        
        try:
            self.tree_model.itemChanged.disconnect(self.on_item_changed)
        except TypeError: pass
        self._is_updating_checks = True

        try:
            paths_set_to_check = {Path(p_str) for p_str in paths_to_check_str_abs}

            def set_checks_based_on_list(parent_q_item_or_model: Union[QStandardItem, QStandardItemModel]):
                is_model_root = isinstance(parent_q_item_or_model, QStandardItemModel)
                num_rows = parent_q_item_or_model.rowCount()

                for r in range(num_rows):
                    child_q_item = parent_q_item_or_model.item(r) if is_model_root else parent_q_item_or_model.child(r, 0) 
                    if not child_q_item: continue

                    if not child_q_item.isCheckable() or not child_q_item.isEnabled():
                        if child_q_item.hasChildren() and child_q_item.data(IS_DIR_ROLE):
                            set_checks_based_on_list(child_q_item) 
                        continue
                    
                    item_path_obj = child_q_item.data(PATH_ROLE)
                    new_state = Qt.Unchecked 

                    if item_path_obj:
                        resolved_item_path = item_path_obj.resolve()
                        if resolved_item_path in paths_set_to_check:
                            new_state = Qt.Checked
                    
                    if child_q_item.checkState() != new_state:
                        child_q_item.setCheckState(new_state)
                    
                    if child_q_item.hasChildren() and child_q_item.data(IS_DIR_ROLE):
                        set_checks_based_on_list(child_q_item)

            set_checks_based_on_list(self.tree_model.invisibleRootItem())

            for i in range(self.tree_model.invisibleRootItem().rowCount()):
                top_level_item = self.tree_model.invisibleRootItem().child(i)
                if top_level_item and top_level_item.data(IS_DIR_ROLE):
                    self._update_all_parent_states_recursive(top_level_item)
            
            self.app.show_status("Explicit check states applied.")

        except Exception as e:
            self.app.show_error(f"Error applying explicit checks: {e}\n{traceback.format_exc()}")
        finally:
            self._is_updating_checks = False
            try:
                self.tree_model.itemChanged.connect(self.on_item_changed)
            except TypeError: pass


class FolderStructureApp(QMainWindow):
    class StructureGenerationWorker(QObject):
        generation_complete = pyqtSignal(str) 
        generation_error = pyqtSignal(str)    
        finished = pyqtSignal()              

        def __init__(self, processor: FolderProcessor, settings: dict, selected_paths: Optional[List[Path]], final_prompt: str, doc_content: str):
            super().__init__()
            self.processor = processor
            self.settings = settings
            self.selected_paths = selected_paths
            self.final_prompt = final_prompt
            self.doc_content = doc_content

        @pyqtSlot()
        def run(self):
            try:
                generated_text = self.processor.generate_structure_text(
                    self.settings["folder_path"],
                    self.settings.get("selected_presets", []), 
                    self.settings.get("custom_folders", ""),
                    self.settings.get("custom_extensions", ""),
                    self.settings.get("custom_patterns", ""),
                    self.settings.get("dynamic_patterns", ""), 
                    self.settings.get("custom_inclusions", ""), 
                    self.settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB),
                    self.final_prompt,
                    self.doc_content,
                    selected_file_paths=self.selected_paths,
                    for_worker=True 
                )
                self.generation_complete.emit(generated_text)
            except Exception as e:
                self.generation_error.emit(f"Error during structure generation: {e}\n{traceback.format_exc()}")
            finally:
                self.finished.emit()

    def __init__(self):
        super().__init__()
        QCoreApplication.setOrganizationName("AICodeHelper")
        QCoreApplication.setApplicationName("FolderStructureAppV2.7.1") # Updated for tabbed UI
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

        self.current_generation_thread: Optional[QThread] = None
        self.current_generation_worker: Optional[FolderStructureApp.StructureGenerationWorker] = None
        
        self.pending_tree_checks: Optional[List[str]] = None 

        # UI elements that are initialized in _create_settings_tab_content or ProjectExplorerTab
        self.folder_path_edit: Optional[QLineEdit] = None
        self.load_tree_button: Optional[QPushButton] = None # New button in Tab 1
        self.project_explorer_tab: Optional[ProjectExplorerTab] = None # Renamed

        self.custom_prompt_edit: Optional[QTextEdit] = None # In ProjectExplorerTab
        self.template_combo: Optional[QComboBox] = None # In ProjectExplorerTab
        self.generate_button: Optional[QPushButton] = None # In ProjectExplorerTab


        self.initUI() 
        self.load_persistent_settings() 
        
        self.create_actions()
        self.create_menus() 
        self.create_status_bar()

        self._update_recent_menu() 
        self._update_template_combo() 
        self._update_doc_list_widget() 
        
        initial_theme_file = self.theme_manager.get_current_theme_file_name()
        self.theme_manager.apply_theme_from_file_name(initial_theme_file)

        self.load_initial_environment()
        self.show_status("Ready. Select project folder and filters, then load project tree.")
    
    def show_status(self, message: str):
        self.statusBar().showMessage(message, 7000) 
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
        self.setWindowTitle(f'Folder Structure to Text v{DEFAULT_SETTINGS["version"]}') 
        self.setGeometry(100, 100, 1200, 900) 
        self.setWindowIcon(load_icon("application-x-executable", "application-x-executable")) 

        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)

        # Tab 1: Project Setup & Filters
        settings_filters_widget = QWidget()
        settings_filters_widget.setObjectName("ProjectSetupFiltersTabWidget") 
        settings_filters_outer_layout = QVBoxLayout(settings_filters_widget)
        settings_filters_outer_layout.setSpacing(10)
        self._create_project_setup_filters_tab_content(settings_filters_outer_layout) 
        self.main_tabs.addTab(settings_filters_widget, load_icon("preferences-system", "preferences-system"), "1. Project & Filters")
        self.project_setup_filters_tab_index = 0 # Store index

        # Tab 2: Project Explorer & Prompt
        self.project_explorer_tab = ProjectExplorerTab(self) 
        self.project_explorer_tab.setObjectName("ProjectExplorerPromptTabWidget")
        self.main_tabs.addTab( self.project_explorer_tab, load_icon("edit-select-all", "edit-select-all"), "2. Explorer & Prompt")
        self.project_explorer_tab_index = 1 # Store index

        # Tab 3: Output
        output_widget = QWidget()
        output_widget.setObjectName("OutputTabWidget") 
        output_layout = QVBoxLayout(output_widget)
        output_layout.setSpacing(10)
        self._create_output_tab_content(output_layout)
        self.main_tabs.addTab(output_widget, load_icon("text-x-generic", "text-x-generic"), "3. Output")
        self.output_tab_index = 2 # Store index
        
        # Initially disable Tab 2 and Tab 3
        self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
        self.main_tabs.setTabEnabled(self.output_tab_index, False)

        # Connect folder path textChanged for dynamic tab disabling
        if self.folder_path_edit:
            self.folder_path_edit.textChanged.connect(self._on_folder_path_manually_changed)


    def _create_project_setup_filters_tab_content(self, layout: QVBoxLayout):
        # Top: Folder path and Load Tree button
        project_load_group = QGroupBox("Target Project")
        project_load_layout = QVBoxLayout(project_load_group)

        folder_path_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("Select or enter the target folder path...")
        self.folder_path_edit.textChanged.connect(self._handle_folder_change_for_title) # For window title only
        browse_button = QPushButton(load_icon("folder-open", "document-open"), " Browse...")
        browse_button.setToolTip("Select the root folder of the project")
        browse_button.clicked.connect(self.browse_folder)
        folder_path_layout.addWidget(self.folder_path_edit, 1)
        folder_path_layout.addWidget(browse_button)
        project_load_layout.addLayout(folder_path_layout)

        self.load_tree_button = QPushButton(load_icon("view-process-tree", "view-process-tree"), " Load Project Tree")
        self.load_tree_button.setToolTip("Load the project's file tree based on the path above and filters below.")
        self.load_tree_button.clicked.connect(self.trigger_tree_population)
        self.load_tree_button.setFixedHeight(35)
        project_load_layout.addWidget(self.load_tree_button, 0, Qt.AlignCenter)
        layout.addWidget(project_load_group)

        # Filters in a scroll area
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
        custom_group = QGroupBox("Custom Filtering Rules (Comma-separated, for initial tree state & non-tree generation)")
        custom_form_layout = QFormLayout(custom_group) 
        self.custom_folders_edit = QLineEdit()
        self.custom_folders_edit.setPlaceholderText("e.g., docs,tests,temp (excluded folder names)")
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText("e.g., .log,.tmp,.bak (excluded extensions)")
        self.custom_patterns_edit = QLineEdit()
        self.custom_patterns_edit.setPlaceholderText("e.g., *.log,temp_*,cache_*/ (excluded glob patterns)")
        self.dynamic_exclude_edit = QLineEdit() 
        self.dynamic_exclude_edit.setPlaceholderText("e.g., *.private,credentials.json (additional tree exclusion patterns)")
        self.custom_inclusions_edit = QLineEdit()
        self.custom_inclusions_edit.setPlaceholderText("e.g., src/main/, README.md, docs/*.md (inclusion patterns for tree)")
        
        custom_form_layout.addRow("Exclude Folders (Names):", self.custom_folders_edit)
        custom_form_layout.addRow("Exclude Extensions:", self.custom_extensions_edit)
        custom_form_layout.addRow("Exclude Patterns (Glob):", self.custom_patterns_edit)
        custom_form_layout.addRow("More Exclude Patterns (Tree):", self.dynamic_exclude_edit)
        custom_form_layout.addRow("Include Paths/Patterns (Tree):", self.custom_inclusions_edit)
        custom_filter_layout.addWidget(custom_group)
        self.settings_toolbox.addItem(custom_filter_widget, load_icon("view-filter", "system-search"), "Custom Filtering (Initial Tree State)")

        options_widget = QWidget()
        options_layout = QFormLayout(options_widget) 
        options_layout.setContentsMargins(9,9,9,9)
        self.max_size_spinbox = QDoubleSpinBox()
        self.max_size_spinbox.setSuffix(" MB")
        self.max_size_spinbox.setMinimum(0.01); self.max_size_spinbox.setMaximum(500.0) 
        self.max_size_spinbox.setSingleStep(0.1); self.max_size_spinbox.setValue(DEFAULT_MAX_FILE_SIZE_MB)
        self.save_output_checkbox = QCheckBox("Save Markdown output automatically on Generate")
        options_layout.addRow("Max File Size (for Content):", self.max_size_spinbox)
        options_layout.addRow(self.save_output_checkbox) 
        self.settings_toolbox.addItem(options_widget, load_icon("preferences-desktop-display", "video-display"), "Generation Options")

        doc_integration_widget = QWidget()
        doc_layout = QVBoxLayout(doc_integration_widget)
        doc_layout.setContentsMargins(9,9,9,9)
        doc_layout.addWidget(QLabel("Import Markdown/Text documentation files (appended to prompt):"))
        self.doc_list_widget = QListWidget()
        self.doc_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) 
        self.doc_list_widget.setToolTip("Content of these files will be added to the AI prompt before custom instructions.")
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

    def _on_folder_path_manually_changed(self):
        # If folder path is changed in Tab 1 after a tree was loaded (Tab 2 enabled)
        if self.main_tabs.isTabEnabled(self.project_explorer_tab_index):
            self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
            self.main_tabs.setTabEnabled(self.output_tab_index, False)
            if self.project_explorer_tab:
                self.project_explorer_tab.tree_model.clear()
                self.project_explorer_tab.tree_model.setHorizontalHeaderLabels(['Name'])
            
            self.show_status("Project folder changed. Click 'Load Project Tree' to update.")
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index) # Switch back to Tab 1
            if self.load_tree_button: self.load_tree_button.setEnabled(True) # Ensure load button is re-enabled


    def trigger_tree_population(self):
        if not self.folder_path_edit or not self.load_tree_button or not self.project_explorer_tab:
            self.show_error("UI components not fully initialized. Cannot load tree.")
            return

        folder_path_str = self.folder_path_edit.text()
        if not folder_path_str or not Path(folder_path_str).is_dir():
            self.show_warning("Please select a valid project folder first.")
            self.browse_folder() # Prompt to select
            # Re-check after browse
            folder_path_str = self.folder_path_edit.text()
            if not folder_path_str or not Path(folder_path_str).is_dir():
                return # Still no valid folder

        self.load_tree_button.setEnabled(False)
        self.show_status(f"Loading project tree for: {Path(folder_path_str).name}...")
        
        # Disable other tabs while loading tree
        self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
        self.main_tabs.setTabEnabled(self.output_tab_index, False)
        
        # The ProjectExplorerTab's worker will handle actual population and signaling
        self.project_explorer_tab.start_populate_tree_worker()

    def _on_project_tree_load_finished(self, success: bool):
        """Called by ProjectExplorerTab's worker when tree population is done."""
        if self.load_tree_button: self.load_tree_button.setEnabled(True)

        if success:
            self.main_tabs.setTabEnabled(self.project_explorer_tab_index, True)
            self.main_tabs.setCurrentIndex(self.project_explorer_tab_index)
            self.show_status("Project tree loaded. Select files and configure prompt on Tab 2.")

            # Apply pending checks if any (e.g., from a loaded environment)
            if self.project_explorer_tab and self.pending_tree_checks is not None:
                self.project_explorer_tab.apply_explicit_checks(self.pending_tree_checks)
                self.pending_tree_checks = None # Clear after applying
                self.show_status("Saved tree selection applied. Configure prompt on Tab 2.")
        else:
            self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
            # Status already set by error handler in ProjectExplorerTab or by show_error
            self.show_error("Failed to load project tree. Check folder path and filter settings on Tab 1.")
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)


    def create_actions(self):
        self.new_project_action = QAction(load_icon("document-new", "document-new"), "&New Project", self, shortcut="Ctrl+N", statusTip="Clear folder path and start new analysis (keeps current settings)", triggered=self.new_project)
        self.load_env_action = QAction(load_icon("document-open", "document-open"), "&Load Environment...", self, shortcut="Ctrl+L", statusTip="Load configuration from a JSON file", triggered=self.load_environment_dialog)
        self.save_env_action = QAction(load_icon("document-save", "document-save"), "&Save Environment", self, shortcut="Ctrl+S", statusTip="Save current configuration to the current file", triggered=self.save_current_environment)
        self.save_env_as_action = QAction(load_icon("document-save-as", "document-save-as"), "Save Environment &As...", self, shortcut="Ctrl+Shift+S", statusTip="Save current configuration to a new JSON file", triggered=self.save_environment_as)
        self.manage_recent_action = QAction(load_icon("document-open-recent", "document-open-recent"), "&Manage Recent Environments...", self, statusTip="View and remove recent environment files", triggered=self.manage_recent_environments)
        self.exit_action = QAction(load_icon("application-exit", "application-exit"), "E&xit", self, shortcut="Ctrl+Q", statusTip="Exit the application", triggered=self.close)
        
        self.reset_settings_action = QAction(load_icon("view-refresh", "view-refresh"), "&Reset All Settings", self, shortcut="Ctrl+R", statusTip="Reset all settings to their defaults", triggered=self.reset_settings)
        self.clear_output_action = QAction(load_icon("edit-clear", "edit-clear-all"), "&Clear Output Area", self, shortcut="Ctrl+Shift+C", statusTip="Clear the output text area", triggered=self.clear_output)

        self.save_env_action.setEnabled(self.current_environment_file is not None)

    def create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.load_env_action)
        self.recent_env_menu = file_menu.addMenu(load_icon("document-open-recent", "document-open-recent"), "Load Recent Environment")
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
        self.themes_menu = view_menu.addMenu(load_icon("preferences-desktop-theme", "preferences-desktop-theme"), "&Themes")
        self.theme_manager.create_theme_menu_actions(self.themes_menu) 

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def browse_folder(self):
        if not self.folder_path_edit: return

        start_dir = self.settings.value("lastBrowseDir", str(Path.home()))
        current_path = self.folder_path_edit.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", current_path or start_dir)
        if folder:
            self.folder_path_edit.setText(folder) # This will trigger textChanged
            self.settings.setValue("lastBrowseDir", folder)
            self.show_status(f"Selected folder: {folder}. Configure filters and click 'Load Project Tree'.")
            # Tree population is now explicitly triggered by "Load Project Tree" button

    def new_project(self):
        confirm = QMessageBox.question(
            self, "New Project", 
            "Clear the target folder path, output, and interactive tree selection?\n"
            "Disconnect current environment file (if any)?\n\n"
            "Current exclusion, inclusion, prompt, documentation, and other settings will be kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if confirm == QMessageBox.Yes:
            if self.folder_path_edit: self.folder_path_edit.clear()
            self.clear_output() 
            if self.project_explorer_tab:
                self.project_explorer_tab.tree_model.clear()
                self.project_explorer_tab.tree_model.setHorizontalHeaderLabels(['Name'])
            
            # Disable Tab 2 and Tab 3, enable Tab 1
            self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
            self.main_tabs.setTabEnabled(self.output_tab_index, False)
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)
            if self.load_tree_button: self.load_tree_button.setEnabled(True)


            self.current_environment_file = None
            self.save_env_action.setEnabled(False)
            self._update_window_title()
            self.show_status("Project cleared. Select folder and filters, then load project tree.")
            if self.folder_path_edit: self.folder_path_edit.setFocus()


    def clear_output(self):
        self.raw_output_textedit.clear()
        self.rendered_output_view.clear()
        self.copy_raw_button.setEnabled(False)
        # Output tab might be disabled if we are resetting from an earlier stage
        if self.main_tabs.isTabEnabled(self.output_tab_index):
             self.show_status("Output cleared.")
        # Do not switch tabs here, user might be on Tab 1 or 2.

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
                self.rendered_output_view.setHtml(html_output)
            except Exception as e: 
                self.show_warning(f"Markdown rendering error: {e}. Showing raw text.")
                self.rendered_output_view.setPlainText(raw_markdown) 
            self.rendered_output_view.moveCursor(QTextCursor.Start)
            self.rendered_output_view.ensureCursorVisible()
        else: 
            self.rendered_output_view.clear()
            self.rendered_output_view.setPlaceholderText("A basic rendered preview of the Markdown will appear here.")


    def reset_settings(self):
        confirm = QMessageBox.question(
            self, "Confirm Reset", 
            "Reset ALL settings (filters, inclusions, prompt, docs, templates, theme) to defaults "
            "and clear folder/output/tree?\nEnvironment association will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            default_settings_copy = DEFAULT_SETTINGS.copy() 
            default_settings_copy["prompt_templates"] = list(DEFAULT_AI_PROMPT_TEMPLATES) 
            default_settings_copy["loaded_doc_paths"] = [] 
            default_settings_copy["checked_tree_paths_str_abs"] = [] 

            self.apply_settings_to_ui(default_settings_copy) 
            
            if self.folder_path_edit: self.folder_path_edit.clear()
            self.clear_output()
            if self.project_explorer_tab:
                self.project_explorer_tab.tree_model.clear()
                self.project_explorer_tab.tree_model.setHorizontalHeaderLabels(['Name'])
            
            self.prompt_templates = default_settings_copy["prompt_templates"]
            self.loaded_doc_paths = default_settings_copy["loaded_doc_paths"]
            self._update_template_combo()
            self._update_doc_list_widget()

            self.theme_manager.apply_theme_from_file_name(DEFAULT_SETTINGS["current_theme_file"]) 

            # Reset tab states
            self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
            self.main_tabs.setTabEnabled(self.output_tab_index, False)
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)
            if self.load_tree_button: self.load_tree_button.setEnabled(True)

            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            self.show_status("All settings reset. Select folder and filters, then load project tree.")
    
    def get_settings_from_ui_for_filters(self) -> Dict[str, Any]:
        selected_presets = [item.text() for item in self.preset_list_widget.selectedItems()]
        return {
            "selected_presets": selected_presets,
            "custom_folders": self.custom_folders_edit.text(),
            "custom_extensions": self.custom_extensions_edit.text(),
            "custom_patterns": self.custom_patterns_edit.text(),
            "dynamic_patterns": self.dynamic_exclude_edit.text(),
            "custom_inclusions": self.custom_inclusions_edit.text(),
            "max_file_size_mb": self.max_size_spinbox.value(), 
        }


    def get_settings_from_ui(self) -> Dict[str, Any]:
        filter_settings = self.get_settings_from_ui_for_filters()
        current_custom_prompt = self.custom_prompt_edit.toPlainText() if self.custom_prompt_edit else ""
        
        checked_paths_str_abs = []
        if self.project_explorer_tab and self.main_tabs.isTabEnabled(self.project_explorer_tab_index): # Only get if tree is loaded/relevant
            selected_paths_from_tree = self.project_explorer_tab.get_selected_file_paths()
            checked_paths_str_abs = [str(p.resolve()) for p in selected_paths_from_tree]

        user_templates = [
            t for t in self.prompt_templates 
            if not any(d_t['name'] == t['name'] and d_t['content'] == t['content'] for d_t in DEFAULT_AI_PROMPT_TEMPLATES)
        ]

        all_settings = {
            "version": DEFAULT_SETTINGS["version"], 
            "folder_path": self.folder_path_edit.text() if self.folder_path_edit else "",
            **filter_settings, 
            "save_output_checked": self.save_output_checkbox.isChecked(),
            "custom_prompt": current_custom_prompt,
            "current_theme_file": self.theme_manager.current_theme_file_name,
            "prompt_templates": user_templates, 
            "loaded_doc_paths": self.loaded_doc_paths, 
            "checked_tree_paths_str_abs": checked_paths_str_abs,
        }
        return all_settings

    def apply_settings_to_ui(self, settings_dict: Dict[str, Any]):
        loaded_version = settings_dict.get("version", "1.0") 
        if not loaded_version.startswith(DEFAULT_SETTINGS["version"].split('.')[0]): 
            print(f"INFO: Loading settings from a legacy format (v{loaded_version}). Applying defaults for new features or mismatches.")

        if self.folder_path_edit: self.folder_path_edit.setText(settings_dict.get("folder_path", DEFAULT_SETTINGS["folder_path"]))
        
        self.preset_list_widget.clearSelection()
        selected_presets_from_file = settings_dict.get("selected_presets", [])
        if isinstance(selected_presets_from_file, list): 
            for preset_name in selected_presets_from_file:
                items = self.preset_list_widget.findItems(preset_name, Qt.MatchExactly)
                if items: items[0].setSelected(True)
        
        self.custom_folders_edit.setText(settings_dict.get("custom_folders", DEFAULT_SETTINGS["custom_folders"]))
        self.custom_extensions_edit.setText(settings_dict.get("custom_extensions", DEFAULT_SETTINGS["custom_extensions"]))
        self.custom_patterns_edit.setText(settings_dict.get("custom_patterns", DEFAULT_SETTINGS["custom_patterns"]))
        self.dynamic_exclude_edit.setText(settings_dict.get("dynamic_patterns", DEFAULT_SETTINGS["dynamic_patterns"])) 
        self.custom_inclusions_edit.setText(settings_dict.get("custom_inclusions", DEFAULT_SETTINGS["custom_inclusions"]))
        self.max_size_spinbox.setValue(float(settings_dict.get("max_file_size_mb", DEFAULT_SETTINGS["max_file_size_mb"])))
        self.save_output_checkbox.setChecked(bool(settings_dict.get("save_output_checked", DEFAULT_SETTINGS["save_output_checked"])))

        if self.custom_prompt_edit: self.custom_prompt_edit.setPlainText(settings_dict.get("custom_prompt", DEFAULT_SETTINGS["custom_prompt"]))

        loaded_user_templates = settings_dict.get("prompt_templates", []) 
        combined_templates = list(DEFAULT_AI_PROMPT_TEMPLATES) 
        default_names = {t['name'] for t in DEFAULT_AI_PROMPT_TEMPLATES}

        if isinstance(loaded_user_templates, list):
            for t_user in loaded_user_templates:
                if isinstance(t_user, dict) and 'name' in t_user and 'content' in t_user:
                    is_customized_default = False
                    for i, d_t in enumerate(combined_templates): 
                        if d_t['name'] == t_user['name']: 
                            if d_t['content'] != t_user['content']: 
                                combined_templates[i] = t_user 
                            is_customized_default = True
                            break
                    if not is_customized_default and t_user['name'] not in default_names: 
                        combined_templates.append(t_user)
                else:
                    self.show_warning(f"Invalid template format found in environment file: {t_user}. Skipping.")
        self.prompt_templates = combined_templates
        self._update_template_combo() 

        loaded_docs_str_paths = settings_dict.get("loaded_doc_paths", [])
        valid_loaded_docs = []
        if isinstance(loaded_docs_str_paths, list) and all(isinstance(p, str) for p in loaded_docs_str_paths):
            for path_str in loaded_docs_str_paths:
                p = Path(path_str)
                if p.exists() and p.is_file():
                    valid_loaded_docs.append(str(p.resolve())) 
                else:
                    self.show_warning(f"Documentation file from environment not found or invalid: {path_str}. Skipping.")
            self.loaded_doc_paths = valid_loaded_docs
        else:
            self.loaded_doc_paths = [] 
            if "loaded_doc_paths" in settings_dict: 
                 self.show_warning("Loaded documentation paths have an invalid format. Clearing list.")
        self._update_doc_list_widget()

        loaded_theme_file = settings_dict.get("current_theme_file", DEFAULT_SETTINGS["current_theme_file"])
        if self.theme_manager.current_theme_file_name != loaded_theme_file: 
            self.theme_manager.apply_theme_from_file_name(loaded_theme_file)

        self.pending_tree_checks = settings_dict.get("checked_tree_paths_str_abs", None)

        # After applying settings, Tab 2 and 3 should be disabled until tree is loaded.
        # The user needs to click "Load Project Tree" if folder_path is set.
        self.main_tabs.setTabEnabled(self.project_explorer_tab_index, False)
        self.main_tabs.setTabEnabled(self.output_tab_index, False)
        self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)
        if self.load_tree_button: self.load_tree_button.setEnabled(True)

        if self.folder_path_edit and self.folder_path_edit.text() and Path(self.folder_path_edit.text()).is_dir():
            self.show_status("Environment settings applied. Click 'Load Project Tree' to proceed.")
        elif self.project_explorer_tab: 
            self.project_explorer_tab.tree_model.clear()
            self.project_explorer_tab.tree_model.setHorizontalHeaderLabels(['Name'])
            if self.pending_tree_checks is not None: 
                self.show_warning("Could not apply saved tree selection as the project folder is not set or invalid in the loaded environment.")
                self.pending_tree_checks = None 


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

        self.theme_manager.current_theme_file_name = self.settings.value("currentThemeFileName", DEFAULT_THEME_FILE)
        
        self.prompt_templates = list(DEFAULT_AI_PROMPT_TEMPLATES) 
        default_names_contents = {(t['name'], t['content']) for t in DEFAULT_AI_PROMPT_TEMPLATES}
        
        user_templates_data = self.settings.value("promptTemplates", []) 
        if isinstance(user_templates_data, list):
            for t_user in user_templates_data:
                if isinstance(t_user, dict) and 'name' in t_user and 'content' in t_user:
                    if (t_user['name'], t_user['content']) not in default_names_contents:
                        found_default_to_replace = False
                        for i, d_t in enumerate(self.prompt_templates):
                            if d_t['name'] == t_user['name']: 
                                self.prompt_templates[i] = t_user 
                                found_default_to_replace = True
                                break
                        if not found_default_to_replace: 
                            self.prompt_templates.append(t_user) 
                else:
                    print("WARNING: Stored prompt template from persistent settings has invalid format. Skipping.")
        elif user_templates_data: 
            print("WARNING: Stored prompt templates (persistent) invalid format (not a list). Resetting.")
            self.settings.remove("promptTemplates") 

        doc_paths_data = self.settings.value("loadedDocPaths", [])
        valid_doc_paths = []
        if isinstance(doc_paths_data, list) and all(isinstance(p, str) for p in doc_paths_data):
             for path_str in doc_paths_data:
                 p = Path(path_str)
                 if p.exists() and p.is_file():
                     valid_doc_paths.append(str(p.resolve())) 
                 else:
                     print(f"INFO: Pruning non-existent documentation path from persistent settings: {path_str}")
             self.loaded_doc_paths = valid_doc_paths
             if len(self.loaded_doc_paths) != len(doc_paths_data): 
                 self.settings.setValue("loadedDocPaths", self.loaded_doc_paths)
        elif doc_paths_data: 
            self.loaded_doc_paths = []
            print("WARNING: Stored documentation paths (persistent) invalid format. Resetting.")
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
                        self.show_warning(f"Failed loading most recent environment '{most_recent_path.name}'. Removing from list.")
                        self._remove_recent_environment(str(most_recent_path)) 
                else: 
                    self.show_warning(f"Most recent environment file not found: '{most_recent_path.name}'. Removing from list.")
                    self._remove_recent_environment(str(most_recent_path))
        
        if not loaded_from_recent:
            settings_to_apply = DEFAULT_SETTINGS.copy() 
            settings_to_apply['prompt_templates'] = self.prompt_templates 
            settings_to_apply['loaded_doc_paths'] = self.loaded_doc_paths 
            settings_to_apply['current_theme_file'] = self.theme_manager.current_theme_file_name 

            self.apply_settings_to_ui(settings_to_apply) 
            self.current_environment_file = None 
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            # Initial status set at the end of __init__
            # self.show_status("Loaded default settings. No recent environment loaded or load failed.")


    def _update_window_title(self):
        base_title = f"Folder Structure to Text v{DEFAULT_SETTINGS['version']}"
        if self.current_environment_file:
            self.setWindowTitle(f"{base_title} - [{self.current_environment_file.name}]")
        else:
            folder_name = ""
            if self.folder_path_edit and self.folder_path_edit.text():
                 folder_name = Path(self.folder_path_edit.text()).name
            
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
                loaded_settings_dict = json.load(f) 
            
            if not isinstance(loaded_settings_dict, dict):
                raise TypeError("Invalid JSON format in environment file.")

            self.apply_settings_to_ui(loaded_settings_dict) 
            
            self.current_environment_file = file_path
            self.settings.setValue("lastEnvDir", str(file_path.parent)) 
            self._add_recent_environment(file_path.name, str(file_path)) 
            
            self._update_window_title()
            self.save_env_action.setEnabled(True) 
            # Do not auto-load tree. User must click "Load Project Tree"
            # Status will be updated by apply_settings_to_ui or related logic.
            if self.folder_path_edit and self.folder_path_edit.text() and Path(self.folder_path_edit.text()).is_dir():
                 self.show_status(f"Environment '{file_path.name}' loaded. Click 'Load Project Tree' on Tab 1.")
            else:
                 self.show_status(f"Environment '{file_path.name}' loaded. Project folder is not set or invalid. Please set it on Tab 1.")
            return True
        except (IOError, json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
            self.show_error(f"Failed loading environment '{file_path.name}': {e}")
            self.current_environment_file = None 
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            return False
        except Exception as e: 
            self.show_error(f"Unexpected error loading environment '{file_path.name}': {e}\n{traceback.format_exc()}")
            self.current_environment_file = None
            self._update_window_title()
            self.save_env_action.setEnabled(False)
            return False

    def load_environment_dialog(self):
        start_dir = self.settings.value("lastEnvDir", str(Path.home()))
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Environment", start_dir, "JSON Files (*.json);;All Files (*)")
        if fileName:
            self._load_environment_from_path(Path(fileName))

    def save_current_environment(self):
        if not self.current_environment_file:
            self.save_environment_as() 
            return
        
        if not self.current_environment_file.parent.exists():
            self.show_error(f"Directory '{self.current_environment_file.parent}' no longer exists. Cannot save. Please use 'Save As...'.")
            self.current_environment_file = None 
            self.save_env_action.setEnabled(False)
            self._update_window_title()
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
        
        folder_name_str = ""
        if self.folder_path_edit and self.folder_path_edit.text():
            folder_name_str = Path(self.folder_path_edit.text()).name
        
        sanitized_folder_name = sanitize_filename(folder_name_str) if folder_name_str else "untitled"
        default_name = f"{sanitized_folder_name}_fse_env.json"
        
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Environment As...", str(Path(start_dir) / default_name), "JSON Files (*.json);;All Files (*)")
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
                
                action = QAction(action_text, self, triggered=functools.partial(self.load_specific_recent_environment, env['path']))
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
        if not self.template_combo: return

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
        if not self.template_combo or not self.custom_prompt_edit: return

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
        if not self.custom_prompt_edit: return

        current_content = self.custom_prompt_edit.toPlainText().strip()
        if not current_content:
            QMessageBox.warning(self, "Cannot Save Empty", "Prompt text area is empty. Cannot save as template.")
            return

        dialog = EditTemplateDialog(template_content=current_content, existing_names=self.get_template_names(), parent=self)
        dialog.setWindowTitle("Save Current Prompt as Template") 
        
        if dialog.exec_() == QDialog.Accepted:
            new_template_name = dialog.get_template_name()
            new_template_content = dialog.get_template_content() 
            
            new_template = {"name": new_template_name, "content": new_template_content}

            is_exact_default_duplicate = any(
                t_def['name'] == new_template_name and t_def['content'] == new_template_content 
                for t_def in DEFAULT_AI_PROMPT_TEMPLATES
            )
            if is_exact_default_duplicate:
                self.show_warning(f"Template '{new_template_name}' is identical to a default template and was not saved as a new user template.")
                idx = self.template_combo.findText(new_template_name)
                if idx !=-1: self.template_combo.setCurrentIndex(idx)
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
        
        self.save_prompt_templates_to_settings() 
        self._update_template_combo() 
        self.show_status("Template management closed. Changes (if any) saved.")

    def get_template_names(self) -> List[str]:
        return [t.get('name', '') for t in self.prompt_templates]

    def save_prompt_templates_to_settings(self):
        default_templates_set = {(dt['name'], dt['content']) for dt in DEFAULT_AI_PROMPT_TEMPLATES}
        
        user_templates_to_save = [
            t for t in self.prompt_templates 
            if (t['name'], t.get('content', '')) not in default_templates_set
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
                    path_str_resolved = str(path.resolve()) 
                    if path_str_resolved not in self.loaded_doc_paths:
                        self.loaded_doc_paths.append(path_str_resolved)
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

    def start_generate_structure_worker(self):
        if self.current_generation_thread and self.current_generation_thread.isRunning():
            self.show_warning("Structure generation is already in progress.")
            return
        if not self.folder_path_edit or not self.generate_button or not self.project_explorer_tab: 
            self.show_error("UI not ready for generation.")
            return

        current_processing_settings = self.get_settings_from_ui()
        folder_path = current_processing_settings["folder_path"]

        if not folder_path or not Path(folder_path).is_dir():
            self.show_warning("Project folder path is not valid. Please set it in Tab 1 and load the tree.")
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)
            if self.folder_path_edit: self.folder_path_edit.setFocus()
            return
        
        # Ensure tree is actually loaded and Explorer tab is active
        if not self.main_tabs.isTabEnabled(self.project_explorer_tab_index) or \
           self.project_explorer_tab.tree_model.rowCount() == 0 :
            self.show_warning("Project tree not loaded or empty. Please load tree in Tab 1 first.")
            self.main_tabs.setCurrentIndex(self.project_setup_filters_tab_index)
            return


        self.settings.setValue("lastFolderPath", folder_path)
        if not self.current_environment_file: 
            self._update_window_title()

        self.generate_button.setEnabled(False)
        self.copy_raw_button.setEnabled(False) 
        self.raw_output_textedit.setPlainText("Generating, please wait...")
        self.rendered_output_view.setPlainText("Generating...")
        
        # Enable and switch to output tab
        self.main_tabs.setTabEnabled(self.output_tab_index, True)
        self.main_tabs.setCurrentIndex(self.output_tab_index)
        self.output_tabs.setCurrentIndex(0) 
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.show_status("Starting structure generation...")


        final_custom_prompt = apply_placeholders(current_processing_settings["custom_prompt"], self)
        documentation_content = self._get_combined_documentation_content()
        
        selected_paths_from_tree = self.project_explorer_tab.get_selected_file_paths()

        if not Path(folder_path).exists():
            self.show_error(f"Target folder '{folder_path}' no longer exists. Generation aborted.")
            self._on_generation_finished() 
            return

        self.current_generation_worker = FolderStructureApp.StructureGenerationWorker(
            self.processor, current_processing_settings, selected_paths_from_tree,
            final_custom_prompt, documentation_content
        )
        self.current_generation_thread = QThread()
        self.current_generation_worker.moveToThread(self.current_generation_thread)

        self.current_generation_worker.generation_complete.connect(self._on_generation_complete)
        self.current_generation_worker.generation_error.connect(self._on_generation_error)
        self.current_generation_worker.finished.connect(self._on_generation_finished)

        self.current_generation_thread.started.connect(self.current_generation_worker.run)
        self.current_generation_thread.start()

    def _on_generation_complete(self, generated_text: str):
        self.raw_output_textedit.setPlainText(generated_text)
        self.update_rendered_output() 
        
        is_error_output = generated_text.startswith("```error")
        self.copy_raw_button.setEnabled(not is_error_output and bool(generated_text)) 
        
        current_settings = self.get_settings_from_ui() 
        if current_settings["save_output_checked"] and not is_error_output and generated_text:
            self.save_output_markdown_to_file(generated_text, Path(current_settings["folder_path"]).name)
        
        self.show_status("Structure generation complete. Output is ready on Tab 3.")


    def _on_generation_error(self, error_message: str):
        self.show_error(f"Generation Error: {error_message}")
        error_text_md = f"```error\n{error_message}\n```"
        self.raw_output_textedit.setPlainText(error_text_md)
        self.rendered_output_view.setPlainText(error_text_md) 
        self.copy_raw_button.setEnabled(False) 
        self.show_status("Generation failed. See error message on Tab 3.")


    def _on_generation_finished(self):
        QApplication.restoreOverrideCursor()
        if self.generate_button: self.generate_button.setEnabled(True)
        
        if self.raw_output_textedit.toPlainText(): 
            self.raw_output_textedit.moveCursor(QTextCursor.Start)
            self.raw_output_textedit.ensureCursorVisible()

        if self.current_generation_thread:
            if self.current_generation_thread.isRunning(): 
                self.current_generation_thread.quit()
                self.current_generation_thread.wait(1000) 
            self.current_generation_thread.deleteLater() 
            self.current_generation_thread = None
        if self.current_generation_worker:
            self.current_generation_worker.deleteLater()
            self.current_generation_worker = None


    def save_output_markdown_to_file(self, text_content: str, folder_name: str):
        current_project_folder = self.folder_path_edit.text() if self.folder_path_edit else ""
        default_dir_str = str(Path(current_project_folder).parent) if current_project_folder and Path(current_project_folder).is_dir() else str(Path.home())
        
        save_dir_str = self.settings.value("lastMarkdownSaveDir", default_dir_str)
        save_dir = Path(save_dir_str)
        if not save_dir.exists() or not save_dir.is_dir(): 
            save_dir = Path(default_dir_str) 
            if not save_dir.exists() or not save_dir.is_dir(): save_dir = Path.home() 
            self.settings.remove("lastMarkdownSaveDir") 
            
        sanitized_folder_name = sanitize_filename(folder_name) if folder_name else "output"
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        suggested_name = f"fse_{sanitized_folder_name}_{timestamp}.md"
        
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown Output", 
            str(save_dir / suggested_name), 
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
        self.show_status("Closing application, saving settings...")
        
        if self.project_explorer_tab and self.project_explorer_tab.current_tree_population_thread and \
           self.project_explorer_tab.current_tree_population_thread.isRunning():
            print("Waiting for tree population thread to finish...")
            self.project_explorer_tab.current_tree_population_thread.quit()
            if not self.project_explorer_tab.current_tree_population_thread.wait(2000): 
                print("Tree population thread did not finish gracefully.")
            # self.project_explorer_tab.current_tree_population_thread = None # Worker/thread deleteLater themselves

        if self.current_generation_thread and self.current_generation_thread.isRunning():
            print("Waiting for generation thread to finish...")
            self.current_generation_thread.quit()
            if not self.current_generation_thread.wait(2000): 
                print("Generation thread did not finish gracefully.")
            # self.current_generation_thread = None # Worker/thread deleteLater themselves

        self.settings.setValue("currentThemeFileName", self.theme_manager.current_theme_file_name)
        self.save_prompt_templates_to_settings() 
        self.settings.setValue("recentEnvironments", self.recent_environments)
        
        valid_doc_paths = [p for p in self.loaded_doc_paths if Path(p).exists() and Path(p).is_file()]
        self.settings.setValue("loadedDocPaths", valid_doc_paths)
        
        if self.folder_path_edit and self.folder_path_edit.text() and Path(self.folder_path_edit.text()).exists():
            self.settings.setValue("lastBrowseDir", str(Path(self.folder_path_edit.text()).resolve())) 
        
        if self.current_environment_file and self.current_environment_file.parent.exists():
            self.settings.setValue("lastEnvDir", str(self.current_environment_file.parent.resolve()))

        for key in ["lastDocDir", "lastMarkdownSaveDir", "lastBrowseDir", "lastEnvDir"]:
            path_val_str = self.settings.value(key)
            if path_val_str and isinstance(path_val_str, str):
                path_val = Path(path_val_str)
                if not path_val.exists() or not path_val.is_dir():
                    self.settings.remove(key) 
            elif path_val_str: 
                 self.settings.remove(key)

        self.settings.sync() 
        self.show_status("Settings saved. Exiting application.")
        event.accept()


if __name__ == '__main__':
    if not ASSETS_DIR.exists():
        try:
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Created missing assets directory: {ASSETS_DIR}")
        except OSError as e:
            print(f"Warning: Could not create assets directory: {e}")
    
    if not THEMES_DIR.exists():
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created themes directory: {THEMES_DIR}")

    default_light_theme_path = THEMES_DIR / DEFAULT_THEME_FILE 
    if not default_light_theme_path.exists():
        try:
            default_light_qss = """
                QWidget { font-family: "Segoe UI", Arial, sans-serif; font-size: 9pt; background-color: #f0f0f0; color: #1e1e1e; }
                QMainWindow, QDialog { background-color: #f0f0f0; }
                QGroupBox { border: 1px solid #c8c8c8; border-radius: 4px; margin-top: 1ex; font-weight: bold; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; background-color: #f0f0f0; left: 10px;}
                QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color: white; border: 1px solid #c0c0c0; border-radius: 3px; padding: 2px; }
                QTextEdit { selection-background-color: #a8d8ff; selection-color: black; }
                QPushButton { background-color: #e1e1e1; border: 1px solid #adadad; border-radius: 3px; padding: 5px; min-height: 15px; }
                QPushButton:hover { background-color: #cacaca; } QPushButton:pressed { background-color: #b0b0b0; } QPushButton:disabled { background-color: #dcdcdc; color: #a0a0a0; }
                QListWidget, QTreeView { background-color: white; border: 1px solid #c0c0c0; selection-background-color: #cce8ff; selection-color: black; alternate-background-color: #f7f7f7; }
                QTreeView::item { padding: 3px; } QTreeView::item:selected { background-color: #cce8ff; color: black; }
                QHeaderView::section { background-color: #e8e8e8; padding: 4px; border: 1px solid #d0d0d0; font-weight: bold;}
                QTabWidget::pane { border: 1px solid #c0c0c0; top: -1px; background: #f0f0f0;}
                QTabBar::tab { background: #d8d8d8; border: 1px solid #b0b0b0; border-bottom: none; padding: 5px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px;}
                QTabBar::tab:selected { background: #f0f0f0; margin-bottom: -1px; } QTabBar::tab:hover { background: #e0e0e0; }
                QStatusBar { background-color: #e0e0e0; border-top: 1px solid #c0c0c0; }
                QToolBox::tab { background-color: #e0e0e0; border: 1px solid #c0c0c0; border-bottom: none; padding: 5px; font-weight: bold; border-top-left-radius: 3px; border-top-right-radius: 3px;}
                QToolBox::tab:selected { background-color: #f0f0f0; border-bottom: 1px solid #f0f0f0; margin-bottom: -1px;}
                QScrollArea { border: none; }
                QCheckBox::indicator { width: 13px; height: 13px; } 
            """.replace("{ASSETS_DIR}", ASSETS_DIR.as_posix())
            default_light_theme_path.write_text(default_light_qss, encoding='utf-8')
            print(f"Created default theme: {default_light_theme_path}")
        except Exception as e:
            print(f"Could not create default_light.qss: {e}")

    default_dark_theme_path = THEMES_DIR / "default_dark.qss"
    if not default_dark_theme_path.exists():
        try:
            default_dark_qss = """
                QWidget { font-family: "Segoe UI", Arial, sans-serif; font-size: 9pt; background-color: #2d2d2d; color: #e0e0e0; }
                QMainWindow, QDialog { background-color: #2d2d2d; }
                QGroupBox { border: 1px solid #4a4a4a; border-radius: 4px; margin-top: 1ex; font-weight: bold; color: #e0e0e0;}
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; background-color: #2d2d2d; left: 10px; color: #e0e0e0;}
                QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color: #3c3c3c; border: 1px solid #505050; border-radius: 3px; padding: 2px; color: #e0e0e0; }
                QTextEdit { selection-background-color: #0050a0; selection-color: white; }
                QPushButton { background-color: #4a4a4a; border: 1px solid #606060; border-radius: 3px; padding: 5px; min-height: 15px; color: #e0e0e0; }
                QPushButton:hover { background-color: #5a5a5a; } QPushButton:pressed { background-color: #3a3a3a; } QPushButton:disabled { background-color: #404040; color: #808080; }
                QListWidget, QTreeView { background-color: #353535; border: 1px solid #484848; color: #e0e0e0; selection-background-color: #0050a0; selection-color: white; alternate-background-color: #3a3a3a; }
                QTreeView::item { padding: 3px; } QTreeView::item:selected { background-color: #0050a0; color: white; }
                QHeaderView::section { background-color: #3e3e3e; padding: 4px; border: 1px solid #505050; font-weight: bold; color: #e0e0e0;}
                QTabWidget::pane { border: 1px solid #404040; top: -1px; background: #2d2d2d;}
                QTabBar::tab { background: #404040; border: 1px solid #505050; border-bottom: none; padding: 5px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #c0c0c0;}
                QTabBar::tab:selected { background: #2d2d2d; margin-bottom: -1px; color: #e0e0e0; } QTabBar::tab:hover { background: #484848; color: #e0e0e0;}
                QStatusBar { background-color: #3a3a3a; border-top: 1px solid #484848; color: #e0e0e0;}
                QToolBox::tab { background-color: #3a3a3a; border: 1px solid #484848; border-bottom: none; padding: 5px; font-weight: bold; border-top-left-radius: 3px; border-top-right-radius: 3px; color: #d0d0d0;}
                QToolBox::tab:selected { background-color: #2d2d2d; border-bottom: 1px solid #2d2d2d; margin-bottom: -1px; color: #e0e0e0;}
                QScrollArea { border: none; background-color: #2d2d2d; }
            """.replace("{ASSETS_DIR}", ASSETS_DIR.as_posix()) 
            default_dark_theme_path.write_text(default_dark_qss, encoding='utf-8')
            print(f"Created default dark theme: {default_dark_theme_path}")
        except Exception as e:
            print(f"Could not create default_dark.qss: {e}")


    app = QApplication(sys.argv)
    try:
        main_window = FolderStructureApp()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e: 
        print("\n--- Unhandled Exception During Application Startup ---")
        print(f"Error: {e}\n{traceback.format_exc()}")
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

