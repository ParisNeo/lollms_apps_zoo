# Interactive Score Editor Documentation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Getting Started](#getting-started)
4. [User Interface](#user-interface)
5. [Working with Notes](#working-with-notes)
6. [Instruments](#instruments)
7. [File Operations](#file-operations)
8. [Playback](#playback)

## Overview
The Interactive Score Editor is a web-based musical notation tool that allows users to create and edit musical scores with multiple instruments using an intuitive interface.

## Features
- Multi-instrument support
- Real-time note input
- MIDI playback functionality
- LilyPond file import/export
- Interactive staff notation
- Multiple note duration options
- Rest insertion capabilities

## Getting Started
1. Open the application in a web browser
2. A default instrument track will be created automatically
3. Click the green "+" button to add more instruments
4. Select note durations from the dropdown menu
5. Click on the staff to place notes

## User Interface

### Main Controls
- **Add Instrument** (Green "+" button)
- **Note Duration Selector** (Dropdown menu)
- **Clear** (Removes all notes)
- **Remove Last Note** (Deletes the most recent note)
- **Load File** (Import LilyPond files)
- **Save File** (Export as LilyPond format)
- **Play** (MIDI playback)

### Staff Display
- Interactive musical staff for each instrument
- Visual note placement guide
- Automatic note snapping to correct positions

## Working with Notes

### Note Duration Options
- Whole Note (1)
- Half Note (2)
- Quarter Note (4)
- Eighth Note (8)
- Sixteenth Note (16)
- Rest

### Adding Notes
1. Select desired duration
2. Click on staff at desired pitch
3. Notes automatically snap to correct positions

### Editing Notes
- Use "Remove Last Note" to delete the most recent note
- Use "Clear" to remove all notes
- Click on staff to add new notes

## Instruments

### Available Instrument Categories
- **Strings**: Violin, Viola, Cello, Double Bass, Guitar, Harp
- **Woodwinds**: Flute, Piccolo, Clarinet, Oboe, Bassoon, Saxophone
- **Brass**: Trumpet, Trombone, French Horn, Tuba
- **Keyboard**: Piano, Harpsichord, Organ
- **Percussion**: Drums, Timpani, Xylophone, Marimba, Vibraphone
- **Voice**: Soprano, Alto, Tenor, Bass

### Managing Instruments
- Add new instruments with the "+" button
- Remove instruments using the "×" button on each staff
- Select instrument type from dropdown menu

## File Operations

### Loading Files
1. Click "Load File" button
2. Select a LilyPond (.ly) file
3. Score will be automatically imported

### Saving Files
1. Click "Save File" button
2. File will be downloaded as "score.ly"
3. Contains complete LilyPond notation

## Playback

### MIDI Playback Features
- Real-time synthesis of all instrument parts
- Instrument-specific sound profiles
- Synchronized playback of all staves

### Instrument Sound Profiles
- Piano: Polyphonic synthesis
- Strings: Sawtooth wave with sustain
- Woodwinds: Sine wave with quick attack
- Brass: Square wave with medium attack

---
*Note: This application requires a modern web browser with JavaScript enabled.*