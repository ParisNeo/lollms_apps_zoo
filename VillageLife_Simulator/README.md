# Village Life Simulator Documentation

## Overview

The Village Life Simulator is a web-based application that allows users to create and simulate life in a virtual village. Users can define the number of locations and characters, set the village context, and observe interactions between villagers over time.

## Features

- Dynamic village generation based on user input
- Character creation with unique traits and backstories
- Location generation fitting the village context
- Real-time simulation of villager activities and interactions
- Adjustable simulation speed
- Step-by-step simulation mode
- Export and import of simulation state
- Visual representation of the village map and character information
- Event log to track important occurrences

## User Interface

### Village Map
- Displays locations as yellow squares and villagers as blue circles
- Click on a villager to view their history

### Controls
- Number of Places: Set the number of locations in the village
- Number of Personas: Set the number of villagers
- Village Context: Describe the setting and style of the village
- Build Village: Generate the village based on the input parameters
- Start/Pause Simulation: Toggle the simulation on and off
- Speed Control: Adjust the pace of the simulation
- Export State: Save the current simulation state to a file
- Import State: Load a previously saved simulation state
- Next Step: Advance the simulation by one step (when in step mode)

### Character Information
- Displays current status and basic info for each villager
- "Show Memories" button to view detailed history of a villager

### Event Log
- Chronological list of significant events in the simulation

## Technical Implementation

### Dependencies
- Tailwind CSS for styling
- Lollms Client Library for AI-powered text generation

### Key Functions

#### `generateVillager(villageContext)`
Generates a unique villager with name, age, occupation, personality traits, and backstory.

#### `generateLocation(villageContext)`
Creates a unique location in the village with name, type, capacity, and description.

#### `updateVillagerStatus(villager)`
Updates a villager's current status, including location, activity, mood, and new memories.

#### `generateInteraction(villager1, villager2)`
Simulates an interaction between two villagers, including dialogue and outcomes.

#### `runSimulation()`
Main loop for running the simulation, updating villager statuses and generating interactions.

#### `simulationStep()`
Performs a single step of the simulation, updating all villagers and generating one interaction.

### User Interface Updates

#### `updateVillageMap()`
Refreshes the visual representation of the village map with current locations and villager positions.

#### `updateCharacterInfo()`
Updates the display of villager information cards.

#### `addEventToLog(event)`
Adds a new event to the event log display.

### Data Management

#### `exportBtn` Event Listener
Allows users to save the current simulation state to a JSON file.

#### `importBtn` Event Listener
Enables users to load a previously saved simulation state from a JSON file.

## Getting Started

1. Open the HTML file in a web browser.
2. Set the desired number of places and personas.
3. Enter a village context description.
4. Click "Build Village" to generate the initial state.
5. Use the "Start Simulation" button to begin the simulation.
6. Adjust speed or use step mode as needed.
7. Interact with villager icons to view their history.
8. Use export/import functions to save or load simulation states.