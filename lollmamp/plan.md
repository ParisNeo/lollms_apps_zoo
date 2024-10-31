# Lollmamp

## Refined User Requirements

Develop a Winamp-inspired web application named **Lollmamp** that provides a comprehensive MP3 playing experience. The application should support the following core functionalities:

- **File Management:** Ability to add individual MP3 files and entire folders to the playlist.
- **Playback Controls:** Play, pause, stop, shuffle, and repeat tracks.
- **Navigation:** Seek to specific timestamps within a track.
- **Volume Control:** Adjust the playback volume seamlessly.
- **User Interface:** Aesthetic and responsive design utilizing TailwindCSS to ensure an intuitive and engaging user experience.

The goal is to create the most efficient and user-friendly MP3 player available as a single-file web application.

## Libraries and Tools

- **TailwindCSS:** For efficient and responsive styling.
- **JavaScript (ES6):** For implementing application logic and interactivity.
- **HTML5 Audio API:** To handle audio playback functionalities.
- **LocalStorage:** To persist user playlists across sessions.

## User Interface Components

1. **Header Section**
   - **App Title:** Display the name "Lollmamp".
   - **Logo/Icon:** A stylized icon representing the MP3 player.

2. **Playlist Panel**
   - **File/Folders Addition:**
     - Buttons to add individual MP3 files.
     - Option to add entire folders.
   - **Playlist Display:**
     - List of added tracks with track information (Title, Artist, Duration).
     - Ability to reorder or remove tracks.

3. **Now Playing Section**
   - **Track Details:**
     - Display current track's title, artist, and album art if available.
   - **Playback Controls:**
     - Play/Pause, Stop, Next, Previous buttons.
     - Shuffle and Repeat toggle buttons.
   - **Seek Bar:**
     - Interactive slider to navigate to different parts of the track.
     - Display of elapsed and remaining time.
   - **Volume Control:**
     - Slider to adjust volume.
     - Mute/Unmute button.

4. **Footer Section**
   - **Status Indicators:**
     - Current playback status (e.g., Playing, Paused).
   - **Progress Bar:**
     - Visual representation of the current track's progress.

## Use Cases

1. **Adding MP3 Files**
   - User clicks the "Add Files" button.
   - Selects one or multiple MP3 files from the device.
   - Selected files are added to the playlist display.

2. **Adding Folders**
   - User clicks the "Add Folder" button.
   - Selects a folder containing MP3 files.
   - All MP3 files within the folder are recursively added to the playlist.

3. **Playing a Track**
   - User selects a track from the playlist.
   - Clicks the "Play" button.
   - The selected track begins playback with its details displayed in the Now Playing section.

4. **Shuffling Playlists**
   - User toggles the "Shuffle" button.
   - Tracks play in a random order without repetition until all tracks have been played.

5. **Seeking Within a Track**
   - User interacts with the seek bar slider.
   - The playback position updates to the selected timestamp within the track.

6. **Controlling Volume**
   - User adjusts the volume slider to increase or decrease the playback volume.
   - User can mute or unmute the audio using the dedicated button.

7. **Persisting Playlists**
   - User's playlist is automatically saved using LocalStorage.
   - Upon revisiting the application, the saved playlist is loaded automatically.

## Technical Considerations

- **Single HTML File Structure:**
  - Inline CSS using TailwindCSS.
  - Embedded JavaScript for all functionalities.
- **Responsive Design:**
  - Ensure the application is accessible and visually appealing across various devices and screen sizes.
- **Performance Optimization:**
  - Efficient loading and handling of MP3 files to prevent lag or delays.
- **Accessibility:**
  - Implement ARIA labels and keyboard navigation support for enhanced accessibility.