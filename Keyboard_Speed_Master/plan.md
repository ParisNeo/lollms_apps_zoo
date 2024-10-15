# Keyboard Typing Speed App

## User Requirements

- Create a web application for testing and improving typing speed
- Implement two modes: Training and Test
- Provide multiple texts for users to type
- Display real-time metrics: current speed, average speed, variance
- Show statistics and curves at the end of each session

## User Interface Elements

### Header
- App title: "KeySpeed Master"
- Mode selector: Training / Test

### Main Content Area
- Text display area (shows the text to be typed)
- User input area (where user types)
- Real-time metrics display
  - Current speed (words per minute)
  - Average speed
  - Variance

### Footer
- Start/Reset button
- Text selector dropdown

### Results Modal
- Statistics summary
- Performance curves
- Close button

## Use Cases

1. Training Mode
   - User selects Training mode
   - User chooses a text from the dropdown
   - User starts typing in the input area
   - Real-time metrics update as user types
   - User can reset and start over at any time

2. Test Mode
   - User selects Test mode
   - User chooses a text from the dropdown
   - Timer starts when user begins typing
   - User types the entire text
   - Test ends when text is completed or time runs out
   - Results modal displays statistics and curves

3. View Results
   - User completes a training or test session
   - Results modal appears with statistics and curves
   - User can close modal and start a new session

## Technical Considerations

- Single HTML file structure
  - HTML for layout and structure
  - CSS for styling (internal `<style>` tag)
  - JavaScript for functionality (internal `<script>` tag)

- Libraries to consider:
  - Chart.js for generating performance curves
  - Moment.js for time calculations (if needed)

- JavaScript functions to implement:
  - Text comparison algorithm
  - Words per minute calculation
  - Real-time metrics update
  - Statistics generation
  - Chart rendering