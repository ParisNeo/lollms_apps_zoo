# Tailwind CSS Class Tester Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Usage](#usage)
4. [Components](#components)
5. [Dark Mode](#dark-mode)
6. [Styling](#styling)

## Introduction

The Tailwind CSS Class Tester is a web application that allows users to experiment with Tailwind CSS classes and see their effects in real-time. It provides an interactive interface for selecting and applying various Tailwind CSS classes to a sample text element.

## Features

- Category-based class selection
- Real-time preview of applied classes
- Dark mode support
- Responsive design
- HTML input and preview functionality

## Usage

1. Select a category from the dropdown menu.
2. Choose a specific class from the class dropdown.
3. Click the "Add Class" button to apply the selected class.
4. View the applied classes in the input field.
5. See the real-time preview of the applied classes on the sample text.
6. Enter custom HTML in the input area to see it rendered in the preview section.
7. Use the "Reset" button to clear all applied classes and start over.

## Components

### Category Select
- Dropdown menu for selecting Tailwind CSS categories
- Options include: Text, Background, Layout, Flexbox, Grid, Border, Shadow, Hover, Transition, Position, Overflow, Cursor, Opacity, Z-Index

### Class Select
- Dropdown menu for selecting specific classes within the chosen category
- Dynamically updates based on the selected category

### Add Class Button
- Adds the selected class to the applied classes list

### Applied Classes Input
- Displays all currently applied classes
- Allows manual editing of classes

### HTML Input
- Textarea for entering custom HTML code

### Preview
- Displays the rendered HTML with applied Tailwind CSS classes

### Reset Button
- Clears all applied classes and resets the interface

## Dark Mode

The application supports dark mode, which can be toggled using the switch in the header. Dark mode applies a different color scheme to improve readability in low-light environments.

## Styling

The application uses Tailwind CSS for styling, providing a clean and responsive design. Key style features include:

- Gradient background
- Responsive container layout
- Shadow effects on main content area
- Rounded corners on various elements
- Hover effects on buttons
- Transition animations for smooth user interactions

For detailed styling information, refer to the Tailwind CSS classes used in the HTML structure.