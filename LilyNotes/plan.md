# LilyPond Web Editor

## Application Description
A web-based editor for creating and editing LilyPond music notation files with live preview capabilities, designed as a single HTML file application.

## Key Requirements
- Single file web application (HTML, CSS, JavaScript)
- LilyPond code editor
- Live preview of the musical score
- File import/export functionality
- Basic editing tools and shortcuts

## External Dependencies
- Ace Editor (for code editing)
- LilyPond.js (for rendering)
- FileSaver.js (for file handling)
- Bootstrap Icons (for UI elements)

## User Interface Components
### Layout
1. Top Navigation Bar
   - File operations buttons
   - View toggle buttons
   - Help button

2. Main Content Area
   - Split view layout
     - Left: Code editor panel
     - Right: Preview panel

3. Status Bar
   - Compilation status
   - Error messages
   - Cursor position

### UI Elements
- Editor Theme Selector
- Font Size Controls
- Download/Save Button
- Import Button
- Full Screen Toggle
- Split View Resizer

## Use Cases
1. Basic Operations
   - Create new LilyPond document
   - Load existing file
   - Save file
   - Export as PDF/MIDI

2. Editing Features
   - Syntax highlighting
   - Auto-completion
   - Line numbering
   - Error highlighting

3. Preview Functions
   - Real-time rendering
   - Preview zoom controls
   - Toggle preview pane

4. File Management
   - New file creation
   - File import (.ly files)
   - Export as .ly file
   - Export as PDF

## Local Storage Implementation
- Auto-save functionality
- User preferences storage
- Recent files history

## Error Handling
- Syntax error detection
- Compilation error display
- Invalid file handling
- Connection status monitoring

## Keyboard Shortcuts
- Ctrl+S: Save
- Ctrl+N: New File
- Ctrl+O: Open File
- Ctrl+Shift+P: Toggle Preview
- Ctrl+B: Compile Score

## Styling Considerations
- Dark/Light theme support
- Responsive design
- Mobile-friendly layout
- Clear typography
- High contrast UI elements