# AI-Enhanced Presentation Creator

## User Requirements
Create a web application that allows users to generate AI-enhanced PowerPoint presentations using natural language prompts. The application should integrate with LoLLMs for content generation and AI image creation capabilities, utilizing the provided backend API.

## User Interface Elements

### Header
- Application title: "AI-Enhanced Presentation Creator"
- Brief description of the app's functionality

### Main Content Area
1. Input Section
   - Textbox for user prompt
   - "Generate Presentation" button

2. Presentation Preview Section
   - Display generated slides in a carousel format
   - Show slide title, content, and images

3. Image Upload/Generation Section
   - For each slide with an image:
     - Display image description
     - Option to upload an image or generate AI image
     - Preview of uploaded/generated image

4. Final Actions Section
   - "Download Presentation" button
   - "Start Over" button

### Footer
- Credits and version information

## Use Cases

1. Generate Presentation
   - User enters a prompt describing the desired presentation
   - Application sends request to backend API
   - LoLLMs generates JSON structure for the presentation
   - Frontend displays preview of generated slides

2. Upload Custom Image
   - User selects a slide with "user_provided" image type
   - User uploads an image file
   - Frontend sends image to backend API
   - Updated slide displayed in preview

3. Generate AI Image
   - User selects a slide with "generate" image type
   - Frontend sends image generation request to backend API
   - Generated image displayed in preview

4. Download Presentation
   - User reviews and confirms the final presentation
   - Frontend requests the completed presentation from backend API
   - User downloads the PowerPoint file

## Implementation Details

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Enhanced Presentation Creator</title>
    <style>
        /* Add your CSS styles here */
    </style>
</head>
<body>
    <header>
        <h1>AI-Enhanced Presentation Creator</h1>
        <p>Create stunning presentations with AI-generated content and images</p>
    </header>

    <main>
        <section id="input-section">
            <textarea id="user-prompt" placeholder="Describe your presentation..."></textarea>
            <button id="generate-btn">Generate Presentation</button>
        </section>

        <section id="preview-section">
            <!-- Slides will be dynamically added here -->
        </section>

        <section id="image-section">
            <!-- Image upload/generation options will be dynamically added here -->
        </section>

        <section id="final-actions">
            <button id="download-btn" disabled>Download Presentation</button>
            <button id="start-over-btn">Start Over</button>
        </section>
    </main>

    <footer>
        <p>Powered by LoLLMs - Version 1.0</p>
    </footer>

    <script>
        // Add your JavaScript code here
        // Include functions for:
        // - Sending requests to the backend API
        // - Handling LoLLMs interactions for JSON generation
        // - Managing image uploads and AI image generation
        // - Updating the UI with generated content and images
        // - Implementing the presentation download functionality
    </script>
</body>
</html>
```