# Multi Codes Analysis Tool Documentation

## Overview

The **Multi Codes Analysis Tool** is a web-based application designed to help users analyze multiple code files based on a given prompt. It allows users to add code files, input a prompt, and receive a detailed analysis of the code files. The tool supports multiple languages and provides options to save and load projects.

## Features

- **Add Code Files**: Add multiple code files for analysis.
- **Prompt Input**: Enter a prompt to guide the analysis.
- **Analyze**: Generate a detailed analysis of the code files based on the prompt.
- **Save/Load Projects**: Save your current project or load a previously saved project.
- **Copy/Save Output**: Copy the analysis output to the clipboard or save it as a markdown file.
- **Multi-language Support**: Switch between English, French, and Spanish.

## Getting Started

### 1. Add Code Files

- Click the **Add Code** button to add a new code editor.
- You can either type your code directly into the editor or upload a file by clicking the **Open File** button.
- To remove a code editor, click the **Remove File** button.

### 2. Enter a Prompt

- In the **Prompt Input** area, enter a prompt that will guide the analysis of the code files.
- Example: "Analyze the performance and security of the following code."

### 3. Analyze the Code

- Once you have added your code files and entered a prompt, click the **Analyze** button.
- The tool will generate a detailed analysis of the code files based on the prompt and display the results in the **Output Area**.

### 4. Copy or Save the Output

- After the analysis is complete, you can:
  - **Copy the Output**: Click the **Copy Output** button to copy the analysis to your clipboard.
  - **Save the Output**: Click the **Save Output** button to download the analysis as a markdown file.

### 5. Save or Load a Project

- **Save Project**: Click the **Save Project** button to save your current project, including the code files, prompt, and output.
- **Load Project**: Click the **Load Project** button to load a previously saved project.

## Multi-language Support

The tool supports English, French, and Spanish. You can switch between languages using the language selector at the top of the page. The interface and messages will be translated accordingly.

### Available Languages

- **English**
- **Français**
- **Español**

## User Interface

### Buttons

- **Add Code**: Adds a new code editor.
- **Save Project**: Saves the current project (code files, prompt, and output).
- **Load Project**: Loads a previously saved project.
- **Analyze**: Generates an analysis based on the code files and prompt.
- **Copy Output**: Copies the analysis output to the clipboard.
- **Save Output**: Saves the analysis output as a markdown file.

### Input Fields

- **Prompt Input**: Enter the prompt that will guide the analysis.
- **Code Editors**: Add and edit code files for analysis.

### Output Area

- Displays the analysis results after clicking the **Analyze** button.

## Saving and Loading Projects

### Save Project

- Click the **Save Project** button to download a JSON file containing the current project (code files, prompt, and output).

### Load Project

- Click the **Load Project** button to upload a previously saved JSON file and restore the project.

## Local Storage

The tool automatically saves the current state (prompt, code files, and output) in the browser's local storage. This allows you to continue where you left off if you close or refresh the page.

## Loading and Saving State

- **Load Saved State**: When the page loads, the tool will automatically load the saved state from local storage (if available).
- **Save State**: The tool automatically saves the current state to local storage when you leave the page.

## Error Handling

If an error occurs during the analysis, an error message will be displayed in the **Output Area**.

## Loading Indicator

While the analysis is being generated, a loading overlay with a spinning strawberry icon will be displayed to indicate that the system is busy.

## License

This tool is provided as-is without any warranties.