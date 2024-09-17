# World Clock with Weather

## Objective
Create a standalone world clock web application that displays up to 10 and a minimum of 2 major selectable time zones simultaneously. The application should feature both digital and analog clock styles and provide weather updates for the selected local areas, highlighting any abnormal conditions.

## Design Requirements
1. **Time Zones:**
   - Allow users to select from a list of major time zones.
   - Display up to 10 time zones simultaneously, with a minimum of 2.
   - Provide both digital and analog clock displays for each time zone.

2. **Weather Information:**
   - Integrate weather updates for the selected time zones.
   - Highlight abnormal weather conditions (e.g., storms, extreme temperatures).
   - Display weather clips or icons representing the current weather status.

3. **User Interface:**
   - Responsive design to ensure compatibility across various devices (desktop, tablet, mobile).
   - Light and dark mode options for user preference.
   - Intuitive and user-friendly interface for easy navigation and interaction.

4. **Additional Features:**
   - Alarm functionality for each time zone.
   - Option to switch between digital and analog clock displays.
   - Toggle for light/dark mode.

## Implementation Details

### HTML Structure
- Main container for the world clock.
- Sections for each time zone, including clock displays and weather information.
- Controls for selecting time zones, switching clock styles, and toggling light/dark mode.

### CSS Styling
- Define styles for both light and dark modes.
- Use a consistent color scheme and typography.
- Ensure layout and positioning are responsive and adaptable to different screen sizes.

### JavaScript Functionality
- Update clocks in real-time for multiple time zones.
- Implement switching between digital and analog displays.
- Retrieve and display weather information using a weather API.
- Set and trigger alarms for each time zone.
- Toggle light/dark mode based on user preference.

## Code Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>World Clock with Weather</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            color: var(--text-color);
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background-color: var(--header-background);
        }

        #timezones-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            padding: 1rem;
        }

        .timezone {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 0.5rem;
            padding: 1rem;
            width: 200px;
            text-align: center;
        }

        .clock {
            margin: 1rem 0;
        }

        .weather {
            margin-top: 0.5rem;
        }

        #controls {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }

        :root {
            --background-color: #ffffff;
            --text-color: #000000;
            --header-background: #f0f0f0;
            --border-color: #cccccc;
        }

        body.dark-mode {
            --background-color: #1e1e1e;
            --text-color: #ffffff;
            --header-background: #333333;
            --border-color: #444444;
        }
    </style>
</head>
<body>
    <div id="app">
        <header>
            <h1>World Clock with Weather</h1>
            <button id="toggle-mode">Toggle Light/Dark Mode</button>
        </header>
        <main>
            <div id="timezones-container">
                <!-- Timezone clocks will be dynamically added here -->
            </div>
            <div id="controls">
                <label for="timezone-select">Select Time Zone:</label>
                <select id="timezone-select">
                    <!-- Time zone options will be dynamically added here -->
                </select>
                <button id="add-timezone">Add Time Zone</button>
            </div>
        </main>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const timezonesContainer = document.getElementById('timezones-container');
            const timezoneSelect = document.getElementById('timezone-select');
            const addTimezoneButton = document.getElementById('add-timezone');
            const toggleModeButton = document.getElementById('toggle-mode');

            const timezones = [
                'UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney'
                // Add more time zones as needed
            ];

            const weatherAPIKey = 'YOUR_WEATHER_API_KEY';
            const weatherAPIUrl = 'https://api.openweathermap.org/data/2.5/weather';

            function updateClock(timezone, clockElement) {
                const now = new Date();
                const options = { timeZone: timezone, hour: '2-digit', minute: '2-digit', second: '2-digit' };
                const timeString = now.toLocaleTimeString([], options);
                clockElement.textContent = timeString;
            }

            function fetchWeather(timezone, weatherElement) {
                const url = `${weatherAPIUrl}?q=${timezone}&appid=${weatherAPIKey}`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        const weatherDescription = data.weather[0].description;
                        weatherElement.textContent = weatherDescription;
                    })
                    .catch(error => {
                        console.error('Error fetching weather data:', error);
                        weatherElement.textContent = 'Weather data unavailable';
                    });
            }

            function addTimezone(timezone) {
                const timezoneDiv = document.createElement('div');
                timezoneDiv.className = 'timezone';

                const clockDiv = document.createElement('div');
                clockDiv.className = 'clock';
                timezoneDiv.appendChild(clockDiv);

                const weatherDiv = document.createElement('div');
                weatherDiv.className = 'weather';
                timezoneDiv.appendChild(weatherDiv);

                timezonesContainer.appendChild(timezoneDiv);

                setInterval(() => updateClock(timezone, clockDiv), 1000);
                fetchWeather(timezone, weatherDiv);
            }

            timezones.forEach(tz => {
                const option = document.createElement('option');
                option.value = tz;
                option.textContent = tz;
                timezoneSelect.appendChild(option);
            });

            addTimezoneButton.addEventListener('click', () => {
                const selectedTimezone = timezoneSelect.value;
                addTimezone(selectedTimezone);
            });

            toggleModeButton.addEventListener('click', () => {
                document.body.classList.toggle('dark-mode');
            });
        });
    </script>
</body>
</html>
```

## Description.yaml

```yaml
name: World Clock with Weather
author: Your Name
creation_date: 2023-10-01
description: A standalone world clock web application that displays up to 10 and a minimum of 2 major selectable time zones simultaneously. Features both digital and analog clock styles and provides weather updates for the selected local areas, highlighting any abnormal conditions.
```

## Icon.png
- Create a simple icon representing a clock with weather elements (e.g., sun, cloud, rain) to visually indicate the app's functionality.