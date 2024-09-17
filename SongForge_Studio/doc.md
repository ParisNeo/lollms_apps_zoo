# Song Building Studio Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [User Interface](#user-interface)
4. [How to Use](#how-to-use)
5. [Localization](#localization)
6. [Technical Details](#technical-details)

## Introduction

Song Building Studio is a web application that helps users generate and enhance song lyrics and styles using AI assistance. It provides an interactive interface for creating, modifying, and saving song ideas.

## Features

- Generate song lyrics and style descriptions based on user input
- Enhance existing lyrics and styles
- Add specific music style elements
- Update lyrics based on custom instructions
- Undo changes for both lyrics and style
- Save and load song data
- Integration with external music creation tools (Suno.ai and Udio.com)
- Multi-language support (English and French)

## User Interface

The application consists of several main sections:

1. **Song Description**: A text area for describing the desired song
2. **Lyrics**: A text area displaying generated or edited lyrics
3. **Style Description**: A text area showing the song's style elements
4. **Music Style Selector**: A dropdown menu for adding predefined style elements
5. **Lyrics Update Instructions**: A text area for entering specific instructions to modify lyrics
6. **Action Buttons**: Various buttons for generating, enhancing, saving, and loading song data
7. **Help Modal**: A pop-up window providing usage instructions
8. **Language Selector**: A dropdown menu for changing the interface language

## How to Use

1. **Generate a Song**:
   - Enter a description in the "Song Description" text area
   - Click the "Generate Song" button
   - View the generated lyrics and style description in their respective text areas

2. **Enhance Lyrics or Style**:
   - Click the "Enhance Lyrics" or "Enhance Style" button to improve the existing content

3. **Add Style Elements**:
   - Select a music style from the dropdown menu
   - Click "Add to Style" to include it in the style description

4. **Update Lyrics**:
   - Enter specific instructions in the "Lyrics Update Instructions" text area
   - Click "Update Lyrics" to modify the existing lyrics based on the instructions

5. **Undo Changes**:
   - Use the "Undo" buttons next to the lyrics and style sections to revert to the previous version

6. **Save and Load Songs**:
   - Click "Save Song" to download the current lyrics and style as a JSON file
   - Click "Load Song" to upload a previously saved JSON file

7. **Access External Tools**:
   - Use the "Open Suno.ai" or "Open Udio.com" buttons to visit external music creation websites

8. **Get Help**:
   - Click the help button (question mark icon) in the bottom-right corner to view usage instructions

## Localization

The application supports multiple languages:

- To change the language, use the language selector dropdown in the top-right corner
- Currently supported languages: English and French

## Technical Details

- Built using HTML, CSS (Tailwind), and JavaScript
- Uses the LollmsClient for AI text generation
- Implements the WebAppLocalizer for multi-language support
- Stores undo history for both lyrics and style modifications
- Utilizes local storage for language preference persistence

Developers can extend the application by:
- Adding new language translations to the `translations` object
- Implementing additional AI-assisted features using the `lc.generate()` method
- Expanding the list of music styles in the dropdown menu
- Enhancing the user interface with additional Tailwind CSS classes