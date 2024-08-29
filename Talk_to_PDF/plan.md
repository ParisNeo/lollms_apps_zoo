Talk to PDF

Requirements:
- Upload and interact with PDF documents
- AI impersonation of PDF content
- Question-answering about specific elements
- Full PDF summarization
- Dynamic RAG or summary generation based on prompt
- Markdown rendering for discussions
- Localization support (English and French)
- Adjustable AI personality and tone
- Configurable Lollms parameters
- Persistent settings
- TailwindCSS styling
- Educational user experience

User Interface Elements:
1. Header with app title and language selector
2. PDF upload area (drag-and-drop or file selection)
3. Chat interface with message history
4. User input field for questions/prompts
5. Settings button (SVG icon)
6. Settings modal:
   - AI personality dropdown (humorous, serious, etc.)
   - Lollms parameters (host URL, context size, generation size)
   - UI language selector
   - Apply and Cancel buttons
7. PDF preview/summary area
8. Loading indicators for AI responses and PDF processing

Use Cases:
1. Upload PDF:
   - User selects or drags a PDF file
   - System processes and analyzes the PDF
   - AI generates an initial greeting based on PDF content

2. Ask Questions:
   - User types a question about the PDF
   - System determines whether to use RAG or summary
   - AI generates and displays a response
   - Conversation history updates

3. Request Summary:
   - User asks for a full PDF summary
   - AI generates and displays a comprehensive summary

4. Adjust Settings:
   - User clicks the settings button
   - Settings modal opens
   - User modifies AI personality, Lollms parameters, or UI language
   - Changes are saved and applied

5. Switch Language:
   - User selects a different language
   - UI text updates to the chosen language

6. Learn from PDF:
   - User engages in a conversation about the PDF content
   - AI provides explanations, examples, and additional context
   - User gains knowledge through interactive dialogue