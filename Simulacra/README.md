# Simulacra: Artificial Life Simulation

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Getting Started](#getting-started)
4. [User Interface](#user-interface)
5. [Simulation Settings](#simulation-settings)
6. [Running the Simulation](#running-the-simulation)
7. [Statistics and Charts](#statistics-and-charts)
8. [Saving Results](#saving-results)
9. [Organism Behavior](#organism-behavior)
10. [Food Generation](#food-generation)
11. [Customization](#customization)

## Introduction
Simulacra is a web-based artificial life simulation that allows users to observe and interact with a population of digital organisms as they evolve and adapt to their environment.

## Features
- Interactive canvas-based simulation
- Customizable simulation parameters
- Real-time statistics tracking
- Line chart visualization of population metrics
- CSV export of simulation results
- Organism tooltips on mouseover

## Getting Started
To run the simulation, simply open the `index.html` file in a modern web browser. The application uses CDN-hosted libraries, so an internet connection is required.

## User Interface
The interface consists of:
- A large canvas where the simulation takes place
- Control buttons (Start Simulation, Simulate, Stop, Save Results)
- A statistics panel showing current population metrics
- A line chart displaying historical data
- A settings popup for configuring simulation parameters

## Simulation Settings
Users can customize the following parameters:
- Initial Population Size
- Initial Food Amount
- Food Spawn Rate
- Energy Depletion Speed
- Random Mutations (enabled/disabled)
- Search Pattern (Nearest Food, Random Movement, Zigzag Pattern)

## Running the Simulation
1. Click "Start Simulation" to open the settings popup
2. Adjust the parameters as desired
3. Click "Apply and Start" to begin the simulation
4. Use the "Simulate" button to resume a paused simulation
5. Click "Stop" to pause the simulation at any time

## Statistics and Charts
The application displays real-time statistics including:
- Current population count
- Average speed of organisms
- Average vision range of organisms
- Current food count

A line chart shows the historical trends of these metrics over generations.

## Saving Results
Click the "Save Results" button to export the simulation data as a CSV file. The file will contain generation-by-generation statistics for further analysis.

## Organism Behavior
Organisms in the simulation:
- Move according to the selected search pattern
- Consume food to gain energy
- Reproduce when they have sufficient energy
- Die when their energy is depleted

## Food Generation
Food items appear randomly on the canvas based on the configured spawn rate.

## Customization
Advanced users can modify the `script` section of the HTML file to adjust organism properties, alter food mechanics, or implement new features.