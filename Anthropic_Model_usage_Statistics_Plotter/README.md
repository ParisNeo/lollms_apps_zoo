# Anthropic Model Usage Statistics Plotter

This web application allows users to visualize and analyze their Anthropic model usage statistics by uploading a CSV file exported from the Anthropic dashboard.

## Features

- Upload and process Anthropic usage CSV files
- View data summary and AI-generated insights
- Interactive charts for visualizing usage data
- Multiple chart types:
  - Time Series
  - Model Version Comparison
  - Workspace Usage
  - Usage Types
  - Workspace Usage Over Time
  - API Usage Over Time
- Zoom and pan functionality for charts
- Export charts as PNG
- Export processed data as JSON

## How to Use

1. Export a CSV file from your Anthropic dashboard.
2. Open the Anthropic Statistics Plotter web application.
3. Click "Choose File" and select the exported CSV file.
4. Click "Upload and Process" to analyze the data.
5. View the Data Summary for an overview of your usage.
6. Select different chart types from the dropdown menu to visualize your data.
7. Use mouse wheel or pinch to zoom in/out of charts.
8. Click and drag to pan around zoomed charts.
9. Use the "Reset Zoom" button to return to the original view.
10. Export charts as PNG or data as JSON for further analysis using the provided buttons.

## Technical Details

The application is built using:

- HTML5
- JavaScript
- Tailwind CSS for styling
- Chart.js for data visualization
- Papa Parse for CSV parsing
- Hammer.js and chartjs-plugin-zoom for chart interactions

## Setup

No installation is required. Simply open the `index.html` file in a modern web browser to use the application.

## Data Privacy

This application processes data entirely in the browser. No data is sent to any server or stored externally.

## Troubleshooting

If you encounter any issues:

1. Ensure you're using the latest version of your web browser.
2. Check that the CSV file is correctly formatted and exported from the Anthropic dashboard.
3. Clear your browser cache and reload the page.

For additional help, click the "Help" button in the application for a step-by-step guide.