### `README.md`

```markdown
# ScrapeMaster GUI

**ScrapeMaster GUI** is a desktop application built with PyQt5 that provides a user-friendly interface for the [ScrapeMaster](https://github.com/ParisNeo/scrapemaster) web scraping library. It simplifies the process of extracting content from web pages, allowing users to view data as raw Markdown or rendered HTML, save and load scraping sessions, and customize scraping parameters.

*(Generated: 2025-05-07 13:00:42)*

## Features

*   **User-Friendly Interface**: Intuitive PyQt5 GUI for easy web scraping.
*   **URL Scraping**: Input a URL and initiate scraping with a single click.
*   **Dual View Output**:
    *   View scraped content in **Raw Markdown** format (editable).
    *   Preview content as **Rendered HTML**.
*   **File Management**:
    *   **Save**: Store scraped URL and Markdown content in JSON format.
    *   **Load**: Open previously saved JSON scraping sessions.
    *   **Export**: Save raw Markdown content to `.md` files.
    *   **Recent Files**: Quickly access recently opened/saved files.
*   **Customizable Scraping Settings**:
    *   **Strategy Selection**: Choose and order scraping strategies supported by ScrapeMaster.
    *   **Headless Mode**: Toggle headless browser operation for relevant strategies.
    *   **Crawl Depth**: Set the maximum depth for scraping multiple linked pages.
*   **Theme Support**: Customize the application's appearance with various themes powered by `qt_material`.
*   **Icon Integration**: Enhanced user experience with icons from `qtawesome`.
*   **Status Bar**: Get real-time feedback, warnings, and error messages.
*   **Clipboard**: Easily copy the raw Markdown output.
*   **URL Handling**: Automatic detection and prefixing for `http://` or `https://` schemes.

## Folder Structure

```text
📁 scrape_master/
├─ 📁 assets/
├─ 📄 description.yaml
└─ 📄 scrape_master.py
```

## File Contents

*   **`scrape_master.py`**: The main Python script containing the PyQt5 application code for the ScrapeMaster GUI.
*   **`description.yaml`**: Metadata file describing the ScrapeMaster GUI application, its features, and other relevant information.
*   **`assets/`**: Directory intended for local assets like custom icons (if not solely relying on qtawesome).

## Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)
*   A graphical environment (since it's a GUI application)
*   The `ScrapeMaster` library.

## Installation

1.  **Clone the repository (or download the files):**
    If this GUI is part of the main ScrapeMaster repository:
    ```bash
    git clone https://github.com/ParisNeo/scrapemaster.git
    cd scrapemaster/scrape_master_gui # Adjust path if needed
    ```
    If it's a standalone repository:
    ```bash
    git clone <repository_url>
    cd scrape_master
    ```

2.  **Install `pipmaster` (if not already installed):**
    `pipmaster` is used by the script to ensure other dependencies are present.
    ```bash
    pip install pipmaster
    ```

3.  **Install Dependencies:**
    The script `scrape_master.py` attempts to install required packages using `pipmaster` upon its first run:
    `PyQt5`, `markdown`, `qt_material`, `qtawesome`.

    You also need the `ScrapeMaster` library itself. If it's not installed as a standard Python package, ensure it's accessible. The script attempts to find it in the parent directory: `../scrapemaster`.
    If `ScrapeMaster` is a pip-installable package:
    ```bash
    pip install scrapemaster
    ```

4.  **Ensure ScrapeMaster Library Path:**
    If the `ScrapeMaster` library is not installed via pip and resides in a custom location, you might need to adjust `sys.path` in `scrape_master.py` or ensure the relative path (`../scrapemaster`) is correct.

## Usage

1.  Navigate to the directory containing `scrape_master.py`.
2.  Run the application:
    ```bash
    python scrape_master.py
    ```

**Using the GUI:**

*   **Enter URL**: Type or paste the web page URL you want to scrape into the input field.
*   **Scrape**: Click the "Scrape" button to start the process.
*   **View Output**:
    *   The **Raw Markdown** tab will display the extracted content in Markdown format.
    *   The **Rendered HTML** tab will show a preview of the Markdown.
*   **File Menu**:
    *   `Load JSON...`: Load previously saved scraped data.
    *   `Save As JSON...`: Save the current URL and Markdown content.
    *   `Export as Markdown (.md)...`: Export only the Markdown to a `.md` file.
    *   `Recent Files`: Access recently loaded/saved files.
    *   `Exit`: Close the application.
*   **Options Menu**:
    *   `Settings...`: Open the settings dialog to configure scraping strategies, headless mode, and crawl depth.
*   **View Menu**:
    *   `Theme`: Select a UI theme for the application.
*   **Copy Button**: Click "Copy Raw Markdown" to copy the content of the Raw Markdown tab to your clipboard.
*   **Status Bar**: Check the bottom of the window for status messages, warnings, or errors.

## Configuration

### Scraping Settings
Accessible via `Options > Settings...`

*   **Scraping Strategies**: Check the boxes next to the strategies you want to enable. ScrapeMaster will try them in the order they appear.
*   **Headless Mode**: Check "Run browser headless" if you want browser-based strategies (like Playwright or Selenium, if supported by your ScrapeMaster version) to run without a visible browser window.
*   **Crawl Depth**: Set the maximum number of linked pages to scrape starting from the initial URL. `0` means only the initial URL will be scraped.

### Themes
Accessible via `View > Theme`

Select your preferred user interface theme from the list. The theme is applied instantly. Your selected theme is saved and will be loaded the next time you start the application.

## File Formats

*   **Saved Data (`.json`)**:
    When you save a session, a JSON file is created containing:
    ```json
    {
        "url": "THE_SCRAPED_URL",
        "markdown": "THE_EXTRACTED_MARKDOWN_CONTENT",
        "scraped_at": "YYYY-MM-DD HH:MM:SS TZ"
    }
    ```
*   **Exported Markdown (`.md`)**:
    A plain text file containing only the raw Markdown content.

## Disclaimer

This application is provided "as-is" without any warranties. The accuracy and completeness of the scraped output depend on the ScrapeMaster library, the target website's structure, and the user's configuration. Users should review the output carefully and ensure compliance with website terms of service. The developers are not responsible for any issues arising from the use of this tool.

## Author

*   ParisNeo with gemini 2.5 & claude

## License

This project is licensed under the Apache 2.0 License.