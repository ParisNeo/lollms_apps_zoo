# -*- coding: utf-8 -*-
# Project: ScrapeMaster GUI
# Author: ParisNeo with gemini 2.5 & claude
# Description: A PyQt5 GUI application for the ScrapeMaster library, allowing users to scrape web content, view it raw or rendered, save/load results, and manage scraping settings, with persistent theming and proper icon integration.

import sys
import json
import os
from urllib.parse import urlparse
import time
import traceback
import functools
from pathlib import Path

try:
    import pipmaster as pm
    pm.ensure_packages(["PyQt5", "markdown", "qt_material", "qtawesome"])
except ImportError:
    print("Error: pipmaster not found...") # Keep error handling
    sys.exit(1)
except Exception as e:
    print(f"Error ensuring packages: {e}")
    sys.exit(1)

try:
    # --- PyQt5 Imports FIRST ---
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLineEdit, QPushButton, QTextEdit, QLabel, QAction, QFileDialog,
        QMessageBox, QMenu, QStatusBar, QTabWidget, QDialog, QCheckBox,
        QDialogButtonBox, QGridLayout, QSpinBox
    )
    from PyQt5.QtCore import QSettings, Qt, pyqtSignal
    # Explicitly import QFontDatabase and QIcon from QtGui
    from PyQt5.QtGui import QIcon, QFontDatabase, QColor # <-- Added QFontDatabase, QColor

    # --- Import qt_material AFTER PyQt ---
    import qt_material

    # --- Import qtawesome ---
    import qtawesome as qta

except ImportError as e:
    print(f"Error: Missing required PyQt5 components, markdown, qt_material, or qtawesome. ({e})")
    print("Please ensure PyQt5, markdown, qt_material, and qtawesome are installed correctly.")
    print("Ensure PyQt5 is imported before qt_material.") # Added note
    sys.exit(1)


try:
    import markdown
except ImportError:
    print("Error: 'markdown' library not found. Please install it: 'pip install markdown'")
    sys.exit(1)

# --- Adjust path for ScrapeMaster ---
try:
    current_dir = Path(__file__).parent
    scrapemaster_path = current_dir.parent / 'scrapemaster'
    if not scrapemaster_path.exists():
         pass
    else:
         # Prepend parent dir to sys.path ONLY if scrapemaster is found there
         # Avoids potential conflicts if scrapemaster is properly installed
         sys.path.insert(0, str(current_dir.parent))

    from scrapemaster import ScrapeMaster
    from scrapemaster.core import SUPPORTED_STRATEGIES, DEFAULT_STRATEGY_ORDER
except ImportError as e:
     print(f"Error importing ScrapeMaster library: {e}")
     print("Please ensure the ScrapeMaster library is installed or accessible.")
     print("If running from source, ensure the path is correct relative to the script.")
     print(f"Current script directory: {current_dir}")
     print(f"Attempted parent directory: {current_dir.parent}")
     print(f"Python search path: {sys.path}")
     sys.exit(1)


APP_NAME = "ScrapeMaster GUI"
ORG_NAME = "AICodeHelper"
MAX_RECENT_FILES = 10
SETTINGS_RECENT_FILES = "recentFiles"
SETTINGS_STRATEGY_PREFIX = "settings/strategyEnabled_"
SETTINGS_HEADLESS = "settings/headlessMode"
SETTINGS_CRAWL_DEPTH = "settings/crawlDepth"
SETTINGS_SELECTED_THEME = "selectedTheme"
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_WINDOW_STATE = "window/state"
DEFAULT_THEME = "light_cyan_500.xml"

# --- Global variable to hold the current theme name applied ---
# Needed because apply_stylesheet is called on the QApplication instance
g_current_theme_file = DEFAULT_THEME

