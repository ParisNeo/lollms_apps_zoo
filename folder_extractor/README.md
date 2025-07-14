# Folder Structure to Text (Folder Extractor) v3.0

**Author:** ParisNeo with Gemini
**Category:** Developer Tools, Utilities, AI Tools
**License:** MIT

## Overview

Folder Structure to Text is a powerful web-based utility designed to help developers, technical writers, and AI prompt engineers analyze and document software projects. It generates a comprehensive Markdown representation of a folder's structure, including optional file contents or code signatures.

The application now features a full **Project Management Dashboard**, allowing you to save, manage, and quickly access multiple projects. A key enhancement is the integration with **AI language models** (like Lollms or any OpenAI-compatible service) to intelligently suggest which files are relevant to a specific development task, streamlining the process of building context for feature development or bug fixing.

## Core Features

*   **Project Management Dashboard:**
    *   Save and manage a list of your projects.
    *   "Star" important projects for easy access.
    *   CRUD (Create, Read, Update, Delete) functionality for your project list.
*   **AI-Powered File Selection:**
    *   Connect to any OpenAI-compatible LLM service (e.g., `lollms-chat`).
    *   Provide a natural language goal (e.g., "implement user authentication").
    *   The AI will analyze your project's file list and automatically select the most relevant files for the task.
*   **Advanced Tree Generation & Filtering:**
    *   Generates a visual, text-based tree of your project's folder structure.
    *   Includes full file content or, for Python/JavaScript, extracts high-level code signatures (classes and functions).
    *   **Smart Refresh Options:** When reloading a project tree, choose to either preserve your manually selected files or have the app automatically re-select files based on presets.
    *   Extensive filtering capabilities:
        *   **Exclusion Presets:** Quickly ignore common files and folders for Python, Node.js, Java, and more.
        *   **Custom Rules:** Exclude specific folders, extensions, or glob patterns.
        *   **Inclusion Rules:** Ensure specific files or folders are always included, overriding any exclusion rules.
*   **Customizable AI Prompting Workflow:**
    *   **Prompt Templates:** Create, save, and manage reusable prompt templates with dynamic placeholders (`{FOLDER_NAME}`, `{DATE}`, etc.).
    *   **Documentation Integration:** Append external documentation files directly into your prompt context.
*   **Modern Web Interface:**
    *   A clean, responsive UI built with FastAPI and TailwindCSS.
    *   Full support for light and dark themes.
    *   All settings are saved in your browser's local storage for persistence.

## Installation

### Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)

### Running the Application

The application uses `pipmaster` to automatically install its dependencies on the first run.

1.  Save the `server.py` script.
2.  Create a `static` folder in the same directory and place `index.html`, `main.js`, and `style.css` inside it (if they are provided as separate files).
3.  Navigate to the directory in your terminal.
4.  Run the server:
    ```bash
    python server.py
    ```
5.  The application will automatically open in your default web browser at `http://127.0.0.1:8765`.

## How to Use

### 1. Project Dashboard

*   When you first launch the app, you'll see the project dashboard.
*   Click **"Add New Project"** to add your first project by providing a name and browsing to its folder path on the server.
*   Your projects will appear as cards. You can **star**, **edit**, or **delete** them.
*   Click on a project card to open the main **Extractor View**.

### 2. Extractor View (Loading a Project)

*   **Tab 1: Project & Filters:**
    *   Your project path is pre-filled.
    *   Configure exclusion/inclusion filters and set the max file size for content extraction.
    *   **(New) LLM Settings:** Enter the URL and API Key for your OpenAI-compatible LLM service.
    *   Click **"Load Project Tree"**.
*   **Tab 2: Explorer & Prompt:**
    *   The file tree for your project is displayed. You can manually check files for **full content** or click the **'S'** button for **signatures** (for `.py`/`.js` files).
    *   **(New) Refreshing:** The "Refresh" button will now ask if you want to **Preserve** your current selections or **Repopulate** them based on project presets.
    *   **(New) AI Select:** Click **"AI Select..."**, enter your goal (e.g., "fix login bug"), and let the configured LLM check the most relevant files for you.
    *   Select and load an AI prompt template, or write your own custom instructions.
*   **Tab 3: Output:**
    *   Click **"Generate Structure Text"**.
    *   The final Markdown output, combining your instructions, the folder tree, and selected file contents/signatures, will be generated.
    *   You can view the raw Markdown, see a rendered preview, and copy it to your clipboard.

## License

This project is licensed under the MIT License.
