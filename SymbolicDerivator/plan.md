# Symbolic Derivative Function Generator

## User Requirements

Create a web application that:
1. Generates Python functions for partial derivatives of a given function
2. Utilizes SymPy for symbolic differentiation on the backend
3. Returns text of Python functions that compute the derivatives
4. Allows users to save the generated code

## User Interface Elements

1. Input area for the original function
2. Input area for parameters to differentiate against
3. "Generate Derivatives" button
4. Output area for displaying generated Python functions
5. "Save Code" button
6. Status/message display area

## Use Cases

1. User enters a mathematical function
2. User specifies parameters for partial derivatives
3. User clicks "Generate Derivatives" button
4. System processes the input using SymPy
5. System displays generated Python functions
6. User reviews the generated code
7. User clicks "Save Code" button to download the functions

## Technical Considerations

1. Single HTML file structure
2. CSS for styling the user interface
3. JavaScript for handling user interactions and AJAX requests
4. Backend API endpoint for processing SymPy calculations
5. Error handling for invalid inputs or processing errors

## Implementation Plan

1. HTML structure
   - Header with application title
   - Input form for function and parameters
   - Button for generating derivatives
   - Output area for displaying results
   - Button for saving generated code

2. CSS styling
   - Responsive layout
   - Input and output area styling
   - Button styling

3. JavaScript functionality
   - Form submission handling
   - AJAX request to backend API
   - Displaying results in the output area
   - Implementing "Save Code" functionality

4. Backend API (separate from this file)
   - Endpoint for processing SymPy calculations
   - Function to generate Python code from SymPy results

5. Error handling and user feedback
   - Input validation
   - Error messages for invalid inputs or processing errors
   - Success messages for code generation and saving