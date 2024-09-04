MATLAB Function Generator

User Requirements:
Create a web-based tool that generates MATLAB functions based on user input requirements. The application should provide a user-friendly interface for inputting function specifications and display the generated MATLAB code. Additionally, include functionality to copy the generated code and save it to disk.

User Interface Elements:
1. Header with application title and brief description
2. Input area for user requirements (textarea)
3. Generate button to trigger function creation
4. Output area to display generated MATLAB function
5. Copy button with clipboard icon (SVG)
6. Save button with download icon (SVG)
7. Footer with credits and version information

Use Cases:
1. User enters function requirements
2. User clicks Generate button
3. AI processes input and generates MATLAB function
4. Generated function is displayed in output area
5. User clicks Copy button to copy code to clipboard
6. User clicks Save button to download function as .m file

HTML Structure:
1. <!DOCTYPE html>
2. <html lang="en">
3. <head>
   - Meta tags
   - Title
   - Tailwind CSS CDN link
4. <body>
   - Header
   - Main content container
     - Input section
     - Output section
   - Footer
5. <script>
   - JavaScript code for functionality

CSS (Tailwind classes):
- Responsive layout
- Custom colors and styling
- Flexbox for layout structure

JavaScript Functions:
1. generateFunction(): Process user input and generate MATLAB function
2. copyToClipboard(): Copy generated code to clipboard
3. saveToFile(): Save generated function as .m file
4. updateUI(): Handle UI updates and interactions

SVG Icons:
1. Clipboard icon for Copy button
2. Download icon for Save button

Error Handling:
- Display error messages for invalid input
- Handle API errors gracefully

Accessibility:
- Proper ARIA labels for interactive elements
- Keyboard navigation support