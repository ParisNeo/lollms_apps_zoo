# Test-Time Training Dataset Generator

## User Requirements

Create a web application that utilizes Lollms to generate a dataset for test-time training. The application should:
1. Leverage Lollms' code generation capabilities to create examples
2. Generate a database of task prompts and task achievements
3. Structure the data as a list of dictionaries with "task_prompt" and "task_process" pairs
4. Allow exporting the dataset as JSON

## User Interface Elements

1. Header
   - Application title
   - Brief description

2. Input Section
   - Text area for entering the initial task description
   - Button to generate examples

3. Generated Examples Display
   - Table or list view of generated examples
   - Columns: Task Prompt, Task Process

4. Controls
   - Button to generate more examples
   - Button to clear all examples
   - Button to export dataset as JSON

5. Footer
   - Credits and version information

## Use Cases

1. Generate Initial Dataset
   - User enters a task description
   - System generates multiple examples using Lollms
   - Display generated examples in the UI

2. Add More Examples
   - User clicks "Generate More" button
   - System generates additional examples
   - New examples are added to the existing list

3. Clear Dataset
   - User clicks "Clear All" button
   - All generated examples are removed from the display

4. Export Dataset
   - User clicks "Export JSON" button
   - System compiles all examples into a JSON format
   - JSON file is downloaded to the user's device

## Technical Considerations

1. Single HTML File Structure
   - HTML for structure
   - CSS for styling (internal `<style>` tag)
   - JavaScript for functionality (internal `<script>` tag)

2. Lollms Integration
   - Use Lollms API for code generation
   - Implement error handling for API calls

3. Data Management
   - Store generated examples in a JavaScript array
   - Implement functions for adding, clearing, and exporting data

4. JSON Export
   - Use `JSON.stringify()` to convert data to JSON format
   - Implement file download functionality using Blob and URL.createObjectURL()

5. Responsive Design
   - Use CSS flexbox or grid for layout
   - Implement media queries for mobile responsiveness