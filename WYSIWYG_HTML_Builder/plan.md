# WYSIWYG HTML Content Builder for Lollms

## User Requirements
- Create a powerful and intuitive WYSIWYG HTML content builder
- Integrate with Lollms for dynamic text generation
- Modern interface using advanced Tailwind CSS
- Support for various HTML elements (headers, text, images, divs)
- Dynamic element manipulation (moving, nesting)
- Text generation for individual elements using Lollms
- Image handling with base64 encoding
- Export and import functionality
- Template loading option
- Customizable styling interface
- Toolbox for adding new elements
- SVG icons for buttons
- Lollms settings management

## User Interface Elements
1. Main editing area
   - Drag-and-drop functionality
   - Visual representation of HTML structure
2. Left sidebar: Element toolbox
   - Buttons for adding various HTML elements
3. Top toolbar
   - Export button
   - Load button
   - Template selection dropdown
   - Settings button
4. Right sidebar: Styling interface
   - Element-specific styling options
   - Global styling options
5. Lollms settings modal
   - Configurable Lollms parameters
   - Save and update buttons

## Element Types
1. Headings (H1-H6)
2. Paragraphs
3. Images
4. Divs (containers)
5. Lists (ordered and unordered)
6. Tables
7. Links
8. Buttons

## Element Controls
- Generate button (SVG icon)
  - Opens Lollms text generation popup
- Remove button (SVG icon)
- Drag handle for moving elements
- Resize handles for adjustable elements

## Use Cases
1. Create new content
   - Add elements from toolbox
   - Arrange elements on the page
   - Generate text using Lollms
   - Style elements individually and globally
2. Edit existing content
   - Load HTML file
   - Modify element structure and content
   - Update styling
3. Use templates
   - Load pre-designed templates
   - Customize template content
4. Export content
   - Save generated HTML to a file
5. Manage Lollms settings
   - Access settings modal
   - Update and save configurations

## Technical Considerations
- Single HTML file structure
  - Inline CSS using Tailwind
  - JavaScript for functionality
- LocalStorage for saving Lollms settings
- File API for importing and exporting HTML
- SVG icons embedded in HTML
- Base64 encoding for image storage
- Lollms API integration for text generation