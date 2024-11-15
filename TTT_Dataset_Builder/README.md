# Test-Time Training Dataset Generator Documentation

## Overview

The Test-Time Training Dataset Generator is a web application that allows users to create datasets for test-time training using the Lollms AI framework. This tool enables users to generate example tasks and solutions based on a given task description, manage saved tasks, and export/import datasets in JSON format.

## Features

1. Generate example tasks and solutions
2. Specify the number of samples to generate
3. Clear generated examples
4. Export dataset to JSON
5. Import dataset from JSON
6. Save and load task descriptions
7. Edit and remove saved tasks

## User Interface

The application consists of the following main sections:

1. Task Description Input
2. Number of Samples Input
3. Action Buttons
4. Generated Examples Display
5. Saved Tasks Management

## Usage

### Generating Examples

1. Enter a task description in the "Task Description" textarea.
2. Specify the number of samples to generate in the "Number of Samples" input field.
3. Click the "Generate Examples" button to create example tasks and solutions.

### Managing Examples

- **Clear All**: Remove all generated examples from the current session.
- **Export JSON**: Save the current set of examples as a JSON file.
- **Reload from JSON**: Import previously exported examples from a JSON file.

### Task Management

- **Save Task**: Store the current task description for future use.
- **Load Task**: View and select from previously saved task descriptions.
- **Edit Task**: Modify a saved task description.
- **Remove Task**: Delete a saved task description.
- **Use Task**: Load a saved task description into the main input field.

## Technical Details

### Dependencies

- Tailwind CSS (via CDN)
- Lollms Client JavaScript library
- Axios library

### Lollms Integration

The application uses the Lollms Client to generate example tasks and solutions. The client is initialized with default parameters:

```javascript
const lc = new LollmsClient(null, null, 4096, -1, 4096, 0.7, 50, 0.95, 0.8, 40, null, 8);
```

### Data Structure

Generated examples are stored as an array of objects, each containing:

- `task_prompt`: A description of the task
- `task_solution`: The expected solution for the task

### Local Storage

The application uses local storage to persist:

- Saved task descriptions
- The last used task description

### Error Handling

The application includes basic error handling for:

- Invalid input (empty task description or invalid number of samples)
- JSON parsing errors when importing datasets
- Network or generation errors when using the Lollms Client

## Customization

To modify the application's appearance or behavior, edit the HTML structure, CSS classes, or JavaScript code as needed. The Tailwind CSS framework is used for styling, allowing for easy customization of the user interface.