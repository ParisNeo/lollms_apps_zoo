# Project Flow Builder

## Project Overview
Project Flow Builder is a comprehensive web application designed to create task flowcharts from contract, REX (Retour d'Expérience), and risk management documents. It provides a user-friendly interface for project management, risk assessment, task organization, and timeline planning.

## User Requirements
- Create, list, edit, and delete projects
- Manage collaborators and their competencies
- Perform risk management assessments
- Generate task flowcharts from various document types
- Create and edit Gantt diagrams
- Export data in various formats (Markdown, PNG, SVG, HTML)

## User Interface Elements

### Main Page
- Project creation form
- Project list (displayed as cards)
- Collaborator list
- Navigation menu

### Project Card
- Title
- Creation date
- Description
- Budget (if available)

### Project Page
- Tabs for different sections:
  1. Risk Management
  2. Task Organigram
  3. Gantt Diagram

### Risk Management Tab
- Risk assessment table
- Risk family selection
- Risk level input (4-quadrant chart)
- Risk description input
- Export button

### Task Organigram Tab
- Project information input fields
- Document upload area
- Text input area for manual entry
- Generated flowchart display
- Flowchart editing tools
- Export options

### Gantt Diagram Tab
- Generated Gantt chart display
- Timeline editing tools
- Critical path highlighting
- Export options

## Use Cases

1. Create a new project
2. Edit project information
3. Delete a project
4. Add/Edit collaborators
5. Perform risk assessment
6. Generate task flowchart
7. Edit task flowchart
8. Generate Gantt diagram
9. Edit Gantt diagram
10. Export project data

## Technical Considerations

### Libraries
- lollms-anything-to-markdown: For file conversion
- lollms.lc.generateCode: For AI-powered code generation
- Chart.js or D3.js: For rendering flowcharts and Gantt diagrams

### Data Structures

#### Task Flowchart JSON Example
```json
{
  "project": {
    "name": "Project Name",
    "budget": 100000,
    "workPackages": [
      {
        "id": "WP1",
        "name": "Work Package 1",
        "collaborator": "John Doe",
        "budget": 30000,
        "tasks": [
          {
            "id": "T1.1",
            "name": "Task 1.1",
            "description": "Task description"
          }
        ]
      }
    ],
    "warnings": [
      "Budget allocation for WP1 seems unrealistic"
    ]
  }
}
```

#### Gantt Diagram JSON Example
```json
{
  "tasks": [
    {
      "id": "WP1",
      "name": "Work Package 1",
      "start": "2023-06-01",
      "end": "2023-07-15",
      "dependencies": []
    },
    {
      "id": "T1.1",
      "name": "Task 1.1",
      "start": "2023-06-01",
      "end": "2023-06-15",
      "dependencies": ["WP1"]
    }
  ],
  "criticalPath": ["WP1", "T1.1"]
}
```

### File Structure
- Single HTML file containing:
  - HTML structure
  - CSS styles (internal or using a framework like Bootstrap)
  - JavaScript code (including all functionality and API calls)

### API Integration
- Implement functions to interact with lollms APIs for file conversion and code generation
- Handle file uploads and conversions
- Integrate AI-generated content into the user interface

### Data Persistence
- Use localStorage or IndexedDB for client-side data storage
- Implement export and import functionality for project data

### Responsive Design
- Ensure the application is usable on various screen sizes
- Implement mobile-friendly interactions for touch devices