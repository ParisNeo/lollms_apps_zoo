# Voice Uploader Web App

## Requirements
- Allow users to record their voice directly in the browser
- Enable users to upload existing WAV files
- Implement file upload functionality using the /upload_voice endpoint
- Ensure only WAV files are accepted for upload

## User Interface Elements
1. Voice Recording Section
   - Record button
   - Stop button
   - Playback button
   - Visualizer for audio input

2. File Upload Section
   - File input field
   - Upload button

3. Status Display
   - Recording status
   - Upload progress
   - Success/Error messages

## Use Cases
1. Record Voice
   - User clicks record button
   - App captures audio from microphone
   - User stops recording
   - Recorded audio is previewed

2. Upload WAV File
   - User selects WAV file from device
   - File is validated for correct format
   - User initiates upload

3. Submit Recorded/Uploaded Audio
   - User confirms submission
   - Audio data is sent to /upload_voice endpoint
   - Server processes the upload
   - User receives confirmation or error message

## Technical Considerations
- Use HTML5 audio APIs for voice recording
- Implement client-side file type validation
- Utilize Fetch API for file upload
- Handle server responses and display appropriate messages

## Libraries and APIs
- Web Audio API for recording and audio visualization
- FileReader API for handling file uploads

## Code Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Uploader</title>
    <style>
        /* CSS styles here */
    </style>
</head>
<body>
    <h1>Voice Uploader</h1>
    
    <div id="recordingSection">
        <!-- Voice recording UI elements -->
    </div>
    
    <div id="fileUploadSection">
        <!-- File upload UI elements -->
    </div>
    
    <div id="statusDisplay">
        <!-- Status messages -->
    </div>

    <script>
        // JavaScript code here
        // - Audio recording logic
        // - File upload handling
        // - API interactions
    </script>
</body>
</html>
```