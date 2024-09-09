HTML Content Builder with Lollms Integration

User Requirements:
Create a WYSIWYG (What You See Is What You Get) tool for building HTML content
Integrate with Lollms for generating text content
Implement a sleek and intuitive interface for adding, nesting, selecting, and removing elements
Utilize advanced Tailwind CSS design for a modern and responsive layout

User Interface Elements:
1. Main editing area (canvas)
2. Toolbar with element options (e.g., headings, paragraphs, images, buttons)
3. Element properties panel
4. Lollms text generation panel
5. Preview mode toggle
6. Save/Export button

Use Cases:
1. Add new elements:
   - Click on desired element in toolbar
   - Drag and drop to position on canvas
2. Nest elements:
   - Drag child element onto parent element
   - Visual feedback for nesting levels
3. Select elements:
   - Click on element to select
   - Multi-select with Shift+Click
4. Remove elements:
   - Select element(s) and press Delete key
   - Remove button in element properties panel
5. Edit element properties:
   - Adjust styling, classes, and attributes in properties panel
6. Generate content with Lollms:
   - Select text element
   - Open Lollms panel
   - Enter prompt and generate text
   - Insert generated text into selected element
7. Preview and export:
   - Toggle preview mode to see final result
   - Export HTML code or save project

Technical Considerations:
- Use HTML5 for structure
- Implement CSS using Tailwind CSS framework
- Utilize JavaScript for dynamic functionality
- Incorporate drag-and-drop API for element manipulation
- Implement contenteditable attribute for inline text editing
- Use localStorage for saving project progress
- Integrate Lollms API for text generation