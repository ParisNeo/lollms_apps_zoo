# Strawberry Dice Roller 🌟

## Overview

The Strawberry Dice Roller is a web application that allows users to roll virtual dice with a strawberry theme. It features a responsive design, language localization, dark mode, and customizable settings.

## Features

- Roll one or two dice
- Animated dice rolling
- Sound effects
- Dark mode toggle
- Language selection (English, French, Spanish)
- Roll history
- Customizable settings

## Technical Stack

- HTML5
- CSS3 (with Tailwind CSS)
- JavaScript (ES6+)
- GSAP for animations
- Web App Localizer for translations

## File Structure

```
index.html
```

## HTML Structure

The `index.html` file contains the entire application structure, including:

- Header with title and controls
- Main content area with dice display and roll button
- Settings menu
- Footer

## JavaScript Functionality

### Key Components

1. `WebAppLocalizer`: Handles language translations
2. Dice creation and animation
3. Dark mode toggle
4. Settings menu
5. Roll history management

### Important Functions

- `createDice()`: Generates HTML for a single die
- `updateDiceDisplay()`: Updates the number of dice shown
- `rollDice()`: Handles the dice rolling animation and result calculation
- `getDiceTransform(number)`: Returns the 3D transform for a specific die face
- `toggleDarkMode()`: Switches between light and dark themes
- `updateRollHistory(result)`: Adds new roll results to the history
- `displayRollHistory()`: Shows the last 5 roll results

## Styling

The application uses a combination of Tailwind CSS classes and custom CSS for styling. Key style features include:

- Responsive design
- 3D dice rendering using CSS transforms
- Animated dice rolling and floating effects
- Gradient backgrounds for header and footer

## Localization

Translations are stored in the `translations` object, supporting English, French, and Spanish. The `WebAppLocalizer` class handles language switching and text updates.

## Local Storage

The application uses local storage to remember user preferences:

- `strawberryDiceRoller_diceCount`: Number of dice to display
- `strawberryDiceRoller_darkMode`: Dark mode state
- `strawberryDiceRoller_rollHistory`: Recent roll results

## Event Listeners

- Roll button: Triggers dice roll
- Dark mode toggle: Switches theme
- Settings toggle: Opens/closes settings menu
- Dice count selector: Updates number of dice
- Language selector: Changes application language

## External Dependencies

- Tailwind CSS (via CDN)
- GSAP (for animations)
- Web App Localizer (custom script)
- Dice rolling sound effect (external audio file)

## Usage

To use the application, simply open the `index.html` file in a web browser. No additional setup or build process is required.