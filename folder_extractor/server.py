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
import time
import ast
import inspect

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import asyncio

import socket
import webbrowser
import threading

try:
    from PyQt5.QtWidgets import QApplication, QFileDialog
    _PYQT5_AVAILABLE = True
except ImportError:
    _PYQT5_AVAILABLE = False


class Template(BaseModel):
    name: str
    content: str

DEFAULT_AI_PROMPT_TEMPLATES_RAW = [
    {
        "name": "AI: Add New Feature - Full Code",
        "content": "You are an expert software developer. Your task is to implement a new feature.\n\n**Feature Request:** {USER_REQUEST}\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the provided folder structure and file contents (full content or signatures as indicated).\n2.  **Develop a Plan:** Create a detailed plan outlining:\n    *   Which files need to be created.\n    *   Which existing files need to be modified.\n    *   A summary of changes for each affected file.\n    *   Any new dependencies required.\n    *   Potential impacts on existing functionality.\n    *   Suggestions for necessary tests.\n    **Present this plan first and wait for my explicit 'ACKNOWLEDGE PLAN' or 'PROCEED' command before generating any code.**\n\n3.  **Implement Changes (Full Code):**\n    *   For **new files**, generate the complete file content from scratch. Ensure the code is clean, well-commented (docstrings/JSDoc where appropriate), and adheres to best practices.\n    *   For **modified files**, regenerate the ENTIRE file with the necessary changes incorporated. Do NOT use placeholders like '// ... existing code ...' or provide only fragments. The output for a modified file must be its complete new content.\n    *   Address all aspects of the feature request.\n    *   Consider edge cases and potential error handling.\n\n**Output Format:**\nAfter I acknowledge the plan, provide the content for each new or modified file one by one. Start each file block with `--- FILE: path/to/your/file.ext ---` and end with `--- END OF FILE ---`. Wait for my 'NEXT' command after each file before proceeding to the next one."
    },
    {
        "name": "AI: Add New Feature - Guided Changes",
        "content": "You are an expert software developer. Your task is to guide me in implementing a new feature.\n\n**Feature Request:** {USER_REQUEST}\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the provided folder structure and file contents (full content or signatures as indicated).\n2.  **Develop a Plan:** Create a detailed plan outlining:\n    *   Which files need to be created.\n    *   Which existing files need to be modified.\n    *   A summary of changes for each affected file (e.g., \"add new function X\", \"modify method Y in class Z\").\n    *   Any new dependencies required.\n    *   Potential impacts on existing functionality.\n    *   Suggestions for necessary tests.\n    **Present this plan first and wait for my explicit 'ACKNOWLEDGE PLAN' or 'PROCEED' command before providing code modifications.**\n\n3.  **Guide Implementation (Diff-like or Specific Instructions):**\n    *   For **new files**: Provide the complete content for the new file.\n    *   For **modified files**: Clearly indicate the changes. For each change:\n        *   Identify the location (e.g., \"In file `path/to/file.ext`, after line X containing `...text...`\" or \"Replace the function `foo()` with the following:\").\n        *   Show the **original code block** (e.g., the entire function or a few lines of context).\n        *   Show the **modified code block** that should replace it or be inserted.\n        *   Ensure changes are for complete functions/methods or logical blocks, not tiny fragments, to make them easier to apply.\n    *   Address all aspects of the feature request.\n\n**Interaction Flow:**\nAfter I acknowledge the plan, you will provide the changes for ONE file (or one significant part of a file) at a time. Start each change block with `--- CHANGE FOR: path/to/your/file.ext ---`. After providing the change, **wait for my 'NEXT' or 'ACKNOWLEDGE CHANGE' command** before proceeding to the next modification or file."
    },
    {
        "name": "AI: Code Review - Full Analysis",
        "content": "You are an expert code reviewer.\n\n**Request:** Please perform a comprehensive code review of the selected files/signatures provided in the project context below.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Thoroughly review the provided code.\n2.  **Develop a Review Plan/Summary:** Briefly outline the key areas you will focus on or a summary of your initial findings. **Present this plan/summary first and wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Provide Detailed Review (File by File):**\n    *   For each file, discuss its purpose and overall quality.\n    *   Focus on:\n        1.  Clarity and Readability\n        2.  Potential Bugs or Edge Cases\n        3.  Performance Optimizations\n        4.  Adherence to Best Practices (e.g., DRY, SOLID)\n        5.  Security Vulnerabilities\n        6.  Code smells or anti-patterns.\n        7.  Quality of comments and documentation (docstrings/JSDoc).\n    *   Provide specific examples from the code and concrete suggestions for improvement.\n\n**Interaction Flow:**\nAfter I acknowledge the plan, provide your review for ONE file at a time. Start each file's review with `--- REVIEW FOR: path/to/file.ext ---`. After completing the review for one file, **wait for my 'NEXT' command** before proceeding to the next file."
    },
    {
        "name": "AI: Code Review - Guided Discussion",
        "content": "You are an expert code reviewer. Let's review the code together.\n\n**Request:** Guide me through a review of the selected files/signatures provided in the project context below. Help me identify areas for improvement.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the provided code.\n2.  **Propose Review Focus:** Suggest a specific file or a high-level aspect (e.g., \"Let's start with the error handling in `utils.py`\") to begin the review. **Wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Interactive Review (Section by Section):**\n    *   Ask targeted questions about specific code sections or patterns you observe.\n    *   Point out potential issues related to:\n        1.  Clarity, Readability\n        2.  Bugs, Edge Cases\n        3.  Performance\n        4.  Best Practices (DRY, SOLID)\n        5.  Security\n    *   When you identify an issue, explain it and then suggest how it could be improved, perhaps by showing a small \"before\" and \"after\" or by describing the change.\n\n**Interaction Flow:**\nAfter I acknowledge your proposed starting point, discuss ONE specific point or section at a time. After each point and your suggestion, **wait for my 'NEXT', 'ACKNOWLEDGE POINT', or a question from me** before moving on."
    },
    {
        "name": "AI: Documentation Skeleton - Full Draft",
        "content": "You are a technical writer specializing in software documentation.\n\n**Request:** Generate a comprehensive documentation skeleton for the project/selected files based on the provided context.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the folder structure and file contents/signatures.\n2.  **Plan Documentation Structure:** Outline the overall structure of the documentation you intend to generate (e.g., sections for API reference, usage guides, component descriptions). **Present this plan first and wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Generate Skeleton (File by File or Component by Component):**\n    *   For each major component, class, or function identified:\n        *   Create a heading.\n        *   Suggest standard documentation sections like: Purpose, Key Attributes/Properties, Methods/Functions (with brief descriptions of parameters and return values if discernible from signatures), Usage Examples (placeholders are fine), Dependencies, Configuration Options.\n    *   Produce a fairly complete draft of the skeleton, ready for more detailed content to be filled in.\n\n**Interaction Flow:**\nAfter I acknowledge the plan, provide the documentation skeleton for ONE major file or component at a time. Start each block with `--- DOCS FOR: path/to/file.ext or ComponentName ---`. After completing one, **wait for my 'NEXT' command**."
    },
    {
        "name": "AI: Documentation Skeleton - Guided Outline",
        "content": "You are a technical writer. Help me create a documentation skeleton for this project.\n\n**Request:** Based on the project context, guide me in outlining the documentation for the selected files/components.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt)\n\n**Instructions:**\n1.  **Analyze Context:** Review the folder structure and file contents/signatures.\n2.  **Propose Starting Point:** Suggest a file or component to start outlining. For example, \"Let's begin by outlining the `UserService` class.\" **Wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Interactive Outlining (Section by Section):**\n    *   For the chosen item, suggest key documentation sections one by one (e.g., \"First, a 'Purpose' section. What would you say is its main role?\").\n    *   For functions/methods, prompt for details: \"For the `createUser` method, what are its parameters? What does it return? Any important notes for usage?\"\n    *   Help me build up the outline collaboratively.\n\n**Interaction Flow:**\nAfter I acknowledge your starting point, propose ONE section or sub-item for the outline at a time. After each proposal, **wait for my input, 'NEXT', or 'ACKNOWLEDGE SECTION'** before suggesting the next part of the outline."
    },
    {
        "name": "AI: Explain Code - Detailed Explanation",
        "content": "You are an expert programmer. Your task is to explain code.\n\n**Request:** Please provide a detailed explanation of the functionality of the code snippets/signatures from the selected files in the project context below.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt. You might be asked to focus on specific files or snippets later by the user.)\n\n**Instructions:**\n1.  **Analyze Context:** Review all provided code context.\n2.  **Propose Explanation Order:** Suggest an order for explaining the files or major components (e.g., \"I'll start by explaining `core_logic.py`, then `api_handler.js`.\"). **Present this order and wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Explain Code (File by File, or Component by Component):**\n    *   For each file or significant component:\n        *   Describe its overall purpose and role in the project.\n        *   Explain key classes, functions, or methods: what they do, their parameters, their return values, and how they work together.\n        *   Identify any complex logic, algorithms, or non-obvious behaviors and clarify them.\n        *   Point out important dependencies or interactions with other parts of the code.\n\n**Interaction Flow:**\nAfter I acknowledge the plan, provide your explanation for ONE file or major component at a time. Start each block with `--- EXPLANATION FOR: path/to/file.ext ---`. After completing one, **wait for my 'NEXT' command**."
    },
    {
        "name": "AI: Explain Code - Interactive Q&A",
        "content": "You are an expert programmer. Let's go through this code together and you can explain it to me.\n\n**Request:** Help me understand the selected files/signatures from the project context. I may have specific questions as we go.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt.)\n\n**Instructions:**\n1.  **Analyze Context:** Review all provided code context.\n2.  **Offer Starting Point:** Ask me which file or specific part I'd like to understand first, or suggest a logical starting point (e.g., \"Which part of the code are you most curious about? Or shall we start with `main_module.py`?\"). **Wait for my response or 'PROCEED' if you suggested a start.**\n\n3.  **Interactive Explanation:**\n    *   Once a focus is chosen, provide a high-level overview of that part.\n    *   Then, invite questions or offer to dive into a specific function/class within that part.\n    *   Answer my questions clearly and concisely. Explain what code does, why it might be structured that way, and any tricky parts.\n\n**Interaction Flow:**\nThis will be an interactive session. After your initial overview of a chosen section, **wait for my questions or a 'TELL ME MORE' or 'NEXT SECTION' command.** Respond to one question or explain one sub-component at a time."
    },
    {
        "name": "AI: Refactor Suggestions - Full Report",
        "content": "You are a senior software architect specializing in code quality and refactoring.\n\n**Request:** Analyze the selected code/signatures for potential refactoring opportunities. Provide a comprehensive report.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt.)\n\n**Instructions:**\n1.  **Analyze Context:** Thoroughly review the provided code for areas that could be improved.\n2.  **Plan Refactoring Review:** Outline the key refactoring themes or files you will focus on (e.g., \"Focus on reducing complexity in X, improving modularity in Y, applying Z design pattern\"). **Present this plan first and wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Provide Refactoring Suggestions (File by File or Theme by Theme):**\n    *   For each identified area/file:\n        *   Describe the current situation and why it's a candidate for refactoring.\n        *   Suggest specific improvements to enhance modularity, reduce complexity, improve maintainability, or apply relevant design patterns.\n        *   Explain the benefits of your suggested refactoring.\n        *   If possible, provide a brief conceptual example of the code *before* and *after* the suggested refactoring (signatures or pseudocode is fine for the 'after' if full code is too verbose for a suggestion).\n\n**Interaction Flow:**\nAfter I acknowledge the plan, present your refactoring suggestions for ONE major area or file at a time. Start each block with `--- REFACTORING FOR: path/to/file.ext or ThemeName ---`. After completing one, **wait for my 'NEXT' command**."
    },
    {
        "name": "AI: Refactor Suggestions - Guided Workshop",
        "content": "You are a senior software architect. Let's collaboratively identify refactoring opportunities in this code.\n\n**Request:** Guide me in analyzing the selected code/signatures for refactoring. Help me understand what could be improved and why.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt.)\n\n**Instructions:**\n1.  **Analyze Context:** Review the provided code.\n2.  **Propose Focus Area:** Suggest a specific file, class, or function that seems like a good candidate for refactoring discussion (e.g., \"Let's look at the `process_data` function. It seems quite long. What do you think?\"). **Wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Interactive Refactoring Discussion:**\n    *   For the chosen code segment, ask questions to prompt thinking about its structure (e.g., \"Do you see any repeated logic here?\", \"Could this class be split into smaller ones?\").\n    *   Explain refactoring principles (like SRP, DRY, cohesion, coupling) as they apply.\n    *   When a refactoring opportunity is identified, discuss the pros and cons of different approaches.\n    *   Help me formulate the refactored code, or show a small example of the change.\n\n**Interaction Flow:**\nAfter I acknowledge your proposed focus, discuss ONE specific refactoring idea or code segment at a time. After you explain a point or suggest a change, **wait for my input, 'NEXT', or 'ACKNOWLEDGE IDEA'** before moving on."
    },
    {
        "name": "AI: Test Case Ideas - Comprehensive List",
        "content": "You are a QA engineer with expertise in test case design.\n\n**Request:** Based on the selected files/signatures, generate a comprehensive list of potential test cases.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt.)\n\n**Instructions:**\n1.  **Analyze Context:** Review the code to understand its functionality, inputs, outputs, and potential failure points.\n2.  **Plan Test Case Generation:** Outline the categories of tests you will cover (e.g., unit tests for specific functions, integration tests for module interactions, edge cases, UI tests if applicable from context). **Present this plan first and wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Generate Test Cases (Component by Component):**\n    *   For each function, method, class, or module:\n        *   List unit tests for individual behaviors (happy path, error conditions, boundary values).\n        *   Suggest integration tests for interactions between components.\n        *   Identify potential edge case scenarios.\n        *   Include tests for different input types and data validation.\n    *   Format test cases clearly (e.g., Test ID, Description, Steps, Expected Result).\n\n**Interaction Flow:**\nAfter I acknowledge the plan, provide test case ideas for ONE major component or file at a time. Start each block with `--- TESTS FOR: path/to/file.ext or ComponentName ---`. After completing one, **wait for my 'NEXT' command**."
    },
    {
        "name": "AI: Test Case Ideas - Guided Brainstorming",
        "content": "You are a QA engineer. Let's brainstorm test cases for this code together.\n\n**Request:** Help me generate test case ideas for the selected files/signatures.\n\n**Project Context:**\n(The folder structure and file contents/signatures will be provided below this prompt.)\n\n**Instructions:**\n1.  **Analyze Context:** Review the code.\n2.  **Suggest Starting Point:** Propose a function, class, or feature to start brainstorming tests for (e.g., \"Let's think about tests for the `login` function. What are the main scenarios?\"). **Wait for my 'ACKNOWLEDGE PLAN' or 'PROCEED' command.**\n\n3.  **Interactive Test Case Generation:**\n    *   For the chosen item, prompt me with questions to elicit test ideas (e.g., \"What are valid inputs? Invalid inputs? What happens on success? On failure? Are there any boundary conditions?\").\n    *   Suggest different types of tests (unit, integration, positive, negative, edge cases).\n    *   Help refine the test ideas into more concrete test case descriptions.\n\n**Interaction Flow:**\nAfter I acknowledge your starting point, focus on ONE aspect or scenario for testing at a time. After you suggest a test category or ask a prompting question, **wait for my input, 'NEXT', or 'ACKNOWLEDGE IDEA'** before moving on."
    },
    {"name": "General: Project Overview", "content": "Provide a high-level overview of the project based on its structure and file contents/signatures. What is its main purpose? What are the key technologies used? What are the major components and their roles?\nUser Request: {USER_REQUEST}"},
    {"name": "General: Summarize Changes for Commit", "content": "I've made some changes. Based on the context (you might need to be provided with a diff or a list of modified files later), help me draft a concise and informative commit message. Key changes involve [User briefly describes changes or points to files].\nUser Request: {USER_REQUEST}"},
]


