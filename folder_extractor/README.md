# Folder Structure to Text (Folder Extractor) v2.3

**Author:** ParisNeo with Gemini 2.5
**Category:** Developer Tools, Utilities, AI Tools
**License:** MIT (Assumed)

## Overview

Folder Structure to Text is a comprehensive PyQt5 application designed to generate a Markdown-formatted text representation of a specified folder's structure and its contents. It allows users to select a project folder, customize inclusion and exclusion rules (using presets, specific folder/file names, extensions, and glob patterns), and control aspects like maximum file size for content extraction.

This tool is particularly useful for:
*   **Developers:** Quickly generating an overview of a project's layout and key files.
*   **Technical Writers:** Creating documentation that includes code snippets and file structures.
*   **AI Users/Prompt Engineers:** Preparing detailed context from a codebase for Large Language Models (LLMs).
*   **General Documentation:** Archiving or sharing the state and content of a folder.

It features a user-friendly interface with theme support, environment settings management (load/save configurations), integration of external documentation files into the output, and customizable AI prompt templates to streamline workflows.

## Features

*   **Text-Based Folder Tree:** Generates a visual tree representation of folder structures (e.g., `📁my_folder/`, `📄my_file.py`).
*   **File Content Inclusion:** Includes the content of text-based files directly in the output, formatted within Markdown code blocks.
*   **Markdown Output:** Produces a single, well-formatted Markdown document.
*   **Advanced Filtering:**
    *   **Exclusion Presets:** Common presets for Python, Node.js, C/C++, Rust, Java projects to quickly ignore typical build artifacts, virtual environments, etc.
    *   **Custom Exclusions:** Define specific folder names, file extensions, and glob patterns (e.g., `*.log`, `temp_*/`) to exclude.
    *   **Custom Inclusions:** Specify paths or glob patterns (e.g., `src/main/`, `README.md`, `docs/*.md`) to ensure specific files/folders are included, even if they might otherwise be filtered.
    *   **Dynamic Exclusions:** Add patterns that are dynamically evaluated during generation.
*   **File Size Limit:** Configurable maximum file size (in MB) for including file content, preventing overly large outputs.
*   **User-Friendly GUI:**
    *   Built with PyQt5 for a responsive desktop experience.
    *   Theme support via `qt_material` for customizable dark and light modes.
    *   Tabbed interface for settings and output.
*   **Environment & Configuration Management:**
    *   **Save/Load Environments:** Save all current settings (folder path, filters, prompt, theme, etc.) to a JSON file and load them back later.
    *   **Recent Environments:** Quickly access recently used environment configuration files.
*   **AI Prompting Assistance:**
    *   **Prompt Templates:** Create, save, and manage reusable prompt templates. Supports placeholders like `{FOLDER_NAME}`, `{AUTHOR}`, `{DATE}`, etc., which are automatically filled.
    *   **Interactive AI Workflow Support:** Default templates include standard AI interaction sequences (e.g., `[CONFIRM_PLAN]`, `[CONFIRM_FILE: path/to/file.ext]`).
    *   **Documentation Integration:** Import content from external Markdown or text files directly into the final output, often used to provide supplementary context to an AI.
*   **Output Management:**
    *   **Raw Markdown Display:** View the generated Markdown directly.
    *   **Rendered Preview:** A basic preview of how the Markdown might look when rendered.
    *   **Copy to Clipboard:** Easily copy the full raw Markdown output.
    *   **Auto-Save Option:** Optionally save the generated Markdown to a file automatically upon generation.
*   **Status Bar:** Provides feedback, warnings, and error messages.
*   **Icon Integration:** Uses `qtawesome` and local SVG assets for a more polished user experience.

## Installation

### Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)

### Dependencies

The application uses `pipmaster` to ensure Python packages are installed. If you don't have `pipmaster`, install it first:
```bash
pip install pipmaster
```
Then, upon first run, `pipmaster` will attempt to install the following required packages:
*   `PyQt5`
*   `markdown`
*   `qt_material`
*   `qtawesome`

Alternatively, you can pre-install them:
```bash
pip install PyQt5 markdown qt_material qtawesome
```

### Running the Application

