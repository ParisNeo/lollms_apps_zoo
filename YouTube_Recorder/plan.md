# YouTube Recorder Web App

## Requirements

- Record audio from the microphone
- Capture video from the screen
- View recorded video and audio separately
- Save video and audio files independently
- Single HTML file implementation with embedded CSS and JavaScript

## User Interface Elements

1. Header
   - App title: "YouTube Recorder"
   - App description

2. Recording Controls
   - Start Recording button
   - Stop Recording button
   - Recording status indicator

3. Preview Section
   - Video preview area
   - Audio waveform visualization

4. Download Section
   - Video download button
   - Audio download button

5. Footer
   - Credits and version information

## Use Cases

1. Start Recording
   - User clicks "Start Recording" button
   - App requests necessary permissions
   - Screen capture and audio recording begin simultaneously
   - Recording status updates to "Recording in progress"

2. Stop Recording
   - User clicks "Stop Recording" button
   - Screen capture and audio recording stop
   - Recorded data is processed and prepared for preview

3. Preview Recorded Content
   - Video is displayed in the video preview area
   - Audio waveform is visualized in the audio preview area

4. Download Video
   - User clicks "Download Video" button
   - Browser initiates download of the recorded video file

5. Download Audio
   - User clicks "Download Audio" button
   - Browser initiates download of the recorded audio file

## Technical Considerations

1. Screen Capture API
   - Use `navigator.mediaDevices.getDisplayMedia()` for screen recording

2. Audio Recording API
   - Use `navigator.mediaDevices.getUserMedia()` for audio recording

3. Media Recording
   - Utilize `MediaRecorder` API for both video and audio recording

4. File Handling
   - Use `Blob` and `URL.createObjectURL()` for file creation and download

5. Audio Visualization
   - Implement Web Audio API for real-time audio waveform visualization

6. Responsive Design
   - Use CSS Flexbox or Grid for layout
   - Implement media queries for mobile responsiveness

7. Error Handling
   - Implement try-catch blocks for API calls
   - Display user-friendly error messages for permission denials or API failures