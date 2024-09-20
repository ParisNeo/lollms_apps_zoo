# Multi Codes Analysis Tool

## User Requirements

- Create a web application for analyzing multiple code files
- Allow users to add multiple code editors to the page
- Provide options to input code manually or load from a file
- Enable users to enter prompts and receive analyzed output
- Display output in a markdown-rendered format
- Allow users to copy and save the analysis results

## User Interface Elements

### Header
- Application title: "Multi Codes Analysis Tool"

### Code Input Section
- "Add Code" button
- Dynamic container for multiple code editors
  - VSCode editor component
  - File name input field
  - "Open File" button

### Analysis Section
- Prompt input textarea
- "Analyze" button
- Markdown-rendered output area
- "Copy Output" button
- "Save Output" button

## Use Cases

1. Adding a new code editor
   - User clicks "Add Code" button
   - New VSCode editor, file name input, and "Open File" button appear

2. Inputting code manually
   - User types code directly into the VSCode editor
   - User enters a file name in the input field

3. Loading code from a file
   - User clicks "Open File" button
   - File explorer opens for file selection
   - Selected file's content and name populate the editor and input field

4. Analyzing code
   - User enters a prompt in the textarea
   - User clicks "Analyze" button
   - Analysis result appears in the markdown-rendered output area

5. Copying output
   - User clicks "Copy Output" button
   - Analysis result is copied to clipboard

6. Saving output
   - User clicks "Save Output" button
   - Analysis result is saved as a markdown file

## Technical Considerations

- Use HTML5 for structure
- Implement CSS for styling within a `<style>` tag
- Utilize JavaScript for functionality within a `<script>` tag
- Incorporate the Monaco editor for VSCode-like functionality
- Use a markdown rendering library (e.g., marked.js) for output display
- Implement File API for file reading functionality
- Use localStorage for temporary data storage if needed

## Libraries and Resources

- Monaco Editor: https://microsoft.github.io/monaco-editor/
- Marked.js for Markdown rendering: https://marked.js.org/
- File API: https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications