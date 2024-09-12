# Multi AI Personalities Debate App

## Application Name
AI Debate Arena

## User Requirements
- Create a web application for simulating debates between multiple AI personalities
- Utilize Lollms for text synthesis based on crafted prompts
- Support multiple languages using Lollms localizer
- Allow users to set up and customize debate participants
- Enable users to specify debate subjects
- Generate and display debates with an AI animator
- Format output as HTML
- Provide export functionality to Markdown and HTML

## User Interface Elements
1. Language selection dropdown
2. Participant setup section
   - Name input field
   - Personality description textarea
   - Add participant button
   - List of added participants with edit/delete options
3. Debate subject input field
4. Start debate button
5. Debate display area
6. Export buttons (Markdown and HTML)

## Use Cases
1. Language Selection
   - User selects preferred language from dropdown
   - UI updates to reflect chosen language

2. Participant Setup
   - User enters participant name and description
   - User clicks "Add Participant" button
   - New participant appears in the list
   - User can edit or delete existing participants

3. Debate Initiation
   - User enters debate subject
   - User clicks "Start Debate" button
   - App generates debate content using Lollms

4. Debate Display
   - Generated debate content is displayed in HTML format
   - Animator's comments and participants' arguments are clearly distinguished

5. Export Functionality
   - User clicks "Export to Markdown" or "Export to HTML" button
   - App generates and downloads the exported file

## Technical Considerations
- Single HTML file structure with embedded CSS and JavaScript
- Use of Lollms for text generation and localization
- Dynamic HTML content generation for debate display
- Client-side export functionality for Markdown and HTML

## Prompt Crafting
- Create a prompt template for debate generation
- Include participant information, debate subject, and animator instructions
- Ensure proper formatting for HTML output

## Libraries and Code Examples
- Lollms library for text generation and localization
- Example code for integrating Lollms:
  ```javascript
  // Lollms integration placeholder
  function generateDebate(participants, subject) {
    // Call Lollms API to generate debate content
  }
  
  function translateUI(language) {
    // Use Lollms localizer to update UI text
  }
  ```