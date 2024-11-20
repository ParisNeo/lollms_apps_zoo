# Village Life Simulator

## App Overview
Village Life Simulator is an interactive web-based simulation that brings to life a virtual village with diverse characters, locations, and dynamic interactions. The application simulates the daily lives, relationships, and activities of villagers in a rich, evolving environment.

## User Requirements
- Create a virtual village with multiple characters (personas) and locations
- Simulate real-time interactions and activities of villagers
- Generate and maintain individual memories, backstories, and statuses for each character
- Enable character decision-making and actions based on their current state and memories
- Provide a user interface to view and interact with the simulation
- Allow exporting and importing of simulation states

## Technology Stack
- HTML5, CSS3, and JavaScript (ES6+)
- Lollms generateCode capability for JSON generation
- LocalStorage for saving and loading simulation states

## User Interface Elements
1. Village Overview
   - Map or grid representation of the village
   - Icons or avatars representing characters and their current locations

2. Character Information Panel
   - Name and basic details
   - Current status and location
   - Recent memories and thoughts
   - Action buttons (e.g., "Interact", "View Details")

3. Simulation Controls
   - Start/Pause simulation
   - Speed control (e.g., 1x, 2x, 4x)
   - Export current state button
   - Import previous state button

4. Event Log
   - Scrollable list of recent events and interactions in the village

5. Time and Date Display
   - Current simulation time and date

## Simulation Components
1. Character Generation
   - Name, age, occupation, personality traits
   - Backstory generation
   - Initial memories and relationships

2. Location Generation
   - Village map with various locations (homes, shops, public spaces)
   - Location attributes (e.g., capacity, purpose)

3. Interaction Engine
   - Character movement between locations
   - Dialogue generation between characters
   - Action generation based on character state and location

4. Memory and State Management
   - Updating and storing character memories
   - Maintaining character status (e.g., mood, needs, goals)

5. Decision-Making System
   - Evaluating current state and memories to determine actions
   - Generating appropriate responses to events and interactions

## Use Cases
1. Village Initialization
   - Generate characters, locations, and initial states
   - Set up starting relationships and memories

2. Character Interactions
   - Characters meet and converse at various locations
   - Memories are formed and updated based on interactions

3. Daily Activities
   - Characters perform actions based on their occupation and needs
   - Visit different locations throughout the day

4. Event Handling
   - Random events occur in the village (e.g., celebrations, conflicts)
   - Characters respond to and participate in events

5. User Observation
   - Users can view real-time updates of character actions and status
   - Inspect individual character details and memories

6. State Management
   - Export current simulation state to JSON
   - Import and resume from a previously saved state

## Implementation Plan
1. Set up HTML structure for the user interface
2. Implement basic CSS styling for layout and components
3. Create JavaScript modules for simulation logic:
   - Character generation and management
   - Location handling
   - Interaction and dialogue system
   - Memory and state tracking
   - Decision-making logic
4. Integrate Lollms generateCode for JSON generation of character states, memories, and actions
5. Implement simulation loop and time management
6. Develop UI update functions to reflect simulation state
7. Add export and import functionality using LocalStorage
8. Implement controls for starting, pausing, and adjusting simulation speed
9. Add random event generation and handling
10. Optimize performance for smooth real-time updates
11. Test and debug the simulation for various scenarios and edge cases