1.  Ensure all prerequisites and dependencies are installed.
2.  Save the `server.py` file and the `assets/` folder (if provided with icons) in a directory, for example, `folder_extractor/`.
    ```
    📁 folder_extractor/
    ├─ 📁 assets/  (contains .svg icons if used)
    └─ 📄 server.py
    ```
3.  Navigate to this directory in your terminal.
4.  Run the script:
    ```bash
    python server.py
    ```

## Usage

1.  **Launch the Application:** Execute `python server.py`.
2.  **Select Target Folder:**
    *   Click the "Browse..." button or type the path to the project folder you want to analyze into the "Target Project Folder" field.
3.  **Configure Settings (Settings Tab):**
    *   **Exclusion Presets:** Select one or more presets (e.g., "Python Project") from the list to apply common exclusion rules.
    *   **Custom Filtering:**
        *   **Exclude Folders:** Enter comma-separated folder names to exclude (e.g., `docs,temp`).
        *   **Exclude Exts:** Enter comma-separated extensions to exclude (e.g., `.log,.tmp`).
        *   **Exclude Patterns:** Enter comma-separated glob patterns for exclusion (e.g., `*.bak`, `cache_*/`).
        *   **Dynamic Exclude:** Add more specific exclusion patterns.
        *   **Include Paths/Patterns:** Crucially, specify files or folders to *ensure* they are included (e.g., `src/core/important_module.py`, `config/*.json`). This can override broad exclusion rules for specific items.
    *   **Generation Options:**
        *   **Max File Size:** Set the maximum size (in MB) for a file's content to be included.
        *   **Save Markdown output automatically:** Check if you want the output to be saved to a file immediately after generation.
    *   **Documentation Integration:**
        *   Click "Add Docs..." to select Markdown (`.md`, `.markdown`) or text (`.txt`) files. Their content will be prepended to the "Custom Instructions Prompt" section in the final output.
        *   Manage added files with "Remove Selected" or "Clear All".
    *   **Custom Instructions Prompt:**
        *   Select a pre-defined AI prompt template from the "Template" dropdown (e.g., "AI: Add New Feature").
        *   Click "Load" to populate the text area with the template content. Placeholders like `{FOLDER_NAME}` will be resolved.
        *   Modify the prompt as needed or write your own from scratch.
        *   Use "Save As..." to save the current text area content as a new template.
        *   Click "Manage..." to add, edit, remove, or copy your custom prompt templates.
4.  **Generate Output:**
    *   Click the "Generate Structure Text" button.
    *   The application will process the folder based on your settings.
5.  **View Output (Output Tab):**
    *   **Raw Markdown:** Shows the complete generated Markdown text.
    *   **Rendered Preview:** Provides a basic HTML rendering of the Markdown.
    *   Use "Copy Raw Markdown" to copy the content to your clipboard.
    *   Use "Clear Output" to empty the output areas.
6.  **Managing Environments (File Menu):**
    *   **Save Environment / Save Environment As...:** Save your current settings (folder path, all filters, prompt, theme, etc.) to a JSON file for later reuse.
    *   **Load Environment... / Load Recent Environment:** Load previously saved settings.
    *   **New Project:** Clears the folder path and output, but keeps current settings for a new analysis.
7.  **Changing Themes (View Menu):**
    *   Select a theme from the "Theme" submenu to change the application's appearance.

## Placeholders for Prompts

The following placeholders can be used in custom prompt templates and will be automatically substituted:

*   `{FOLDER_NAME}`: Name of the selected target folder.
*   `{FOLDER_PATH}`: Full path to the selected target folder.
*   `{DATE}`: Current date (YYYY-MM-DD).
*   `{TIME}`: Current time (HH:MM:SS).
*   `{DATETIME}`: Current date and time (YYYY-MM-DD HH:MM:SS).
*   `{AUTHOR}`: Current system username.
*   `{USER_REQUEST}`: (Used internally by default AI templates) Placeholder for the specific user request.

## File Structure (of this tool)

```text
📁 folder_extractor/
├─ 📁 assets/         # Contains .svg icons for the UI
└─ 📄 server.py       # The main Python application script
```

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests. For bugs or feature requests, please open an issue. (Note: Assumes a public repository setup)

## License

This project is licensed under the Apache 2.0 License.