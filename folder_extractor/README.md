# Folder Structure to Text (Folder Extractor) v3.5

**Author:** ParisNeo with Gemini
**Category:** Developer Tools, Utilities, AI Tools
**License:** MIT

## Overview

Folder Structure to Text is a powerful web-based utility designed to help developers, technical writers, and AI prompt engineers analyze and document software projects. It generates a comprehensive Markdown representation of a folder's structure, including optional file contents or code signatures.

The application now features a full **Project Management Dashboard**, integration with **AI language models** for intelligent file selection, and a new **Context-Aware Discussion Tab**. This allows you to chat directly with an AI to carry out development tasks, using your project's context as a foundation, while keeping track of the model's context window size to prevent errors.

## Core Features

*   **Project Management Dashboard:**
    *   Save and manage a list of your projects.
    *   "Star" important projects for easy access.
    *   CRUD (Create, Read, Update, Delete) functionality for your project list.
    *   **Project Cloning:** Quickly duplicate an existing project, including all its settings, filters, and file selections.
    *   **Import/Export:** Export project configurations to a JSON file to share or back up, and import them back into the application.
*   **Interactive & Context-Aware AI Development:**
    *   **AI-Powered File Selection:** Connect to any OpenAI-compatible LLM service (e.g., `lollms-chat`) and have the AI automatically select the most relevant files for a given task.
    *   **Model Selection:** Fetch and choose from the list of available models hosted by your LLM server.
    *   **Context-Aware Discussion Tab:** After generating the project context, chat with the AI to generate code, write documentation, or suggest refactors.
    *   **Tokenizer Integration:** A progress bar shows you how much of the AI's context window is filled, turning from green to yellow to red as you approach the limit, helping you manage the conversation effectively.
*   **Advanced Tree Generation & Filtering:**
    *   Generates a visual, text-based tree of your project's folder structure.
    *   Includes full file content or, for Python/JavaScript, extracts high-level code signatures.
    *   **Smart Refresh Options:** When reloading a project tree, choose to either preserve your manually selected files or have the app automatically re-select files based on presets.
    *   Extensive filtering capabilities with presets and custom rules.
*   **Customizable AI Prompting Workflow:**
    *   **Prompt Templates:** Create and manage reusable prompt templates.
    *   **Save From Editor:** Save the current text in the prompt editor as a new template with one click.
    *   **Import/Export Prompts:** Share your custom prompt templates by exporting them to a JSON file, and import templates from others.
    *   **Documentation Integration:** Append external documentation files directly into your prompt context.
*   **Modern Web Interface:**
    *   A clean, responsive UI with light and dark themes.
    *   All settings, including chat history, are saved in your browser's local storage for persistence across sessions.
    *   Rendered markdown in the chat includes copy buttons on code blocks for convenience.

## Installation

### Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)

### Running the Application

The application uses `pipmaster` to automatically install its dependencies on the first run.

1.  Save the `server.py` script.
2.  Create a `static` folder in the same directory and place `index.html`, `main.js`, and `style.css` inside it.
3.  Navigate to the directory in your terminal.
4.  Run the server:
    ```bash
    python server.py
    ```
5.  The application will automatically open in your default web browser at `http://127.0.0.1:8765`.

## How to Use

1.  **Configure LLM:** Before you start, click the gear icon in the header to open Global Settings. Enter your lollms-compatible server URL and select an AI model. This is required for the Discussion tab to work.
2.  **Add & Load Project:** From the dashboard, add a project. In the main view, configure filters and click **"Load Project Tree"**.
3.  **Manage Projects:**
    *   **Clone:** Click the clone icon on a project card to create a copy with all its settings.
    *   **Export:** Check the box on one or more project cards and click "Export Selected".
    *   **Import:** Click "Import" and select a previously exported JSON file.
4.  **Generate Context:** In the "Explorer & Prompt" tab, select files, write or load a prompt, and click **"Generate Structure Text"**.
    *   Use the "Save" button next to the template selector to save your current prompt text as a new template.
5.  **Discuss with AI:** Switch to the new **"Discussion"** tab.
    *   Click **"Start Discussion"**. This sends the context to the AI and fetches the model's context size.
    *   A progress bar will appear below the chat, showing you the token usage.
    *   Use the chat input to ask questions. The progress bar will update with each message, ensuring you don't exceed the context limit.

## License

This project is licensed under the MIT License.
