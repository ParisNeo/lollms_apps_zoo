```markdown
# Application Name: Document Contextual Summarizer and Synthesizer

## User Requirements
Create a single-file web application that allows users to upload multiple files (PDF, DOCX, TXT) and input a prompt. The application will:
1. Use the Lollms task library's contextual summary tools to extract relevant information from each document based on the provided prompt.
2. Perform a final synthesis of the extracted information from all documents using a second user-provided prompt.
3. Display the results in a user-friendly interface.

The application will be implemented as a single HTML file with embedded CSS and JavaScript.

---

## Plan

### Libraries and Tools
- **Lollms Task Library**: For contextual summary and synthesis functionalities.
- **File Reader API**: To handle file uploads and read file contents in JavaScript.
- **PDF.js**: For parsing PDF files in the browser.
- **JSZip**: For handling multiple file uploads if needed.
- **Bootstrap (optional)**: For responsive and styled UI components.
- **Vanilla JavaScript**: For core functionality and interactivity.

---

### User Interface (UI) Elements
1. **Header Section**
   - Title: "Document Contextual Summarizer and Synthesizer"
   - Brief description of the app's functionality.

2. **File Upload Section**
   - Drag-and-drop area for file uploads.
   - File input button for manual selection.
   - Display list of uploaded files with file names and types.

3. **Prompt Input Section**
   - Textarea for the first prompt (contextual summary).
   - Textarea for the second prompt (final synthesis).

4. **Action Buttons**
   - "Process Documents" button to start the summarization process.
   - "Clear All" button to reset the application.

5. **Results Display Section**
   - Accordion or collapsible sections to display individual document summaries.
   - Final synthesis result displayed prominently.

6. **Footer Section**
   - Credits and links to Lollms documentation.

---

### Use Cases
1. **Uploading Files**
   - Users can upload multiple files in PDF, DOCX, or TXT format.
   - The app will validate file types and display the list of uploaded files.

2. **Inputting Prompts**
   - Users provide a prompt for extracting relevant information from each document.
   - Users provide a second prompt for synthesizing the extracted information.

3. **Processing Documents**
   - The app reads the content of each uploaded file.
   - For each file:
     - Extract relevant information using the Lollms contextual summary tool and the first prompt.
   - Perform a final synthesis of all extracted summaries using the second prompt.

4. **Displaying Results**
   - Show individual document summaries in collapsible sections.
   - Display the final synthesis result prominently.

5. **Clearing Data**
   - Users can reset the application to remove uploaded files, prompts, and results.

---

### Implementation Details
1. **HTML Structure**
   - Use semantic HTML5 elements for structure (e.g., `<header>`, `<main>`, `<footer>`).
   - Include `<input>` elements for file uploads and prompts.
   - Use `<div>` or `<section>` for displaying results.

2. **CSS Styling**
   - Style the drag-and-drop area for file uploads.
   - Use responsive design principles for mobile and desktop compatibility.
   - Highlight results with distinct colors or typography.

3. **JavaScript Functionality**
   - Handle file uploads and read file contents using the File Reader API.
   - Parse PDF files using PDF.js.
   - Extract text from DOCX files using a lightweight library or custom parser.
   - Process TXT files as plain text.
   - Integrate Lollms task library for contextual summary and synthesis.
   - Update the UI dynamically to display results.

4. **Error Handling**
   - Validate file types and sizes during upload.
   - Display error messages for unsupported formats or processing failures.

5. **Performance Optimization**
   - Process files asynchronously to avoid blocking the UI.
   - Use efficient algorithms for text extraction and summarization.

---

### Example Code Snippets
1. **File Upload Handling**
   ```javascript
   document.getElementById('fileInput').addEventListener('change', function(event) {
       const files = event.target.files;
       for (let file of files) {
           console.log(`Uploaded file: ${file.name}`);
           // Process file content here
       }
   });
   ```

2. **Integrating Lollms Task Library**
   ```javascript
   async function summarizeDocument(content, prompt) {
       const summary = await lollms.contextualSummary(content, prompt);
       return summary;
   }

   async function synthesizeSummaries(summaries, prompt) {
       const synthesis = await lollms.synthesize(summaries, prompt);
       return synthesis;
   }
   ```

3. **Displaying Results**
   ```javascript
   function displayResults(summaries, synthesis) {
       const resultsContainer = document.getElementById('results');
       summaries.forEach((summary, index) => {
           const summaryElement = document.createElement('div');
           summaryElement.innerHTML = `<h3>Document ${index + 1}</h3><p>${summary}</p>`;
           resultsContainer.appendChild(summaryElement);
       });
       const synthesisElement = document.createElement('div');
       synthesisElement.innerHTML = `<h2>Final Synthesis</h2><p>${synthesis}</p>`;
       resultsContainer.appendChild(synthesisElement);
   }
   ```

---

### Final Notes
This single-file web application will provide a seamless and efficient way for users to extract and synthesize information from multiple documents using the Lollms task library. The UI will be intuitive, and the functionality will be robust and responsive.
```