# Meeting Minutes Generator

## App Overview
The Meeting Minutes Generator is a single-file web application that transcribes audio recordings of meetings and generates comprehensive meeting minutes using Lollms AI technology.

## User Requirements
- Capture or upload audio recordings of meetings
- Transcribe audio using Lollms AI
- Generate meeting minutes from the transcription
- Save meeting minutes in multiple formats
- Copy meeting minutes to clipboard

## User Interface Elements
1. Header
   - App title and logo
2. Audio Input Section
   - Record audio button
   - Upload audio file button
   - Audio player for playback
3. Transcription Section
   - Transcribe button
   - Transcription text area (read-only)
4. Meeting Minutes Section
   - Generate minutes button
   - Meeting minutes text area (editable)
5. Export Options
   - Save as PDF button
   - Save as DOC button
   - Save as TXT button
   - Copy to clipboard button
6. Footer
   - App information and credits

## Use Cases
1. Record Meeting Audio
   - User clicks "Record" button
   - App captures audio from device microphone
   - User clicks "Stop" to end recording
2. Upload Audio File
   - User clicks "Upload" button
   - File explorer opens for WAV file selection
   - Selected file loads into audio player
3. Transcribe Audio
   - User clicks "Transcribe" button
   - App sends audio to Lollms AI for transcription
   - Transcribed text appears in transcription area
4. Generate Meeting Minutes
   - User clicks "Generate Minutes" button
   - App sends transcription to Lollms AI for processing
   - Generated minutes appear in meeting minutes area
5. Edit Meeting Minutes
   - User can manually edit text in meeting minutes area
6. Export Meeting Minutes
   - User selects desired export format (PDF, DOC, TXT)
   - App generates and downloads file in chosen format
7. Copy to Clipboard
   - User clicks "Copy to Clipboard" button
   - Meeting minutes text is copied to system clipboard

## Technical Considerations
- Use HTML5 audio APIs for recording and playback
- Implement Lollms AI integration for transcription and minutes generation
- Utilize browser's built-in PDF generation for PDF export
- Use libraries like docx.js for DOC file creation
- Implement responsive design for mobile and desktop use