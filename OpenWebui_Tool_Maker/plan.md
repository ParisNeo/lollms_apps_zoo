# OpenWebui Tool Generator App

## App Overview
A web application for generating OpenWebUI tool code based on user prompts, utilizing the lollms generateCode method.

## Requirements
- Generate Python code for OpenWebUI tools based on text prompts
- Display the generated code in a formatted manner
- Allow copying of generated code
- Validate and format the input prompt
- Use the provided example as a reference template

## UI Elements
### Input Section
- Text area for entering the tool description prompt
- Generate button
- Clear button

### Output Section
- Code display area with syntax highlighting
- Copy to clipboard button
- Success/Error message display
- Code preview panel

### Styling
- Modern, clean interface
- Dark theme for code display
- Responsive layout
- Loading indicator during generation

## Technical Implementation
### Libraries
- Prism.js for code syntax highlighting
- Clipboard.js for copy functionality
- Lollms API integration for code generation

### Code Structure
```html
<head>
    <!-- Meta tags -->
    <!-- CSS styles -->
    <!-- Library imports -->
</head>
<body>
    <!-- UI elements -->
    <!-- JavaScript code -->
</body>
```

## Use Cases
1. Basic Tool Generation
   - User enters tool description
   - System generates corresponding Python code
   - Code is displayed with syntax highlighting

2. Code Management
   - User copies generated code
   - User clears input/output
   - User modifies prompt and regenerates

3. Error Handling
   - Invalid prompt detection
   - API error handling
   - Generation timeout handling

## API Integration
### Generate Code Endpoint
```javascript
const generateCode = async (prompt) => {
    return await window.api.generateCode({
        prompt: prompt,
        template: codeTemplate
    });
}
```

## Data Flow
1. User Input → Validation
2. Validation → API Call
3. API Response → Code Formatting
4. Formatted Code → Display
5. User Actions → State Management