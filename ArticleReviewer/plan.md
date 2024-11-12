# Article Review Generator

## Application Overview
Article Review Generator is a single-file web application that allows users to upload various document formats (PDF, TXT, MD, LaTeX, DOCX) and generate a comprehensive review using the Lollms task library for summarization and review generation.

## User Requirements
- Upload documents in PDF, TXT, MD, LaTeX, or DOCX formats
- Generate an article review with a single button click
- Display the generated review using Lollms markdown renderer

## User Interface Elements
1. File upload area
2. Document type selector (PDF, TXT, MD, LaTeX, DOCX)
3. "Generate Review" button
4. Review display area with Lollms markdown renderer

## Use Cases
1. User uploads a document
2. User selects the document type
3. User clicks "Generate Review" button
4. Application processes the document and generates a review
5. Review is displayed in the designated area using Lollms markdown renderer

## Technical Implementation
- HTML structure for the single-file web app
- CSS for styling the user interface
- JavaScript for handling user interactions and API calls
- Integration with Lollms task library for document summarization and review generation
- Implementation of Lollms markdown renderer for review display

## API Integration
- Utilize Lollms task library API for document processing and review generation
- Implement file upload and processing functionality
- Handle API responses and error cases

## Review Generation Process
1. Extract text content from the uploaded document
2. Use Lollms task library to summarize the article
3. Generate a review prompt based on the summary
4. Use the review prompt to generate a comprehensive review
5. Render the generated review using Lollms markdown renderer

## Error Handling
- Validate file types and sizes
- Handle API errors and timeouts
- Display user-friendly error messages

## Performance Considerations
- Implement loading indicators for file upload and review generation processes
- Optimize file processing for large documents

## Security Measures
- Implement file type validation
- Sanitize user inputs
- Secure API communications