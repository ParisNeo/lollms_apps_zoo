# Templated Code Builder

## User Requirements
- Create a web application for building templated code
- Utilize a template to set the structure of the output
- Allow input of content code or generation steering text
- Use generateCode function to build the output code
- Implement VSCode widget for code input and display
- Enable selection of different coding languages for template and content
- Include a comprehensive list of programming languages in a grouped select element
- Automatically resize output when generation is complete
- Apply Lollms theme with a settings SVG button in the top right corner

## User Interface Elements
1. Header
   - Application title
   - Settings SVG button (top right)

2. Input Section
   - Template Code area (VSCode widget)
   - Content Code area (VSCode widget)
   - Generation Steering Text area (textarea)

3. Language Selection
   - Template Language dropdown (grouped select)
   - Content Language dropdown (grouped select)

4. Control
   - Generate Code button

5. Output Section
   - Generated Code area (VSCode widget, resizable)

## Use Cases
1. User inputs template code
2. User selects template language
3. User inputs either content code or generation steering text
4. User selects content language (if applicable)
5. User clicks Generate Code button
6. System processes inputs using generateCode function
7. System displays generated code in output area
8. Output area automatically resizes to fit content

## Implementation Details
- Single HTML file structure with embedded CSS and JavaScript
- Utilize VSCode widget library for code input and display
- Implement a comprehensive grouped select element for language selection
- Use Lollms theme for styling
- Integrate generateCode function for code generation
- Implement dynamic resizing of output area

## Libraries and Resources
- VSCode widget library
- Lollms theme CSS
- generateCode function (assumed to be provided by the Lollms system)
- SVG for settings button