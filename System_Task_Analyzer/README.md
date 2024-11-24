# System Task Analyzer

The System Task Analyzer is a web application designed to help users analyze their system's running tasks and identify potential security threats. This application leverages the Lollms library to provide a comprehensive analysis of system processes.

## Features

- **Running Tasks Overview**: View a list of currently running tasks on your system.
- **Task Analysis**: Analyze tasks to identify potentially suspicious processes.
- **Task Details**: Click on a task to view detailed information.
- **Sorting Options**: Sort tasks by name, memory usage, or CPU usage.
- **Process Management**: Refresh the list of tasks and stop processes if necessary.

## Getting Started

### Prerequisites

- Ensure you have the Lollms library and its dependencies installed.
- The application requires a server running at `http://localhost:8000` to fetch and manage system processes.

### Installation

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Open `index.html` in your preferred web browser.

### Usage

1. **Refresh Processes**: Click the "Refresh processes" button to update the list of running tasks.
2. **Start Analysis**: Click the "Start Analysis" button to analyze the running tasks for potential threats.
3. **Sort Tasks**: Use the dropdown menu to sort tasks by name, memory, or CPU usage. Toggle the sort order using the adjacent button.
4. **View Task Details**: Click on a task in the list to view detailed information.
5. **Stop Process**: Click the "Stop" button next to a task to terminate it.

### User Interface

- **Running Tasks Section**: Displays a list of running tasks with options to refresh and analyze.
- **Analysis Results Section**: Shows the results of the task analysis.
- **Task Details Section**: Provides detailed information about a selected task.
- **Loading Overlay**: Displays a loading spinner during long operations.

### Code Structure

- **HTML**: The user interface is built using Tailwind CSS for styling and layout.
- **JavaScript**: The application logic is implemented using JavaScript, with Axios for HTTP requests and LollmsClient for task analysis.

### Customization

- Modify the `LollmsClient` settings in the JavaScript section to customize the analysis parameters.
- Adjust the Tailwind CSS classes in the HTML to change the appearance of the application.

## License

This project is licensed under the MIT License.

## Acknowledgments

- [Tailwind CSS](https://tailwindcss.com/) for styling.
- [Axios](https://axios-http.com/) for HTTP requests.
- [Lollms](https://lollms.com/) for task analysis capabilities.
