# Personal Teacher Enhanced

Personal Teacher is an interactive learning application that leverages AI to provide personalized educational experiences. Users can express their desire to learn any subject and specify a difficulty level (Beginner, Intermediate, Advanced, Expert). The app generates a comprehensive course with clear sections in markdown format, including objectives, key concepts, detailed content, exercises, and summaries.

It then attempts to create a relevant interactive demo (using HTML/CSS/JS or p5.js) and a multiple-choice quiz with explanations, presenting them in a user-friendly tabbed interface alongside the main lesson content.

The application saves generated courses (lesson, demo code, quiz data) locally using IndexedDB, allowing users to build a personal library of learning materials. Users can search, load, delete, import, and export their saved courses. This enhanced version features an improved UI/UX with dark mode, refined AI prompts for better content generation, and enhanced error handling.

## Version
3.0

## Author
ParisNeo

## Category
Education

## Disclaimer
AI-generated content may require verification for accuracy. Always cross-reference critical information, especially for technical or sensitive subjects. The generated demos and quizzes are intended as supplementary learning tools.

## How to Use
1.  Ensure you have a running Lollms instance (accessible via `lollms-webui`).
2.  Install this personality in Lollms.
3.  Navigate to the "Personal Teacher" personality in the Lollms interface.
4.  Enter the topic you wish to learn in the input field.
5.  Select the desired difficulty level.
6.  Click "Generate Course".
7.  Wait for the AI to generate the lesson, interactive demo, and quiz. The status will be updated below the button.
8.  Once generated, the content will appear in a tabbed interface (Lesson, Interactive Demo, Quiz).
9.  Use the buttons in the header to access saved courses, settings (like language), and toggle dark mode.
10. Saved courses can be accessed, searched, loaded, deleted, imported, and exported via the "Saved Courses" panel.
11. Use the "Export View" button within the course display area to download the currently viewed lesson/demo/quiz as a single HTML file.

## Development Notes
*   This application relies heavily on the Lollms backend for content generation via the `lollms-client.js`.
*   Client-side storage is managed using `Dexie.js` (IndexedDB wrapper).
*   Markdown is rendered using `marked.js` and `lollms_markdown_renderer.js`, supporting syntax highlighting (`highlight.js`), MathJax, and Mermaid diagrams.
*   The UI uses Tailwind CSS for styling.
*   Internationalization is handled by `web.app.localizer.js`.
*   Interactive demos are rendered within sandboxed `iframe` elements using `srcdoc`.
*   Prompts have been refined to guide the AI towards generating structured, accurate, and engaging content appropriate for the selected difficulty level.
*   Error handling has been improved for generation and parsing steps.