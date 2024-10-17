# Code Conversation AI Assistant

## Web App Overview

This single-file web application enables users to discuss code with an AI assistant, featuring a VS Code-like code editor and an interactive chat interface. The AI can modify the code based on user requests, with an undo mechanism for previous changes.

## User Interface Elements

1. Header
   - Application title
   - Configuration button

2. Main content area
   - VS Code-like code editor widget
   - Chat interface
     - Message history display
     - Input field for user messages
     - Send button

3. Control panel
   - Undo button
   - Redo button
   - Steps counter (current step / total steps)

4. Configuration modal
   - Number of undo steps input (default: 10)
   - Save button
   - Cancel button

## Use Cases

1. User inputs initial code
2. User sends message to AI about code modifications
3. AI responds with text explanation and modified code
4. Code editor updates if a single valid code block is detected
5. User requests undo of previous change
6. User adjusts the number of undo steps in configuration

## Technical Considerations

1. Use VS Code API for code editor functionality
2. Implement undo/redo stack for code changes
3. Utilize Lollms markdown for styling chat messages
4. Employ task library's extract_codes function for code extraction
5. Configure AI to respond with full code blocks without simplification comments
6. Implement error handling for invalid code updates

## Data Management

1. Store code history in an array (limited by configuration)
2. Maintain chat history in local storage
3. Save configuration settings in local storage

## AI Integration

1. Set up AI instruction prompt for code modification requests
2. Configure AI to respond with full code blocks
3. Implement code extraction and validation before updating editor

## Styling

1. Use CSS Grid for layout structure
2. Implement responsive design for various screen sizes
3. Apply Lollms theme colors and styles

## Performance Optimization

1. Implement lazy loading for VS Code API
2. Optimize chat history rendering for large conversations
3. Use debounce for user input to reduce API calls