_user_prompt_templates: List[Template] = [Template(**t_dict) for t_dict in DEFAULT_AI_PROMPT_TEMPLATES_RAW]
executor = ThreadPoolExecutor(max_workers=5)

DEFAULT_EXCLUDED_FOLDERS: Set[str] = {
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
    ".DS_Store", 
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
    "Large Media Files": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.mp4", "*.avi", ".mp3", ".wav", "*.pdf", "*.doc", "*.docx", "*.ppt", ".pptx", "*.xls", "*.xlsx", "*.psd", "*.ai", "*.sketch"]
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
_MANDATORY_EXCLUDED_FOLDER_NAMES: Set[str] = { ".git", ".vscode", "__pycache__" }

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', filename).strip(' _.') or "default"

def apply_placeholders(text: str, folder_path: str, user_request: str = "[User-defined request should go here]") -> str:
    text = text.replace("{USER_REQUEST}", user_request)
    for key, func in PLACEHOLDERS.items():
        try:
            text = text.replace(key, str(func(folder_path)))
        except Exception:
            pass
    return text

def _get_py_node_source(node: ast.AST, lines: List[str]) -> str:
    signature_parts = []
    
    if hasattr(node, 'decorator_list'):
        for decorator in node.decorator_list:
            try:
                if hasattr(ast, 'unparse'):
                    decorator_source = ast.unparse(decorator)
                else:
                    decorator_source = "".join(lines[decorator.lineno-1 : decorator.end_lineno]).strip() if hasattr(decorator, 'end_lineno') else f"@{decorator.id if isinstance(decorator, ast.Name) else decorator.attr if isinstance(decorator, ast.Attribute) else 'decorator'}" # type: ignore
                signature_parts.append(f"{decorator_source}")
            except Exception:
                signature_parts.append("@decorator_unknown")

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        name = node.name
        args_str = "..."
        if hasattr(ast, 'unparse'):
            args_str = ast.unparse(node.args)
        else:
            arg_parts = []
            for arg_node in node.args.posonlyargs: arg_parts.append(arg_node.arg)
            if node.args.posonlyargs: arg_parts.append('/')
            for arg_node in node.args.args: arg_parts.append(arg_node.arg)
            if node.args.vararg: arg_parts.append(f"*{node.args.vararg.arg}")
            if node.args.kwonlyargs:
                for kwarg_node in node.args.kwonlyargs: arg_parts.append(kwarg_node.arg)
            if node.args.kwarg: arg_parts.append(f"**{node.args.kwarg.arg}")
            args_str = ", ".join(arg_parts)
        
        returns_str = ""
        if node.returns:
            if hasattr(ast, 'unparse'):
                returns_str = " -> " + ast.unparse(node.returns)
            else:
                returns_str = " -> " + ("".join(lines[node.returns.lineno-1 : node.returns.end_lineno]).strip() if hasattr(node.returns, 'end_lineno') else "Any") # type: ignore

        signature_parts.append(f"{prefix} {name}({args_str}){returns_str}:")
        
        docstring = ast.get_docstring(node, clean=True)
        if docstring:
            indented_docstring = inspect.cleandoc(docstring)
            formatted_doc_lines = ['    """' + indented_docstring.splitlines()[0]]
            if len(indented_docstring.splitlines()) > 1:
                formatted_doc_lines.extend(['    ' + line for line in indented_docstring.splitlines()[1:]])
            formatted_doc_lines[-1] += '"""'
            signature_parts.extend(formatted_doc_lines)
        else:
            signature_parts.append("    ...")

    elif isinstance(node, ast.ClassDef):
        name = node.name
        bases_str = ""
        if node.bases:
            bases_str = "(" + ", ".join([ast.unparse(b) if hasattr(ast, 'unparse') else (b.id if isinstance(b, ast.Name) else "object") for b in node.bases]) + ")" # type: ignore
        signature_parts.append(f"class {name}{bases_str}:")
        
        docstring = ast.get_docstring(node, clean=True)
        class_body_elements_follow = False
        if docstring:
            indented_docstring = inspect.cleandoc(docstring)
            formatted_doc_lines = ['    """' + indented_docstring.splitlines()[0]]
            if len(indented_docstring.splitlines()) > 1:
                formatted_doc_lines.extend(['    ' + line for line in indented_docstring.splitlines()[1:]])
            formatted_doc_lines[-1] += '"""'
            signature_parts.extend(formatted_doc_lines)
            class_body_elements_follow = True
        
        for item in node.body:
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                var_source = ""
                try:
                    if hasattr(ast, 'unparse'):
                        var_source = ast.unparse(item)
                    else:
                        var_source = "".join(lines[item.lineno-1 : item.end_lineno]).strip() if hasattr(item, 'end_lineno') else "class_variable_declaration" # type: ignore
                except:
                    var_source = "class_variable_declaration_unavailable"
                signature_parts.extend(["    " + line for line in var_source.splitlines()])
                class_body_elements_follow = True
        
        if not class_body_elements_follow and not any(isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for i in node.body):
             signature_parts.append("    ...")
    return "\n".join(signature_parts)

def extract_python_signatures(code_content: str) -> str:
    try:
        tree = ast.parse(code_content)
        lines = code_content.splitlines()
        output_signatures = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                node_sig_str = _get_py_node_source(node, lines)
                if isinstance(node, ast.ClassDef):
                    method_sigs = []
                    nested_class_sigs = []
                    has_class_members = bool(ast.get_docstring(node)) or any(isinstance(i, (ast.Assign, ast.AnnAssign)) for i in node.body)

                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_sig_node_str = _get_py_node_source(item, lines)
                            method_sigs.append("\n".join(["    " + line for line in method_sig_node_str.splitlines()]))
                        elif isinstance(item, ast.ClassDef): # Nested classes
                            nested_class_node_str = _get_py_node_source(item, lines)
                            nested_class_sigs.append("\n".join(["    " + line for line in nested_class_node_str.splitlines()]))
                    
                    full_class_sig = [node_sig_str]
                    if (method_sigs or nested_class_sigs):
                        if has_class_members and full_class_sig[-1] == "    ...":
                            full_class_sig.pop()
                        elif not has_class_members and not method_sigs and not nested_class_sigs and not full_class_sig[-1].endswith("..."):
                             if not (node_sig_str.strip().endswith(":") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                                pass # Already has ... or content

                        full_class_sig.extend(method_sigs)
                        full_class_sig.extend(nested_class_sigs)
                    output_signatures.append("\n".join(full_class_sig))
                else: # Top-level function
                    output_signatures.append(node_sig_str)

        if not output_signatures and code_content.strip():
            return "[No top-level functions or classes found. Showing first 5 lines.]\n" + "\n".join(lines[:5])
        elif not output_signatures:
            return "[Empty Python file]"
        return "\n\n".join(output_signatures)
    except SyntaxError as e:
        return f"[SyntaxError in Python file: {e.msg} (line {e.lineno})]"
    except Exception as e:
        return f"[Error extracting Python signatures: {e}\n{traceback.format_exc()}]"

def extract_javascript_signatures(code_content: str) -> str:
    signatures = []
    
    jsdoc_pattern_text = r"/\*\*(?:[^*]|\*(?!/))*\*\/\s*"
    
    name_pattern = r"[A-Za-z_]\w*"
    params_pattern = r"\([^)]*\)"
    
    patterns = {
        "class": re.compile(
            rf"({jsdoc_pattern_text})?(?:export\s+(?:default\s+)?)?class\s+({name_pattern})(?:\s*extends\s+{name_pattern})?\s*\{{"
        ),
        "method": re.compile(
            rf"({jsdoc_pattern_text})?\s*(static\s+|get\s+|set\s+|async\s+)?({name_pattern}|constructor)\s*{params_pattern}\s*\{{"
        ),
        "function_def": re.compile(
            rf"({jsdoc_pattern_text})?(?:export\s+(?:default\s+)?)?(async\s+)?function\s*\*?\s*({name_pattern})?\s*{params_pattern}\s*\{{"
        ),
        "arrow_func_const": re.compile(
            rf"({jsdoc_pattern_text})?(?:export\s+)?(?:const|let|var)\s+({name_pattern})\s*=\s*(async\s+)?{params_pattern}\s*=>\s*(?:\{{|(?=\w|`))"
        ),
        "func_expr_const": re.compile(
            rf"({jsdoc_pattern_text})?(?:export\s+)?(?:const|let|var)\s+({name_pattern})\s*=\s*(async\s+)?function\s*\*?\s*({name_pattern})?\s*{params_pattern}\s*\{{"
        )
    }

    # Helper to format extracted parts
    def format_signature(match_obj, kind):
        jsdoc = match_obj.group(1).strip() + "\n" if match_obj.group(1) else ""
        full_match = match_obj.group(0)
        
        if kind == "class":
            return jsdoc + full_match + "\n  // ... methods and properties ...\n}"
        elif kind in ["method", "function_def", "arrow_func_const", "func_expr_const"]:
            # Remove trailing opening brace or arrow for concise signature
            body_start_index = full_match.rfind('{')
            if body_start_index == -1 and "=>" in full_match : # arrow func without block
                 body_start_index = full_match.rfind('=>') + 2
                 return jsdoc + full_match[:body_start_index].strip() + " ... ;"


            if body_start_index != -1:
                return jsdoc + full_match[:body_start_index].strip() + " { ... }"
            return jsdoc + full_match.strip() + " { ... } // (Malformed or complex)"


    # Iterate over lines to find structures (simpler than full AST)
    # This is a basic approach and might miss complex cases or nested items perfectly.
    # A more robust solution uses a proper JS parser (e.g., esprima, acorn) but adds heavy dependencies.
    
    # Attempt to find classes and their methods
    class_matches = list(patterns["class"].finditer(code_content))
    processed_ranges = []

    for class_match in class_matches:
        signatures.append(format_signature(class_match, "class"))
        processed_ranges.append(class_match.span())
        
        # Look for methods within this class body (approximate)
        class_body_start = class_match.end()
        next_class_start = len(code_content)
        for next_cm in class_matches:
            if next_cm.start() > class_match.start():
                next_class_start = min(next_class_start, next_cm.start())
                break
        
        # Simple balancing for class body end (very approximate)
        open_braces = 1
        class_body_end = class_body_start
        for i in range(class_body_start, next_class_start):
            if code_content[i] == '{': open_braces += 1
            elif code_content[i] == '}': open_braces -= 1
            if open_braces == 0: class_body_end = i + 1; break
        class_body_end = min(class_body_end, next_class_start)

        class_body_content = code_content[class_body_start:class_body_end]
        
        for method_match in patterns["method"].finditer(class_body_content):
            formatted_method_sig = format_signature(method_match, "method")
            signatures.append("  " + formatted_method_sig.replace("\n", "\n  ")) # Indent methods
            # Add method span relative to class_body_content to avoid re-processing
            # This part is tricky with overlapping regex and simple processed_ranges
    
    # Find standalone functions (those not inside already processed class ranges)
    for func_kind in ["function_def", "arrow_func_const", "func_expr_const"]:
        for func_match in patterns[func_kind].finditer(code_content):
            is_processed = False
            for start, end in processed_ranges:
                if start <= func_match.start() < end:
                    is_processed = True; break
            if not is_processed:
                signatures.append(format_signature(func_match, func_kind))
                processed_ranges.append(func_match.span()) # Mark as processed

    if not signatures and code_content.strip():
        return "[No clear top-level functions or classes found via regex. Showing first 5 lines.]\n" + "\n".join(code_content.splitlines()[:5])
    elif not signatures:
        return "[Empty JavaScript file]"
    
    return "\n\n".join(signatures)


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
        self._active_excluded_patterns = list(DEFAULT_ALWAYS_EXCLUDED_PATTERNS)
        for folder_name in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            self._active_excluded_patterns.append(f"{folder_name}/")
            self._active_excluded_folders.add(folder_name)
        self._active_include_patterns = [p.strip().replace("\\", "/") for p in custom_inclusions_str.split(',') if p.strip()]
        
        for preset_name in selected_preset_names:
            if preset_name in PRESET_EXCLUSIONS:
                for pattern in PRESET_EXCLUSIONS[preset_name]:
                    normalized_pattern = pattern.replace("\\", "/")
                    is_mandatory_style_pattern = any(normalized_pattern.startswith(m_folder + "/") or normalized_pattern == m_folder for m_folder in _MANDATORY_EXCLUDED_FOLDER_NAMES)
                    
                    if normalized_pattern.endswith('/') and not '*' in normalized_pattern and not '?' in normalized_pattern and not '[' in normalized_pattern:
                        folder_name_to_add = normalized_pattern[:-1].lower()
                        if folder_name_to_add not in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                             self._active_excluded_folders.add(folder_name_to_add)
                    elif normalized_pattern.startswith("*.") and not '/' in normalized_pattern:
                        self._active_excluded_extensions.add(normalized_pattern[1:].lower())
                    elif not is_mandatory_style_pattern:
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

    def _is_path_hard_excluded(self, path_to_check: Path, root_scan_path: Path, hard_excluded_paths_set: Set[Path]) -> bool:
        if path_to_check in hard_excluded_paths_set:
            return True
        try:
            current = path_to_check.parent
            while current != root_scan_path.parent and current != current.parent: # Stop before filesystem root or if root_scan_path is a parent
                if current in hard_excluded_paths_set:
                    return True
                current = current.parent
        except Exception: # Should not happen with valid paths
            pass
        return False

    def _is_excluded(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        context_root = current_root_override or self._root_folder
        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower() if item.is_file() else ""
        
        if item.is_dir() and item_name_lower in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            return True

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
                if rel_path_str.startswith(dir_pattern + "/"):
                    return True
            elif "/" not in pattern:
                if fnmatch.fnmatchcase(item.name, pattern):
                    return True
            else:
                if fnmatch.fnmatchcase(rel_path_str, pattern):
                    return True
        return False

    def _is_included_by_filter(self, item: Path, current_root_override: Optional[Path] = None) -> bool:
        if not self._active_include_patterns:
            return True 
        if item.is_dir() and item.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
            return False

        context_root = current_root_override or self._root_folder
        try:
            rel_path_str = str(item.resolve().relative_to(context_root).as_posix())
        except (AttributeError, ValueError):
            rel_path_str = item.name.replace("\\", "/")

        for pattern in self._active_include_patterns:
            if fnmatch.fnmatchcase(rel_path_str, pattern):
                return True
            if item.is_dir() and pattern.endswith('/'):
                if fnmatch.fnmatchcase(rel_path_str, pattern[:-1]):
                    return True
            if item.is_dir() and "/" in rel_path_str:
                try:
                    current_path_obj_parts = Path(rel_path_str).parts
                    for i in range(len(current_path_obj_parts)):
                        parent_part_path_str = "/".join(current_path_obj_parts[:i+1])
                        if fnmatch.fnmatchcase(parent_part_path_str, pattern):
                            return True
                        if pattern.endswith("/") and fnmatch.fnmatchcase(parent_part_path_str, pattern[:-1]):
                            return True
                except:
                    pass
        return False

    def _is_text_file(self, file: Path) -> bool:
        if file.suffix.lower() in self._active_excluded_extensions and file.suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
            return False
        return file.suffix.lower() in ALLOWED_TEXT_EXTENSIONS

    def _read_file_content(self, file: Path) -> str:
        try:
            if file.stat().st_size > self._max_file_size_bytes:
                return f"[File omitted: Exceeds size limit ({self._max_file_size_bytes/(1024*1024):.2f} MB)]"
            if file.stat().st_size == 0:
                return "[Empty file]"
            content = ""
            try:
                content = file.read_text(encoding="utf-8", errors='strict')
            except UnicodeDecodeError:
                for enc in ['latin-1', 'cp1252', 'utf-16']:
                    try: 
                        content = file.read_text(encoding=enc)
                        break
                    except UnicodeDecodeError:
                        pass
                    except Exception:
                        content = f"[Error: Could not decode with {enc} or read]"
                        break
                else:
                    content = "[Error: Could not decode file with common encodings (UTF-8, Latin-1, CP1252, UTF-16)]"
            except Exception as e:
                return f"[Error reading file '{file.as_posix()}': {e}]"
            
            line_count = 0
            long_line_threshold = 5000
            excessive_long_lines_count = 0
            for line in content.splitlines():
                line_count += 1
                if len(line) > long_line_threshold:
                    excessive_long_lines_count +=1
            if line_count > 10 and excessive_long_lines_count > line_count * 0.3:
                 pass
            return content or "[File appears empty after read]"
        except OSError as e:
            return f"[OS error accessing file '{file.as_posix()}': {e}]"
        except Exception:
            return "[Unexpected error reading file]"

    def build_file_tree_json(self, folder_path_str: str, filter_settings: Dict[str, Any], hard_excluded_paths_str: List[str]) -> List[Dict[str, Any]]:
        root_path = Path(folder_path_str).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path_str}")
        
        self.setup_exclusions_and_limits(
            filter_settings.get("selected_presets", []),
            filter_settings.get("custom_folders", ""),
            filter_settings.get("custom_extensions", ""),
            filter_settings.get("custom_patterns", ""),
            [p.strip() for p in filter_settings.get("dynamic_patterns", "").split(',') if p.strip()],
            filter_settings.get("custom_inclusions", ""),
            filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB),
            root_path
        )
        hard_excluded_paths_set = {Path(p).resolve() for p in hard_excluded_paths_str}

        if self._is_path_hard_excluded(root_path, root_path, hard_excluded_paths_set):
             return [{"name": root_path.name, "path": str(root_path.as_posix()), "is_dir": True, "is_text": False, "can_be_checked": False, "is_signature_candidate": False, "tooltip":"Hard excluded by user.", "children": []}]


        return [{
            "name": root_path.name,
            "path": str(root_path.as_posix()),
            "is_dir": True,
            "is_text": False,
            "can_be_checked": True,
            "is_signature_candidate": False,
            "children": self._collect_tree_data_recursive(root_path, root_path, hard_excluded_paths_set)
        }]

    def _collect_tree_data_recursive(self, current_dir_path: Path, root_scan_path: Path, hard_excluded_paths_set: Set[Path]) -> List[Dict[str, Any]]:
        items_data = []
        try: 
            paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError) as e:
            error_type = 'Permission Denied' if isinstance(e,PermissionError) else 'OS Error'
            return [{
                "name": f"[{error_type}: {current_dir_path.name}]",
                "path": str(current_dir_path.as_posix()),
                "is_dir": True, "is_text": False, "can_be_checked": False,
                "is_signature_candidate": False, "error": True, "tooltip": f"Cannot access: {e}"
            }]
        
        for path_obj in paths_in_dir:
            resolved_path_obj = path_obj.resolve()
            if self._is_path_hard_excluded(resolved_path_obj, root_scan_path, hard_excluded_paths_set):
                continue

            if path_obj.is_dir() and path_obj.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                continue

            is_item_excluded = self._is_excluded(path_obj, root_scan_path)
            is_item_included_by_filter = self._is_included_by_filter(path_obj, root_scan_path)
            
            item_data = {
                "name": path_obj.name,
                "path": str(path_obj.as_posix()),
                "is_dir": path_obj.is_dir(), 
                "children": [],
                "error": False,
                "tooltip": "",
                "is_signature_candidate": False
            }
            can_be_checked_final = True
            
            if item_data["is_dir"]:
                item_data["is_text"] = False
                can_be_checked_final = not is_item_excluded or is_item_included_by_filter
                item_data["children"] = self._collect_tree_data_recursive(path_obj, root_scan_path, hard_excluded_paths_set)
                if not item_data["children"] and is_item_excluded and not is_item_included_by_filter:
                    can_be_checked_final = False
            else:
                item_data["is_text"] = self._is_text_file(path_obj)
                file_too_large = False
                try: 
                    if item_data["is_text"]:
                        file_too_large = path_obj.stat().st_size > self._max_file_size_bytes
                        if file_too_large:
                            item_data["tooltip"] = f"File size exceeds limit ({self._max_file_size_bytes/(1024*1024):.2f}MB)"
                except OSError as e: 
                    file_too_large = True
                    item_data["tooltip"] = f"Cannot get file size: {e}"

                if not item_data["is_text"]:
                    item_data["tooltip"] = "Binary or non-text file type"
                    can_be_checked_final = False
                elif is_item_excluded and not is_item_included_by_filter:
                    item_data["tooltip"] = "Excluded by filters"
                    can_be_checked_final = False
                elif file_too_large:
                    can_be_checked_final = False
                elif is_item_included_by_filter:
                    can_be_checked_final = item_data["is_text"] and not file_too_large
                else:
                     can_be_checked_final = item_data["is_text"] and not file_too_large
                
                if can_be_checked_final and item_data["is_text"] and (path_obj.suffix.lower() in ['.py', '.js']):
                    item_data["is_signature_candidate"] = True

            item_data["can_be_checked"] = can_be_checked_final
            items_data.append(item_data)
        return items_data

    def _get_all_displayable_paths(self, current_dir_path: Path, root_scan_path: Path, hard_excluded_paths_set: Set[Path]) -> List[Path]:
        all_paths = []
        try:
            paths_in_dir = sorted(list(current_dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except (PermissionError, OSError):
            return [] 

        for path_obj in paths_in_dir:
            resolved_path_obj = path_obj.resolve()
            if self._is_path_hard_excluded(resolved_path_obj, root_scan_path, hard_excluded_paths_set):
                continue

            if path_obj.is_dir() and path_obj.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                continue

            is_excluded_by_rules = self._is_excluded(path_obj, root_scan_path)
            is_included_by_filter = self._is_included_by_filter(path_obj, root_scan_path)
            is_displayable_in_tree = True
            
            if path_obj.is_file():
                if not self._is_text_file(path_obj): 
                    is_displayable_in_tree = False
                else:
                    try:
                        if path_obj.stat().st_size > self._max_file_size_bytes:
                            is_displayable_in_tree = False
                    except OSError: 
                        is_displayable_in_tree = False
            
            if not is_displayable_in_tree:
                pass
            elif is_excluded_by_rules and not is_included_by_filter:
                is_displayable_in_tree = False

            if is_displayable_in_tree:
                all_paths.append(resolved_path_obj)
                if path_obj.is_dir(): 
                    all_paths.extend(self._get_all_displayable_paths(path_obj, root_scan_path, hard_excluded_paths_set))
        return all_paths

    def _generate_tree_markdown_from_paths(self, root_path: Path, paths_for_tree_structure: List[str]) -> List[str]:
        if not paths_for_tree_structure:
            return ["*No items to display in the file tree based on current filters.*"] 
        
        resolved_root_path = root_path.resolve()
        hierarchy: Dict[str, Any] = {}
        all_nodes_to_represent_resolved = set()

        for p_str_raw in paths_for_tree_structure:
            p_resolved = Path(p_str_raw).resolve()
            all_nodes_to_represent_resolved.add(p_resolved)
            try:
                if p_resolved != resolved_root_path and resolved_root_path in p_resolved.parents:
                    current_parent = p_resolved.parent
                    while current_parent != resolved_root_path and resolved_root_path in current_parent.parents:
                        all_nodes_to_represent_resolved.add(current_parent)
                        if current_parent == current_parent.parent:
                            break
                        current_parent = current_parent.parent
                    all_nodes_to_represent_resolved.add(resolved_root_path)
            except (ValueError, AttributeError): 
                 pass
        
        if not all_nodes_to_represent_resolved and resolved_root_path.is_dir(): 
            all_nodes_to_represent_resolved.add(resolved_root_path)

        def get_sort_key(x_path):
            try:
                if resolved_root_path in x_path.parents or x_path == resolved_root_path:
                    return (len(x_path.relative_to(resolved_root_path).parts), str(x_path.as_posix()).lower())
                else:
                    return (0, str(x_path.as_posix()).lower())
            except ValueError:
                 return (0, str(x_path.as_posix()).lower())

        sorted_nodes = sorted(list(all_nodes_to_represent_resolved), key=get_sort_key)

        for node_path_resolved in sorted_nodes:
            try: 
                if node_path_resolved == resolved_root_path:
                    parts = ()
                elif resolved_root_path in node_path_resolved.parents:
                    parts = node_path_resolved.relative_to(resolved_root_path).parts
                else:
                    parts = (node_path_resolved.name,)
            except (ValueError, AttributeError): 
                parts = (node_path_resolved.name,)
            
            current_level = hierarchy
            for part in parts:
                current_level = current_level.setdefault(part, {})
            current_level["_isfile_"] = node_path_resolved.is_file()

        if not hierarchy and resolved_root_path in all_nodes_to_represent_resolved : 
            hierarchy.setdefault("_isfile_", resolved_root_path.is_file())

        def format_level(level_dict: Dict[str, Any], current_prefix: str) -> List[str]:
            lines = []
            items_to_display = {k:v for k,v in level_dict.items() if not k.startswith("_")}
            sorted_names = sorted(items_to_display.keys(), key=lambda k: (items_to_display[k].get("_isfile_", False), k.lower()))
            
            for i, name in enumerate(sorted_names):
                node_details = items_to_display[name]
                is_last_item_in_level = (i == len(sorted_names) - 1)
                is_actually_a_file = node_details.get("_isfile_", False)
                icon = FILE_ICON_STR if is_actually_a_file else FOLDER_ICON_STR
                
                lines.append(f"{current_prefix}{TREE_LAST if is_last_item_in_level else TREE_BRANCH}{icon} {name}{'' if is_actually_a_file else '/'}")
                
                children_dict = {k_c: v_c for k_c, v_c in node_details.items() if not k_c.startswith("_")}
                if not is_actually_a_file and children_dict:
                    lines.extend(format_level(children_dict, current_prefix + (TREE_SPACE if is_last_item_in_level else TREE_VLINE)))
            return lines

        tree_title = f"{FOLDER_ICON_STR} {resolved_root_path.name}/"
        formatted_tree_lines = format_level(hierarchy, "")
        
        if not formatted_tree_lines and resolved_root_path.is_dir() and not paths_for_tree_structure:
             pass
        elif not formatted_tree_lines and resolved_root_path.is_dir():
            pass

        return [tree_title] + formatted_tree_lines if (formatted_tree_lines or resolved_root_path.is_dir()) else ["*No items to display in the file tree based on current filters.*"]


    def _generate_file_contents_markdown(self, root_folder: Path, selected_files_info: List[Dict[str, str]]) -> List[str]: 
        content_lines = ["", "---", "", "## File Contents"]
        if not selected_files_info:
            content_lines.append("\n*No files selected or specified for content/signatures.*")
            return content_lines
        
        resolved_root_folder = root_folder.resolve()
        files_to_process_with_type = []

        for file_info in selected_files_info:
            path_str = file_info["path"]
            selection_type = file_info["type"]
            
            try:
                path = Path(path_str).resolve()
            except Exception:
                continue
            
            if not path.is_file():
                continue

            is_in_mandatory_excluded_dir = False
            try:
                current_check_path = path.parent
                while current_check_path != resolved_root_folder and current_check_path != current_check_path.parent:
                    if current_check_path.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES:
                        is_in_mandatory_excluded_dir = True
                        break
                    current_check_path = current_check_path.parent
            except Exception:
                pass
            if is_in_mandatory_excluded_dir:
                continue

            try:
                path.relative_to(resolved_root_folder)
            except ValueError:
                continue

            is_item_excluded = self._is_excluded(path, resolved_root_folder)
            is_item_included_by_filter = self._is_included_by_filter(path, resolved_root_folder)
            is_text = self._is_text_file(path)
            is_too_large = False
            try:
                if is_text:
                    is_too_large = path.stat().st_size > self._max_file_size_bytes
            except OSError:
                is_too_large = True
            
            can_show_anything = is_text and not is_too_large and (not is_item_excluded or is_item_included_by_filter)
            if can_show_anything:
                files_to_process_with_type.append({"path_obj": path, "type": selection_type, "is_text": is_text})
        
        try:
            files_to_process_with_type.sort(
                key=lambda item: str(item["path_obj"].relative_to(resolved_root_folder).as_posix() 
                                     if (resolved_root_folder in item["path_obj"].parents or item["path_obj"] == resolved_root_folder) 
                                     else item["path_obj"].name).lower())
        except Exception:
            pass

        if not files_to_process_with_type:
             content_lines.append("\n*No valid text files for content/signature display based on filters, limits, context.*")
             return content_lines

        for item_info in files_to_process_with_type:
            file_path = item_info["path_obj"]
            selection_type = item_info["type"]
            is_file_text = item_info["is_text"]

            rel_path_str = str(file_path.relative_to(resolved_root_folder).as_posix()) if (resolved_root_folder in file_path.parents or file_path == resolved_root_folder) else file_path.name
            content_lines.append(f"\n### `{rel_path_str}`")
            
            file_content_str = ""
            lang_for_block = (file_path.suffix[1:] if file_path.suffix else "text").lower()
            lang_for_block = "".join(c for c in lang_for_block if c.isalnum()) or "text"
            
            if selection_type == "signatures" and is_file_text:
                raw_content_for_sig_extraction = self._read_file_content(file_path)
                if raw_content_for_sig_extraction.startswith(("[Error", "[File omitted", "[OS error")):
                    file_content_str = raw_content_for_sig_extraction
                elif file_path.suffix.lower() == ".py":
                    file_content_str = extract_python_signatures(raw_content_for_sig_extraction)
                    lang_for_block = "python"
                elif file_path.suffix.lower() == ".js":
                    file_content_str = extract_javascript_signatures(raw_content_for_sig_extraction)
                    lang_for_block = "javascript"
                else:
                    file_content_str = f"[Signatures for non-Py/JS. Full content instead.]\n{self._read_file_content(file_path)}"
            elif is_file_text:
                file_content_str = self._read_file_content(file_path)
            else:
                file_content_str = "[Not text or unreadable.]"

            aliases = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript', 'jsx': 'javascript', 'md': 'markdown', 'sh': 'bash', 'yml': 'yaml', 'dockerfile': 'dockerfile', 'h': 'c', 'hpp': 'cpp', 'cs': 'csharp', 'rb': 'ruby', 'pl': 'perl', 'kt': 'kotlin', 'rs': 'rust', 'go': 'golang', 'html': 'html', 'css': 'css', 'scss': 'scss', 'vue': 'vue', 'java': 'java', 'xml': 'xml', 'json': 'json', 'sql': 'sql', 'php': 'php', 'conf': 'ini', 'cfg':'ini', 'properties':'ini', 'bat': 'batch', 'ps1': 'powershell', 'makefile':'makefile'}
            final_lang = aliases.get(lang_for_block, lang_for_block)
            content_lines.extend([f"```{final_lang}", *(file_content_str.splitlines() if file_content_str else [""]), "```"])
        return content_lines

    def generate_structure_text(
        self, folder_path_str: str, filter_settings: Dict[str, Any], custom_prompt: str = "",
        documentation_content: str = "", selected_files_info: Optional[List[Dict[str, str]]] = None,
        hard_excluded_paths_str: Optional[List[str]] = None
    ) -> str:
        try:
            self._root_folder = Path(folder_path_str).resolve()
            if not self._root_folder.is_dir():
                raise ValueError(f"Path is not a directory: {self._root_folder}")
        except Exception as e:
            raise ValueError(f"Invalid folder path '{folder_path_str}': {e}")
        
        self.setup_exclusions_and_limits(
            filter_settings.get("selected_presets", []),
            filter_settings.get("custom_folders", ""),
            filter_settings.get("custom_extensions", ""),
            filter_settings.get("custom_patterns", ""),
            [p.strip() for p in filter_settings.get("dynamic_patterns", "").split(',') if p.strip()],
            filter_settings.get("custom_inclusions", ""),
            filter_settings.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB),
            self._root_folder
        )

        current_hard_excluded_paths_set = {Path(p).resolve() for p in hard_excluded_paths_str} if hard_excluded_paths_str else set()
        
        all_displayable_paths_resolved = self._get_all_displayable_paths(self._root_folder, self._root_folder, current_hard_excluded_paths_set)
        all_displayable_paths_str_posix = [str(p.as_posix()) for p in all_displayable_paths_resolved]
        
        if self._is_path_hard_excluded(self._root_folder, self._root_folder, current_hard_excluded_paths_set):
            tree_lines = [f"{FOLDER_ICON_STR} {self._root_folder.name}/ (Hard excluded by user)"]
        else:
            tree_lines = self._generate_tree_markdown_from_paths(self._root_folder, all_displayable_paths_str_posix)

        structure_output_lines = [
            f"# Folder Structure: {self._root_folder.name}",
            f"*(Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*",
            "",
            "```text",
            *tree_lines,
            "```"
        ]
        
        valid_selected_info_for_content = []
        if selected_files_info:
            for item_info in selected_files_info:
                p_str = item_info["path"]
                sel_type = item_info["type"]
                try:
                    p_abs = Path(p_str).resolve()
                    if self._is_path_hard_excluded(p_abs, self._root_folder, current_hard_excluded_paths_set):
                        continue 

                    is_in_mandatory_excluded_dir = False
                    temp_parent = p_abs.parent
                    while temp_parent != self._root_folder.parent and temp_parent != temp_parent.parent:
                        if temp_parent.name.lower() in _MANDATORY_EXCLUDED_FOLDER_NAMES and temp_parent.is_relative_to(self._root_folder):
                            is_in_mandatory_excluded_dir = True
                            break
                        temp_parent = temp_parent.parent
                    if not is_in_mandatory_excluded_dir:
                        valid_selected_info_for_content.append({"path": str(p_abs.as_posix()), "type": sel_type})
                except Exception:
                    pass

        content_output_lines = self._generate_file_contents_markdown(self._root_folder, valid_selected_info_for_content)
        full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)
        final_prompt_parts = []
        
        if documentation_content and documentation_content.strip():
            final_prompt_parts.append("## Imported Documentation\n\n" + documentation_content.strip())
        if custom_prompt and custom_prompt.strip():
            final_prompt_parts.append("## Custom Instructions\n\n" + custom_prompt.strip())
        
        if final_prompt_parts:
            full_output += "\n\n---\n\n" + "\n\n---\n\n".join(final_prompt_parts)
        
        return full_output.strip()

app = FastAPI(title="Folder Structure Extractor Web App", version="2.8.3")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
folder_processor = FolderProcessor()

class FileSelectionInfo(BaseModel):
    path: str
    type: str

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
    hard_excluded_paths: List[str] = []


class GenerateRequest(BaseModel):
    folder_path: str
    filters: FilterSettings
    selected_files_info: List[FileSelectionInfo]
    custom_prompt: str
    loaded_doc_paths: List[str]
    hard_excluded_paths: List[str] = []

class EnvironmentSettings(BaseModel):
    folder_path: str
    selected_presets: List[str]
    custom_folders: str
    custom_extensions: str
    custom_patterns: str
    dynamic_patterns: str
    custom_inclusions: str
    max_file_size_mb: float
    save_output_checked: bool
    custom_prompt: str
    current_theme_file: str = "default_light.qss"
    prompt_templates: List[Template]
    loaded_doc_paths: List[str]
    checked_tree_paths_map: Dict[str, str]
    hard_excluded_paths_abs: List[str] # For client-side storage
    version: str = "2.8.3"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not serve frontend: {e}")

async def asyncio_to_thread(func, *args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(executor, functools.partial(func, *args, **kwargs))

@app.post("/api/load_project_tree")
async def load_project_tree(request: LoadTreeRequest):
    if not request.folder_path:
        raise HTTPException(status_code=400, detail="Folder path empty.")
    folder_path = Path(request.folder_path)
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {request.folder_path}")
    try:
        tree_data = await asyncio_to_thread(
            folder_processor.build_file_tree_json,
            request.folder_path,
            request.filters.model_dump(),
            request.hard_excluded_paths
        )
        return JSONResponse(content={"tree": tree_data})
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tree: {e}")

def _get_folder_path_from_pyqt5_dialog():
    app_instance = QApplication.instance()
    if app_instance is None:
        app_argv = sys.argv if sys.argv else ['']
        app_instance = QApplication(app_argv)
    selected_path = QFileDialog.getExistingDirectory(None, "Select Project Folder on Server", os.path.expanduser("~"))
    return selected_path

@app.post("/api/browse_server_folder")
async def browse_server_folder():
    if not _PYQT5_AVAILABLE:
        raise HTTPException(status_code=501, detail="PyQt5 not available on server.")
    try:
        path = await asyncio_to_thread(_get_folder_path_from_pyqt5_dialog)
        return {"status": "success" if path else "cancelled", "path": str(Path(path).as_posix()) if path else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server dialog error: {e}")

@app.post("/api/generate_structure")
async def generate_structure(request: GenerateRequest):
    if not request.folder_path:
        raise HTTPException(status_code=400, detail="Folder path empty.")
    folder_path = Path(request.folder_path)
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {request.folder_path}")
    try:
        doc_parts = []
        if request.loaded_doc_paths:
            for doc_path_str in request.loaded_doc_paths:
                doc_p = Path(doc_path_str)
                if doc_p.is_file():
                    try:
                        doc_parts.append(f"\n---\n**Doc: `{doc_p.name}`**\n\n{doc_p.read_text(encoding='utf-8', errors='ignore').strip()}\n---")
                    except Exception as e_d:
                        doc_parts.append(f"\n---\n**Doc: `{doc_p.name}` [Error: {e_d}]**\n---")
                else:
                    doc_parts.append(f"\n---\n**Doc: `{doc_p.name}` [Not found/not file]**\n---")
        full_doc_content = "\n".join(doc_parts)
        final_prompt = apply_placeholders(request.custom_prompt, request.folder_path)
        selected_info_for_processor = [item.model_dump() for item in request.selected_files_info]

        text = await asyncio_to_thread(
            folder_processor.generate_structure_text,
            request.folder_path,
            request.filters.model_dump(),
            final_prompt,
            full_doc_content,
            selected_info_for_processor,
            request.hard_excluded_paths
        )
        return JSONResponse(content={"markdown": text})
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate: {e}")

@app.get("/api/prompt_templates")
async def get_prompt_templates():
    return JSONResponse(content=[t.model_dump() for t in _user_prompt_templates])

@app.post("/api/save_template")
async def save_template(template: Template):
    global _user_prompt_templates
    is_pristine = any(td_raw['name'] == template.name and td_raw['content'] == template.content for td_raw in DEFAULT_AI_PROMPT_TEMPLATES_RAW)
    idx = next((i for i, t_curr in enumerate(_user_prompt_templates) if t_curr.name == template.name), -1)
    
    if idx != -1:
        if is_pristine:
            _user_prompt_templates[idx] = Template(**next(item for item in DEFAULT_AI_PROMPT_TEMPLATES_RAW if item["name"] == template.name))
            msg = "reverted"
            stat = "reverted_to_default"
        else:
            _user_prompt_templates[idx] = template
            msg = "updated"
            stat = "success"
    else:
        _user_prompt_templates.append(template)
        msg = "saved new"
        stat = "success"
        
    _user_prompt_templates.sort(key=lambda t: t.name.lower())
    return JSONResponse({"status": stat, "message": f"Template '{template.name}' {msg}.", "templates": [t.model_dump() for t in _user_prompt_templates]})

@app.post("/api/delete_template")
async def delete_template(template_data: Template):
    global _user_prompt_templates
    name_del = template_data.name
    orig_def = next((td_raw for td_raw in DEFAULT_AI_PROMPT_TEMPLATES_RAW if td_raw['name'] == name_del), None)
    curr_idx = next((i for i, t in enumerate(_user_prompt_templates) if t.name == name_del), -1)

    if curr_idx == -1:
        raise HTTPException(status_code=404, detail=f"Template '{name_del}' not found.")
    
    if orig_def:
        _user_prompt_templates[curr_idx] = Template(**orig_def)
        msg = "reverted"
        stat = "reverted_default"
    else:
        del _user_prompt_templates[curr_idx]
        msg = "deleted"
        stat = "deleted_custom"
        
    _user_prompt_templates.sort(key=lambda t: t.name.lower())
    return JSONResponse({"status": stat, "message": f"Template '{name_del}' {msg}.", "templates": [t.model_dump() for t in _user_prompt_templates]})

@app.post("/api/save_environment")
async def save_environment(settings: EnvironmentSettings):
    return JSONResponse(content={"status": "success", "message": "Env settings received by server.", "settings": settings.model_dump()})

@app.post("/api/load_documentation_content")
async def load_documentation_content(doc_paths_request: Dict[str, List[str]]):
    doc_paths = doc_paths_request.get("doc_paths", [])
    if not isinstance(doc_paths, list):
        raise HTTPException(status_code=400, detail="Invalid doc_paths format.")
    doc_parts = []
    for p_str in doc_paths:
        if not isinstance(p_str, str):
            doc_parts.append(f"\n---\n**Invalid Path Entry [{type(p_str)}]**\n---")
            continue
        p = Path(p_str)
        if p.is_file():
            try:
                doc_parts.append(f"\n---\n**Doc: `{p.name}`**\n\n{p.read_text(encoding='utf-8',errors='ignore').strip()}\n---")
            except Exception as e:
                doc_parts.append(f"\n---\n**Doc: `{p.name}` [Error: {e}]**\n---")
        else:
            doc_parts.append(f"\n---\n**Doc: `{p.name}` [Not found/file at: {p_str}]**\n---")
    return JSONResponse(content={"content": "\n\n".join(doc_parts) if doc_parts else "No docs processed."})

def find_free_port(host="127.0.0.1", start_port=8000, max_tries=100):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            try:
                s.bind((host, port))
                return port
            except OSError as e:
                if e.errno == socket.errno.EADDRINUSE:
                    if port == start_port + max_tries - 1:
                        raise
                    continue
                else:
                    raise
    raise OSError(f"No free port found after {max_tries} tries, starting from port {start_port}.")

if __name__ == "__main__":
    import uvicorn
    if not _user_prompt_templates or len(_user_prompt_templates) != len(DEFAULT_AI_PROMPT_TEMPLATES_RAW):
        _user_prompt_templates = [Template(**td) for td in DEFAULT_AI_PROMPT_TEMPLATES_RAW]
        _user_prompt_templates.sort(key=lambda t: t.name.lower())

    host = "127.0.0.1"
    default_port = 8000
    port_to_use = default_port
    try:
        port_to_use = find_free_port(host, default_port)
    except OSError:
        pass
    
    url = f"http://{host}:{port_to_use}"
    
    def open_browser_when_ready():
        time.sleep(2.0)
        try:
            with socket.create_connection((host, port_to_use), timeout=1.0):
                 webbrowser.open_new_tab(url)
        except Exception:
            pass

    threading.Timer(0.1, open_browser_when_ready).start()
    
    try:
        uvicorn.run(app, host=host, port=port_to_use, log_level="info")
    except SystemExit:
        pass
    except socket.error:
        pass
    except Exception:
        traceback.print_exc()