# --- Global function to apply theme ---
# This needs to be called *before* the main window is shown
def apply_theme_globally(app_instance: QApplication, theme_file: str):
    global g_current_theme_file
    try:
        if not theme_file:
            theme_file = DEFAULT_THEME
            print(f"Warning: Invalid theme name provided, falling back to default {DEFAULT_THEME}.")

        qt_material.apply_stylesheet(
            app_instance,
            theme=theme_file,
            invert_secondary=('dark' in theme_file)
        )
        g_current_theme_file = theme_file
        print(f"Theme '{theme_file}' applied globally.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to apply theme '{theme_file}': {e}")
        # Attempt to apply default if the requested one failed
        if theme_file != DEFAULT_THEME:
            try:
                qt_material.apply_stylesheet(app_instance, theme=DEFAULT_THEME, invert_secondary=False)
                g_current_theme_file = DEFAULT_THEME
                print(f"Fell back to default theme '{DEFAULT_THEME}'.")
                QMessageBox.critical(None, "Theme Error", f"Failed to apply theme '{theme_file}'.\nFalling back to default.\nError: {e}")
                return False
            except Exception as e_default:
                print(f"CRITICAL: Failed to apply even the default theme '{DEFAULT_THEME}': {e_default}")
                QMessageBox.critical(None, "Critical Theme Error", f"Failed to apply theme '{theme_file}' AND the default theme '{DEFAULT_THEME}'.\nApplication appearance may be broken.\nError: {e_default}")
                return False
        else: # Failed even on default
             QMessageBox.critical(None, "Critical Theme Error", f"Failed to apply the default theme '{DEFAULT_THEME}'.\nApplication appearance may be broken.\nError: {e}")
             return False


def is_valid_url_for_gui(url_string: str) -> bool:
    if not isinstance(url_string, str): return False
    try:
        result = urlparse(url_string)
        # Allow more schemes if needed, e.g., file, ftp
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except ValueError: return False


class SettingsDialog(QDialog):
    settingsChanged = pyqtSignal()

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Scraper Settings")
        self.setWindowIcon(qta.icon('mdi.cogs')) # Keep using qtawesome for window icon
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.strategy_checkboxes = {}
        grid_layout.addWidget(QLabel("<b>Scraping Strategies (in order):</b>"), 0, 0, 1, 2)
        row = 1
        for strategy in DEFAULT_STRATEGY_ORDER:
            if strategy not in SUPPORTED_STRATEGIES: continue
            checkbox = QCheckBox(strategy.capitalize())
            setting_key = f"{SETTINGS_STRATEGY_PREFIX}{strategy}"
            is_enabled = self.settings.value(setting_key, True, type=bool)
            checkbox.setChecked(is_enabled)

            # <<< --- ADD THIS LINE --- >>>
            checkbox.setStyleSheet("") # Reset stylesheet to use system default

            grid_layout.addWidget(checkbox, row, 0)
            self.strategy_checkboxes[strategy] = checkbox
            row += 1

        grid_layout.addWidget(QLabel("<b>Options:</b>"), row, 0, 1, 2)
        row += 1
        self.headless_checkbox = QCheckBox("Run browser headless (no visible window)")
        headless_enabled = self.settings.value(SETTINGS_HEADLESS, True, type=bool)
        self.headless_checkbox.setChecked(headless_enabled)

        # <<< --- ADD THIS LINE --- >>>
        self.headless_checkbox.setStyleSheet("") # Reset stylesheet to use system default

        grid_layout.addWidget(self.headless_checkbox, row, 0, 1, 2)
        row += 1

        # ... (rest of the dialog setup: SpinBox, Buttons) ...

        # NOTE: You might need to do the same for QSpinBox if its arrows
        # are also causing SVG errors:
        # self.crawl_depth_spinbox.setStyleSheet("")

        layout.addLayout(grid_layout)
        layout.addStretch(1)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save_settings)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def save_settings(self):
        at_least_one_strategy = False
        selected_strategies = []
        for strategy, checkbox in self.strategy_checkboxes.items():
            setting_key = f"{SETTINGS_STRATEGY_PREFIX}{strategy}"
            is_enabled = checkbox.isChecked()
            self.settings.setValue(setting_key, is_enabled)
            if is_enabled:
                at_least_one_strategy = True
                selected_strategies.append(strategy)

        if not at_least_one_strategy:
            QMessageBox.warning(self, "Settings Error", "Please select at least one scraping strategy.")
            return

        print(f"Saving settings: Strategies={selected_strategies}, Headless={self.headless_checkbox.isChecked()}, Depth={self.crawl_depth_spinbox.value()}")
        self.settings.setValue(SETTINGS_HEADLESS, self.headless_checkbox.isChecked())
        self.settings.setValue(SETTINGS_CRAWL_DEPTH, self.crawl_depth_spinbox.value())
        self.settings.sync() # Ensure settings are written
        self.settingsChanged.emit()
        self.accept()


