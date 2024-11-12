# Contextual Summary Builder

## App Overview

The Contextual Summary Builder is a web application that generates tailored summaries of various document types based on user-provided context.

## User Requirements

1. Upload and process PDF, DOCX, TXT, and other document formats
2. Input contextual information for summary customization
3. Utilize task library for document summarization
4. Display output as rendered markdown
5. Support localization for multiple languages
6. Enable copying and exporting of generated summaries

## User Interface Elements

1. File upload area
2. Text input field for contextual information
3. Language selection dropdown
4. Generate summary button
5. Rendered markdown display area
6. Copy to clipboard button
7. Export summary button

## Use Cases

1. Document Upload
   - User selects a document file
   - App validates file type and size
   - File is loaded into the application

2. Context Input
   - User enters contextual information
   - App stores the input for summarization

3. Language Selection
   - User chooses preferred language
   - UI updates to reflect selected language

4. Summary Generation
   - User clicks "Generate Summary" button
   - App processes document using task library
   - Contextual summary is created based on input

5. Display Summary
   - App renders the generated summary as markdown
   - User views the formatted summary

6. Copy Summary
   - User clicks "Copy to Clipboard" button
   - Summary content is copied to clipboard

7. Export Summary
   - User clicks "Export" button
   - App generates downloadable file with summary

## Technical Considerations

1. Single HTML file structure
   - Inline CSS for styling
   - Embedded JavaScript for functionality

2. Libraries and APIs
   - PDF.js for PDF processing
   - Mammoth.js for DOCX handling
   - Marked.js for markdown rendering
   - i18next for localization

3. File Processing
   - Use FileReader API for local file handling
   - Implement file type detection and validation

4. Asynchronous Operations
   - Handle file reading and processing asynchronously
   - Implement loading indicators for user feedback

5. Error Handling
   - Provide user-friendly error messages
   - Gracefully handle unsupported file types

6. Responsive Design
   - Ensure UI adapts to different screen sizes
   - Optimize for both desktop and mobile devices

7. Accessibility
   - Implement ARIA attributes for screen readers
   - Ensure keyboard navigation support

## Localization Strategy

1. Define language JSON files for supported languages
2. Implement language switching functionality
3. Use i18next library for managing translations
4. Apply translations to all UI elements and messages

## Data Flow

1. User Input → File Processing → Context Analysis
2. Document Content + Context → Task Library → Summary Generation
3. Generated Summary → Markdown Rendering → Display
4. User Interaction → Copy/Export Functionality