class DocScraperAppGUI(QMainWindow):
    # Add theme_applier function to __init__
    def __init__(self, theme_applier_func):
        super().__init__()
        QApplication.setOrganizationName(ORG_NAME)
        QApplication.setApplicationName(APP_NAME)
        self.settings = QSettings()
        self.current_file_path = None
        # Store the function passed from main to re-apply themes
        self.theme_applier = theme_applier_func
        # Load the theme *name* from settings, but don't apply it here
        self.current_theme_setting = self.settings.value(SETTINGS_SELECTED_THEME, DEFAULT_THEME)
        self.theme_actions = [] # Initialize here

        # Load window state before initUI if possible
        self.load_window_state()
        self.initUI()
        self.update_recent_files_menu()
        # Set the checkmark on the correct theme menu item based on loaded setting
        self.update_theme_menu_checkstate()
        # Set initial window icon
        self.setWindowIcon(qta.icon('mdi.web-box'))


    def initUI(self):
        self.setWindowTitle(APP_NAME)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- URL Layout ---
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter documentation URL here (e.g., https://docs.python.org)...")
        self.url_input.returnPressed.connect(self.scrape_url_action)
        # *** FIX: Remove color argument ***
        scrape_button = QPushButton(qta.icon('mdi.magnify'), " Scrape")
        scrape_button.setToolTip("Start scraping the entered URL")
        scrape_button.clicked.connect(self.scrape_url_action)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(scrape_button)
        main_layout.addLayout(url_layout)

        self.tab_widget = QTabWidget()
        self.raw_markdown_output = QTextEdit()
        self.raw_markdown_output.setPlaceholderText("Raw scraped Markdown content will appear here...")
        self.raw_markdown_output.setReadOnly(False) # Allow editing if needed
        self.raw_markdown_output.setAcceptRichText(False)
        self.rendered_output = QTextEdit()
        self.rendered_output.setPlaceholderText("Rendered HTML view (if Markdown is scraped successfully).")
        self.rendered_output.setReadOnly(True)
        # Add icons to tabs (optional, but nice)
        self.tab_widget.addTab(self.raw_markdown_output, qta.icon('mdi.code-braces'), "Raw Markdown")
        self.tab_widget.addTab(self.rendered_output, qta.icon('mdi.eye-outline'), "Rendered HTML")
        main_layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        # Add icon to copy button
        self.copy_button = QPushButton(qta.icon('mdi.content-copy'), " Copy Raw Markdown")
        self.copy_button.setToolTip("Copy the raw Markdown text to the clipboard")
        self.copy_button.clicked.connect(self.copy_markdown_action)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.create_menus()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        self.update_title()

    # --- Status/Error Methods ---
    def show_status(self, message: str, timeout: int = 3000):
        self.statusBar.showMessage(message, timeout)
        print(f"INFO: {message}")

    def show_warning(self, message: str):
        self.statusBar.showMessage(f"Warning: {message}", 5000)
        # Use qtawesome icon for message box
        QMessageBox.warning(self, "Warning", message, icon=qta.icon('mdi.alert-outline'))
        print(f"WARNING: {message}")

    def show_error(self, message: str):
         self.statusBar.showMessage(f"Error: {message}", 8000)
         # Use qtawesome icon for message box
         QMessageBox.critical(self, "Error", message, icon=qta.icon('mdi.alert-circle-outline'))
         print(f"ERROR: {message}")

    # --- Menu Creation ---
    def create_menus(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('&File')
        # Add icons to actions using qtawesome
        load_icon = qta.icon('mdi.folder-open-outline')
        load_action = QAction(load_icon, '&Load JSON...', self)
        load_action.setShortcut('Ctrl+O')
        load_action.setStatusTip('Load scraped data from a JSON file')
        load_action.triggered.connect(self.load_file_dialog)
        file_menu.addAction(load_action)

        save_as_icon = qta.icon('mdi.content-save-outline')
        save_as_action = QAction(save_as_icon, 'Save As &JSON...', self)
        save_as_action.setShortcut('Ctrl+S')
        save_as_action.setStatusTip('Save URL and Markdown to a JSON file')
        save_as_action.triggered.connect(self.save_file_dialog)
        file_menu.addAction(save_as_action)

        export_md_icon = qta.icon('mdi.file-export-outline')
        export_md_action = QAction(export_md_icon, '&Export as Markdown (.md)...', self)
        export_md_action.setStatusTip('Export the raw Markdown content to a .md file')
        export_md_action.triggered.connect(self.export_markdown_dialog)
        file_menu.addAction(export_md_action)

        file_menu.addSeparator()
        recent_icon = qta.icon('mdi.history')
        self.recent_files_menu = QMenu('&Recent Files', self) # Create menu FIRST
        self.recent_files_menu.setIcon(recent_icon)         # Set icon SECOND
        file_menu.addMenu(self.recent_files_menu)          # Add the created menu
        file_menu.addSeparator()

        exit_icon = qta.icon('mdi.exit-to-app')
        exit_action = QAction(exit_icon, '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Options Menu
        options_menu = menubar.addMenu('&Options')
        settings_icon = qta.icon('mdi.cogs')
        settings_action = QAction(settings_icon, '&Settings...', self)
        settings_action.setStatusTip('Configure scraping strategies and options')
        settings_action.triggered.connect(self.open_settings_dialog)
        options_menu.addAction(settings_action)

        # View Menu (Themes)
        view_menu = menubar.addMenu('&View')
        theme_icon = qta.icon('mdi.palette-outline')
        theme_menu = view_menu.addMenu("&Theme")             # Create menu FIRST
        theme_menu.setIcon(theme_icon)                      # Set icon SECOND
        available_themes = [
            'dark_blue.xml', 'dark_cyan.xml', 'dark_teal.xml', 'dark_amber.xml', 'dark_red.xml', 'dark_purple.xml', 'dark_lightgreen.xml',
            'light_blue.xml', 'light_cyan.xml', 'light_cyan_500.xml', 'light_teal.xml', 'light_amber.xml', 'light_red.xml', 'light_purple.xml', 'light_lightgreen.xml'
        ] # Added a few more examples
        self.theme_actions.clear() # Ensure it's clear before populating
        for theme_file in sorted(available_themes):
            # Make names more readable
            theme_name = theme_file.replace('.xml', '').replace('_', ' ').replace(' 500', ' (500)').title()
            # Theme switching actions usually don't need individual icons
            action = QAction(theme_name, self, checkable=True)
            # Use functools.partial to pass the theme_file to the handler
            action.triggered.connect(functools.partial(self.change_theme_action, theme_file))
            self.theme_actions.append(action)
            theme_menu.addAction(action)

    # --- Window State Persistence ---
    def load_window_state(self):
        geometry = self.settings.value(SETTINGS_WINDOW_GEOMETRY)
        state = self.settings.value(SETTINGS_WINDOW_STATE)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Set a default size if no geometry is saved
            self.setGeometry(100, 100, 900, 700) # Increased default size
        if state: self.restoreState(state)


    def save_window_state(self):
        self.settings.setValue(SETTINGS_WINDOW_GEOMETRY, self.saveGeometry())
        self.settings.setValue(SETTINGS_WINDOW_STATE, self.saveState())

    # --- Title Update ---
    def update_title(self):
        title = APP_NAME
        if self.current_file_path:
            title += f" - {os.path.basename(self.current_file_path)}"
        self.setWindowTitle(title)

    # --- Theme Handling ---
    # This is called when a theme menu item is clicked
    def change_theme_action(self, theme_file: str):
        if self.theme_applier:
            self.show_status(f"Applying theme: {theme_file}...")
            # Call the global function passed during init
            success = self.theme_applier(QApplication.instance(), theme_file)
            if success:
                self.current_theme_setting = theme_file # Update internal setting tracking
                self.settings.setValue(SETTINGS_SELECTED_THEME, theme_file)
                self.update_theme_menu_checkstate()
                self.show_status(f"Theme '{theme_file}' applied.")
            else:
                # If apply failed, theme_applier handles fallback and messages
                # Refresh menu checks to reflect the actual theme (likely default)
                self.current_theme_setting = g_current_theme_file
                self.update_theme_menu_checkstate()
                self.show_status(f"Failed to apply theme '{theme_file}'. Check logs.", 5000)

    # Updates checkmarks in the theme menu
    def update_theme_menu_checkstate(self):
        global g_current_theme_file # Use the globally applied theme for checking
        current_actual_theme = g_current_theme_file
        for action in self.theme_actions:
            # Extract theme filename from the action's text/logic
            action_theme_name_lower = action.text().lower().replace(' (500)', '_500').replace(' ', '_') + ".xml"
            action.setChecked(action_theme_name_lower == current_actual_theme)


    # --- Settings Dialog ---
    def open_settings_dialog(self):
        # Pass self.settings, which is already initialized
        dialog = SettingsDialog(self.settings, self)
        # Optional: Connect a signal if the main window needs to react *immediately*
        # dialog.settingsChanged.connect(self.on_settings_changed) # Example
        dialog.exec_() # Dialog is modal, execution waits here

    # Example handler if needed
    # def on_settings_changed(self):
    #     self.show_status("Settings updated.", 2000)
    #     # Potentially re-read settings if they affect the main GUI immediately

    # --- Scraping Logic ---
    def scrape_url_action(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_warning("Please enter a URL.")
            return

        # Improved URL validation and fixing
        if not url.startswith(('http://', 'https://')):
            temp_url_https = f"https://{url}"
            temp_url_http = f"http://{url}"
            if is_valid_url_for_gui(temp_url_https):
                url = temp_url_https
                self.url_input.setText(url) # Update input field
                print(f"Assuming HTTPS scheme: {url}")
            elif is_valid_url_for_gui(temp_url_http):
                url = temp_url_http
                self.url_input.setText(url) # Update input field
                print(f"Assuming HTTP scheme: {url}")
            else:
                self.show_warning(f"Invalid or incomplete URL: {self.url_input.text()}")
                return
        elif not is_valid_url_for_gui(url):
             self.show_warning(f"Invalid URL format: {url}")
             return

        # Read settings just before scraping
        active_strategies = [s for s in DEFAULT_STRATEGY_ORDER if self.settings.value(f"{SETTINGS_STRATEGY_PREFIX}{s}", True, type=bool) and s in SUPPORTED_STRATEGIES]
        if not active_strategies:
            self.show_error("No scraping strategies enabled! Go to Options -> Settings.")
            return
        headless_mode = self.settings.value(SETTINGS_HEADLESS, True, type=bool)
        crawl_depth = self.settings.value(SETTINGS_CRAWL_DEPTH, 0, type=int)

        crawl_msg = f", Crawl Depth: {crawl_depth}" if crawl_depth > 0 else ""
        status_msg = f"Scraping {url} (Strategies: {active_strategies}, Headless: {headless_mode}{crawl_msg})..."
        self.show_status(status_msg, 60000) # Long timeout for status
        self.raw_markdown_output.setPlaceholderText(f"Scraping {url}{crawl_msg}...\nPlease wait...")
        self.rendered_output.setPlaceholderText("Waiting for content...")
        self.raw_markdown_output.clear()
        self.rendered_output.clear()
        self.copy_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents() # Ensure UI updates

        markdown_content = None
        html_content = None
        final_status_message = "Scraping finished."
        failed_urls_during_crawl = []
        scraper = None # Define scraper outside try for potential error reporting

        try:
            # Initialize ScrapeMaster with current settings
            scraper = ScrapeMaster(url, strategy=active_strategies, headless=headless_mode)
            results = scraper.scrape_all(
                max_depth=crawl_depth,
                convert_to_markdown=True
            )

            if results:
                markdown_content = results.get('markdown')
                failed_urls_during_crawl = results.get('failed_urls', [])

                if markdown_content:
                    self.raw_markdown_output.setPlainText(markdown_content)
                    self.copy_button.setEnabled(True)
                    visited_count = len(results.get('visited_urls', []))
                    crawl_info = f", {visited_count} page(s) scraped" if crawl_depth > 0 else ""
                    final_status_message = f"Success! (Strategy: {scraper.last_strategy_used or 'N/A'}{crawl_info})"
                    self.raw_markdown_output.setPlaceholderText("Raw scraped Markdown content.")
                    try:
                        # Use common Markdown extensions
                        html_content = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables', 'extra', 'nl2br', 'codehilite'])
                        self.rendered_output.setHtml(html_content)
                        self.rendered_output.setPlaceholderText("Rendered HTML content.")
                    except Exception as e_render:
                        render_error_msg = f"[Render Error: Could not convert Markdown to HTML]\n{e_render}"
                        self.rendered_output.setPlainText(render_error_msg)
                        self.rendered_output.setPlaceholderText("Failed to render Markdown.")
                        print(f"ERROR rendering Markdown: {e_render}")

                else: # No 'markdown' key, but 'results' exist
                    fallback_text = "\n---\n".join(results.get('texts', [])).strip()
                    message = "[INFO] No primary Markdown content was generated by the chosen strategies."
                    if fallback_text:
                         message += " Displaying combined raw text fragments."
                         self.raw_markdown_output.setPlainText(fallback_text)
                         self.copy_button.setEnabled(True) # Allow copying raw text
                    else:
                         message += " No text fragments found either."
                         self.raw_markdown_output.setPlainText(message)
                         self.copy_button.setEnabled(False)
                    final_status_message = message # Update status
                    self.raw_markdown_output.setPlaceholderText(message)
                    self.rendered_output.setPlaceholderText("No Markdown content to render.")

            else: # scraper.scrape_all() returned None or empty dict
                error_message = (scraper.get_last_error() if scraper else "Scraper not initialized") or "Unknown scraping error occurred."
                self.raw_markdown_output.setPlainText(f"Scraping Error:\n{error_message}")
                final_status_message = f"Scraping failed. See Raw tab for details."
                self.raw_markdown_output.setPlaceholderText("Scraping failed. See error message above.")
                self.rendered_output.setPlaceholderText("Scraping failed.")
                # Only show popup for critical setup/strategy errors
                if scraper and ("All scraping strategies failed" in error_message or "Could not initialize" in error_message):
                     self.show_error(error_message)

        except Exception as e:
            # Catch broader exceptions during scraping process
            error_details = traceback.format_exc()
            error_msg = f"Critical Application Error during scraping:\n{e}\n\nDetails:\n{error_details}"
            self.raw_markdown_output.setPlainText(error_msg)
            self.rendered_output.setPlainText(f"[App Error during scrape: {e}]")
            final_status_message = "A critical error occurred during scraping."
            self.raw_markdown_output.setPlaceholderText("Critical error.")
            self.rendered_output.setPlaceholderText("Critical error.")
            self.show_error(f"An unexpected error occurred during scraping:\n{e}") # Show popup

        finally:
             QApplication.restoreOverrideCursor() # Always restore cursor

        # Report failed URLs after cursor is restored and status is set
        if failed_urls_during_crawl:
            failed_list_str = "\n - ".join(failed_urls_during_crawl)
            print(f"WARNING: Failed to scrape the following URLs during crawl:\n - {failed_list_str}")
            # Show non-modal warning in status bar, avoid popup unless critical
            self.show_status(f"Warning: Failed to scrape {len(failed_urls_during_crawl)} URLs during crawl. Check console.", 6000)

        # Show the final status message determined in try/except block
        self.show_status(final_status_message, 5000)
        # Reset file path after scrape, as content is new
        self.current_file_path = None
        self.update_title()

    # --- Clipboard Action ---
    def copy_markdown_action(self):
        clipboard = QApplication.clipboard()
        raw_markdown_text = self.raw_markdown_output.toPlainText()
        if raw_markdown_text:
            clipboard.setText(raw_markdown_text)
            self.show_status("Raw Markdown copied to clipboard!", 2000)
        else:
            self.show_warning("Nothing to copy.")

    # --- File Operations ---
    def get_safe_filename_base(self, url: str) -> str:
        """Generates a safe filename base from a URL."""
        try:
            parsed_url = urlparse(url)
            safe_domain = parsed_url.netloc.replace('.', '_')
            # Handle path: remove leading/trailing slashes, replace others
            safe_path = parsed_url.path.strip('/').replace('/', '_')
            if not safe_path: safe_path = 'index'
            # Combine and sanitize
            base_name = f"{safe_domain}_{safe_path}"
            safe_base = "".join(c for c in base_name if c.isalnum() or c in ('_', '-')).rstrip('_').lower()
            return safe_base[:100] # Limit length
        except Exception:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            return f"scraped_data_{timestamp}"


    def save_file_dialog(self):
        url = self.url_input.text()
        raw_markdown = self.raw_markdown_output.toPlainText()
        if not url or not raw_markdown or not raw_markdown.strip() or raw_markdown.startswith("Error:") or raw_markdown.startswith("[INFO]"):
            self.show_warning("Need valid URL and scraped content to save.")
            return

        suggested_name = self.get_safe_filename_base(url) + ".json"
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Uncomment for testing non-native dialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Scraped Data (JSON)", suggested_name, "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            # Ensure .json extension
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            self.save_file(file_path)

    def save_file(self, file_path):
        data = {
            "url": self.url_input.text(),
            "markdown": self.raw_markdown_output.toPlainText(),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S %Z") # Add timestamp
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.current_file_path = file_path
            self.add_recent_file(file_path)
            self.update_title()
            self.show_status(f"Data saved to {os.path.basename(file_path)}", 3000)
        except IOError as e:
             self.show_error(f"Could not save JSON file (IO Error):\n{e}")
             self.show_status("Save failed.", 3000)
        except Exception as e:
            self.show_error(f"An unexpected error occurred during save:\n{e}")
            self.show_status("Save failed.", 3000)


    def export_markdown_dialog(self):
        raw_markdown = self.raw_markdown_output.toPlainText()
        url = self.url_input.text()

        if not raw_markdown or not raw_markdown.strip() or raw_markdown.startswith("Error:") or raw_markdown.startswith("[INFO]"):
            self.show_warning("No valid Markdown content available to export.")
            return

        suggested_name = self.get_safe_filename_base(url) + ".md"
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Raw Markdown",
            suggested_name,
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)",
            options=options
        )

        if file_path:
            # Ensure appropriate extension if not provided
            if not Path(file_path).suffix:
                 file_path += '.md'

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(raw_markdown)
                self.show_status(f"Markdown exported to {os.path.basename(file_path)}", 3000)
            except IOError as e:
                self.show_error(f"Could not export Markdown file (IO Error):\n{e}")
                self.show_status("Export failed.", 3000)
            except Exception as e:
                 self.show_error(f"An unexpected error occurred during export:\n{e}")
                 self.show_status("Export failed.", 3000)


    def load_file_dialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Scraped Data (JSON)", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            print(f"Attempting to load file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic validation
            if not isinstance(data, dict): raise ValueError("JSON content is not a dictionary.")
            if "url" not in data or "markdown" not in data:
                raise ValueError("JSON file missing 'url' or 'markdown' key.")

            loaded_url = data.get("url", "")
            loaded_markdown = data.get("markdown", "")

            self.url_input.setText(loaded_url)
            self.raw_markdown_output.setPlainText(loaded_markdown)

            # Attempt to render loaded markdown
            is_valid_content = bool(loaded_markdown and loaded_markdown.strip())
            if is_valid_content:
                try:
                    html_content = markdown.markdown(loaded_markdown, extensions=['fenced_code', 'tables', 'extra', 'nl2br', 'codehilite'])
                    self.rendered_output.setHtml(html_content)
                    self.rendered_output.setPlaceholderText("Rendered HTML from loaded file.")
                except Exception as e_render:
                    render_error_msg = f"[Render Error: Could not convert loaded Markdown to HTML]\n{e_render}"
                    self.rendered_output.setPlainText(render_error_msg)
                    self.rendered_output.setPlaceholderText("Failed to render loaded Markdown.")
                    print(f"ERROR rendering loaded Markdown: {e_render}")
                self.copy_button.setEnabled(True)
            else: # Empty or invalid markdown content
                self.rendered_output.clear()
                self.rendered_output.setPlaceholderText("Loaded file contains no Markdown content or only errors.")
                self.copy_button.setEnabled(False)

            self.current_file_path = file_path
            self.add_recent_file(file_path)
            self.update_title()
            self.show_status(f"Loaded {os.path.basename(file_path)}", 3000)

        except FileNotFoundError:
            self.show_error(f"File not found:\n{file_path}")
            self.remove_recent_file(file_path) # Remove from recent if not found
            self.show_status("Load failed: File not found.", 3000)
        except json.JSONDecodeError as e:
            self.show_error(f"Could not decode JSON file (invalid JSON):\n{file_path}\nError: {e}")
            self.show_status("Load failed: Invalid JSON.", 3000)
        except ValueError as e: # Catch our custom validation error
            self.show_error(f"Invalid file format: {e}\nFile: {file_path}")
            self.show_status("Load failed: Invalid format.", 3000)
        except IOError as e:
             self.show_error(f"Could not read file (IO Error):\n{file_path}\nError: {e}")
             self.show_status("Load failed: IO Error.", 3000)
        except Exception as e:
            # Catch any other unexpected errors during load
            self.show_error(f"An unexpected error occurred during load:\n{e}\nFile: {file_path}")
            traceback.print_exc() # Print full traceback for debugging
            self.show_status("Load failed.", 3000)

    # --- Recent Files Handling ---
    def get_recent_files(self) -> list[str]:
        # Ensure it always returns a list, even if setting is corrupt/missing
        return self.settings.value(SETTINGS_RECENT_FILES, [], type=list) or []

    def set_recent_files(self, files: list[str]):
        self.settings.setValue(SETTINGS_RECENT_FILES, files)

    def add_recent_file(self, file_path: str):
        if not file_path or not isinstance(file_path, str): return
        recent_files = self.get_recent_files()
        # Remove existing entry if present (case-insensitive on Windows)
        file_path_norm = os.path.normpath(file_path)
        recent_files = [f for f in recent_files if os.path.normpath(f) != file_path_norm]
        # Insert at the beginning
        recent_files.insert(0, file_path)
        # Trim to max size
        del recent_files[MAX_RECENT_FILES:]
        self.set_recent_files(recent_files)
        self.update_recent_files_menu()

    def remove_recent_file(self, file_path: str):
        if not file_path or not isinstance(file_path, str): return
        recent_files = self.get_recent_files()
        file_path_norm = os.path.normpath(file_path)
        initial_len = len(recent_files)
        recent_files = [f for f in recent_files if os.path.normpath(f) != file_path_norm]
        if len(recent_files) < initial_len:
            self.set_recent_files(recent_files)
            self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_files_menu.clear()
        recent_files = self.get_recent_files()
        actions = []
        # Use QFontMetrics for eliding long paths nicely
        fm = self.fontMetrics()
        menu_width = self.recent_files_menu.width() - 40 # Approx width available for text

        for i, file_path in enumerate(recent_files):
            if not file_path or not isinstance(file_path, str): continue
            # Create a nice display name (e.g., elided path)
            display_name = fm.elidedText(file_path, Qt.ElideMiddle, menu_width)
            action = QAction(f"&{i+1} {display_name}", self)
            action.setData(file_path) # Store full path in data
            action.triggered.connect(self.open_recent_file)
            action.setToolTip(file_path) # Tooltip shows full path
            actions.append(action)

        if actions:
            self.recent_files_menu.addActions(actions)
            self.recent_files_menu.setEnabled(True)
        else:
            no_recent_action = QAction("(No Recent Files)", self)
            no_recent_action.setEnabled(False)
            self.recent_files_menu.addAction(no_recent_action)
            self.recent_files_menu.setEnabled(False)

    def open_recent_file(self):
        action = self.sender()
        if action and isinstance(action, QAction) and action.data():
            file_path = action.data()
            if isinstance(file_path, str) and os.path.exists(file_path):
                 self.load_file(file_path)
            elif isinstance(file_path, str): # File doesn't exist
                self.show_warning(f"Recent file not found: {os.path.basename(file_path)}\n'{file_path}'\nRemoving from list.")
                self.remove_recent_file(file_path)
            else:
                 print(f"Warning: Invalid data in recent file action: {action.data()}")


    # --- Close Event ---
    def closeEvent(self, event):
        # Save window state *before* settings sync
        self.save_window_state()
        # Ensure the *last selected* theme is saved, even if application failed to apply it
        self.settings.setValue(SETTINGS_SELECTED_THEME, self.current_theme_setting)
        # Other settings are saved by the SettingsDialog or implicitly
        self.settings.sync() # Explicitly write settings to storage
        self.show_status("Settings saved. Exiting...", 1000)
        print("Application closing.")
        event.accept()


# --- Main Execution Block ---
if __name__ == '__main__':
    # Set high DPI scaling attribute before creating QApplication
    # Adjust based on your Qt version if necessary
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # --- Apply Theme EARLY ---
    # Load theme setting *before* creating the window
    settings = QSettings(ORG_NAME, APP_NAME) # Use org/app name for consistency
    initial_theme = settings.value(SETTINGS_SELECTED_THEME, DEFAULT_THEME)
    # Ensure QFontDatabase is available before applying theme
    try:
        # This doesn't do much here, but confirms the import worked
        _ = QFontDatabase()
    except NameError:
        print("CRITICAL: QFontDatabase still not defined before theme application!")
        # Optionally show a basic message box if QApplication exists
        try:
            QMessageBox.critical(None, "Startup Error", "QFontDatabase is not available. Cannot apply theme or load icons.")
        except: pass
        sys.exit(1)
    apply_theme_globally(app, initial_theme) # Apply the theme globally

    try:
        # Pass the global theme applying function to the main window instance
        mainWin = DocScraperAppGUI(theme_applier_func=apply_theme_globally)
        mainWin.show()
        sys.exit(app.exec_())
    except Exception as e:
        # Catch-all for critical errors during initialization or runtime
        print("\n--- Unhandled Exception during Application Execution ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        # Try to show a simple Qt message box as a last resort
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Application Crash")
            # Keep message concise, details are in console
            msgBox.setText(f"An unexpected critical error occurred:\n\n{type(e).__name__}: {e}\n\nPlease check the console output for detailed traceback.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
        except Exception as e_msgbox:
            # If even the message box fails, print that error
            print(f"\n--- Error Showing Crash Message Box ---")
            print(f"Message Box Error: {e_msgbox}")
            print(traceback.format_exc())
        sys.exit(1) # Exit with error code