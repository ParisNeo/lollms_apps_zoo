import sys
import os
import pipmaster as pm
pm.ensure_packages(["pyqt5","patch"])
import patch # The library for applying patches
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QCheckBox, QMessageBox, QStatusBar,
    QMainWindow
)
from PyQt5.QtCore import Qt

class PatchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.original_file_path = ""
        self.patch_file_path = ""
        self.output_file_path = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Patcher')
        self.setGeometry(300, 300, 550, 250) # x, y, width, height

        # Central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- File Selection ---
        # Original File
        hbox_orig = QHBoxLayout()
        self.lbl_orig = QLabel('Original File:')
        self.txt_orig = QLineEdit(self)
        self.txt_orig.setReadOnly(True)
        self.btn_browse_orig = QPushButton('Browse...', self)
        self.btn_browse_orig.clicked.connect(self.select_original_file)
        hbox_orig.addWidget(self.lbl_orig)
        hbox_orig.addWidget(self.txt_orig)
        hbox_orig.addWidget(self.btn_browse_orig)
        main_layout.addLayout(hbox_orig)

        # Patch File
        hbox_patch = QHBoxLayout()
        self.lbl_patch = QLabel('Patch File (.diff):')
        self.txt_patch = QLineEdit(self)
        self.txt_patch.setReadOnly(True)
        self.btn_browse_patch = QPushButton('Browse...', self)
        self.btn_browse_patch.clicked.connect(self.select_patch_file)
        hbox_patch.addWidget(self.lbl_patch)
        hbox_patch.addWidget(self.txt_patch)
        hbox_patch.addWidget(self.btn_browse_patch)
        main_layout.addLayout(hbox_patch)

        # --- Output Options ---
        self.chk_save_as = QCheckBox('Save result to a new file', self)
        self.chk_save_as.stateChanged.connect(self.toggle_output_selection)
        main_layout.addWidget(self.chk_save_as)

        # Output File (initially hidden/disabled)
        self.hbox_output = QHBoxLayout()
        self.lbl_output = QLabel('Output File:')
        self.txt_output = QLineEdit(self)
        self.txt_output.setReadOnly(True)
        self.btn_browse_output = QPushButton('Browse...', self)
        self.btn_browse_output.clicked.connect(self.select_output_file)
        self.hbox_output.addWidget(self.lbl_output)
        self.hbox_output.addWidget(self.txt_output)
        self.hbox_output.addWidget(self.btn_browse_output)
        main_layout.addLayout(self.hbox_output)

        # --- Action Button ---
        self.btn_apply = QPushButton('Apply Patch', self)
        self.btn_apply.clicked.connect(self.run_patch_process)
        self.btn_apply.setEnabled(False) # Disabled until files are selected
        main_layout.addWidget(self.btn_apply, alignment=Qt.AlignCenter)

        # --- Status Bar ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Ready. Select files.')

        # Initial state for output widgets
        self.toggle_output_selection(Qt.Unchecked) # Call manually to set initial state


    def select_original_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Original File", "", "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            self.original_file_path = fileName
            self.txt_orig.setText(fileName)
            self.update_apply_button_state()
            self.statusBar.showMessage(f"Original file selected: {os.path.basename(fileName)}")

    def select_patch_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Patch File", "", "Patch Files (*.diff *.patch);;All Files (*)", options=options)
        if fileName:
            self.patch_file_path = fileName
            self.txt_patch.setText(fileName)
            self.update_apply_button_state()
            self.statusBar.showMessage(f"Patch file selected: {os.path.basename(fileName)}")

    def select_output_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # Suggest a default name based on original file
        default_name = ""
        if self.original_file_path:
            base, ext = os.path.splitext(os.path.basename(self.original_file_path))
            default_name = os.path.join(os.path.dirname(self.original_file_path), f"{base}_patched{ext}")

        fileName, _ = QFileDialog.getSaveFileName(self, "Save Patched File As...", default_name, "All Files (*)", options=options)
        if fileName:
            self.output_file_path = fileName
            self.txt_output.setText(fileName)
            self.update_apply_button_state()
            self.statusBar.showMessage(f"Output file set: {os.path.basename(fileName)}")


    def toggle_output_selection(self, state):
        enable = (state == Qt.Checked)
        self.lbl_output.setEnabled(enable)
        self.txt_output.setEnabled(enable)
        self.btn_browse_output.setEnabled(enable)
        if not enable:
            self.txt_output.clear()
            self.output_file_path = ""
        self.update_apply_button_state() # Re-check if Apply should be enabled

    def update_apply_button_state(self):
        """Enable Apply button only if required files are selected."""
        orig_ok = bool(self.original_file_path and os.path.exists(self.original_file_path))
        patch_ok = bool(self.patch_file_path and os.path.exists(self.patch_file_path))
        output_ok = (not self.chk_save_as.isChecked()) or (self.chk_save_as.isChecked() and bool(self.output_file_path))

        self.btn_apply.setEnabled(orig_ok and patch_ok and output_ok)

    def run_patch_process(self):
        """Handles the logic of calling the patch function."""
        if not self.original_file_path or not self.patch_file_path:
            QMessageBox.warning(self, "Missing Files", "Please select both an original file and a patch file.")
            return

        save_as_new = self.chk_save_as.isChecked()
        output_target = self.output_file_path if save_as_new else None

        if save_as_new and not output_target:
             QMessageBox.warning(self, "Missing Output Path", "Please specify an output file path when 'Save as new file' is checked.")
             return

        if not save_as_new:
            reply = QMessageBox.question(self, 'Confirm In-Place Patch',
                                         f"Are you sure you want to modify '{os.path.basename(self.original_file_path)}' directly?\nThis cannot be undone easily.",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.statusBar.showMessage("Patching cancelled by user.")
                return

        self.statusBar.showMessage("Applying patch...")
        QApplication.processEvents() # Update UI

        success, message = self.apply_patch_file(
            patch_filepath=self.patch_file_path,
            original_filepath=self.original_file_path,
            output_filepath=output_target
        )

        if success:
            self.statusBar.showMessage(f"Success: {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.statusBar.showMessage(f"Error: {message}")
            QMessageBox.critical(self, "Patch Error", message)

        # Optionally clear fields after operation, or leave them
        # self.txt_orig.clear(); self.original_file_path = ""
        # self.txt_patch.clear(); self.patch_file_path = ""
        # self.txt_output.clear(); self.output_file_path = ""
        # self.update_apply_button_state()


    def apply_patch_file(self, patch_filepath, original_filepath, output_filepath=None):
        """
        Applies a unified diff patch to an original file.

        Args:
            patch_filepath (str): Path to the .diff or .patch file.
            original_filepath (str): Path to the file to be patched.
            output_filepath (str, optional): Path to save the patched file.
                                            If None, modifies the original file in place.
                                            Defaults to None.

        Returns:
            tuple[bool, str]: (True if successful, status message) or (False, error message)
        """
        try:
            # Load the patch set from the patch file
            # Use encoding='utf-8' for robustness
            patch_set = patch.fromfile(patch_filepath)
            if not patch_set:
                return False, f"Could not parse patch file: {patch_filepath}"

            original_dir = os.path.dirname(os.path.abspath(original_filepath))
            original_basename = os.path.basename(original_filepath)

            # --- Option 1: Modify original file in-place ---
            if output_filepath is None:
                if patch_set.apply(root=original_dir):
                    return True, f"Patch applied successfully in-place to {original_basename}."
                else:
                    # Try to find specific reason (optional, adds complexity)
                     # patch_set.write_hunks(...) # Could write rejected hunks
                    return False, "Patch application failed. Hunks might not match the original file content."

            # --- Option 2: Write to a new output file ---
            else:
                 # Read original content (binary mode for safety)
                try:
                    with open(original_filepath, 'rb') as f_orig:
                        original_content = f_orig.read()
                except Exception as e:
                     return False, f"Error reading original file: {e}"

                # Find the patch item corresponding to the original file's basename
                patch_item = None
                # Need to decode patch paths for comparison if needed, handle potential encoding issues
                try:
                    decoded_basename = original_basename.encode('utf-8') # Assuming patch uses utf-8 names
                except UnicodeDecodeError:
                    # Fallback or handle non-UTF8 filenames if necessary
                    decoded_basename = original_basename.encode(sys.getfilesystemencoding(), errors='replace')

                for item in patch_set.items:
                    # Compare target/source path bytes directly or decode carefully
                    target_path_bytes = item.target.strip(b'/')
                    source_path_bytes = item.source.strip(b'/')

                    if target_path_bytes == decoded_basename or source_path_bytes == decoded_basename:
                         patch_item = item
                         break
                     # Try decoding if direct byte comparison fails (less reliable)
                    try:
                         if target_path_bytes.decode('utf-8') == original_basename or \
                            source_path_bytes.decode('utf-8') == original_basename:
                             patch_item = item
                             break
                    except UnicodeDecodeError:
                         continue # Skip item if path decoding fails


                if not patch_item:
                    return False, f"Could not find patch instructions for '{original_basename}' within '{os.path.basename(patch_filepath)}'"

                # Apply the patch to the in-memory content (split lines)
                # Decode original content carefully for text patches, keepends=True is important
                try:
                    # Try UTF-8 first, fallback to system default or latin-1
                    try:
                         original_lines_text = original_content.decode('utf-8').splitlines(keepends=True)
                    except UnicodeDecodeError:
                         original_lines_text = original_content.decode(sys.getdefaultencoding(), errors='replace').splitlines(keepends=True)

                    # The python-patch library expects text lines for apply()
                    patched_lines_text = patch_item.apply(original_lines_text)

                except Exception as e:
                     return False, f"Error preparing content for patching: {e}"


                if patched_lines_text is None or patched_lines_text is False: # Check both based on library behavior
                    return False, "Patch application failed for generating output file (hunks might not match)."

                # Join lines and encode back to bytes (use UTF-8 for consistency)
                patched_content_bytes = "".join(patched_lines_text).encode('utf-8')

                # Write the patched content to the new file
                try:
                    output_dir = os.path.dirname(os.path.abspath(output_filepath))
                    if output_dir:
                         os.makedirs(output_dir, exist_ok=True)
                    with open(output_filepath, 'wb') as f_out: # Write in binary mode
                        f_out.write(patched_content_bytes)
                    return True, f"Patched content successfully saved to '{os.path.basename(output_filepath)}'."
                except Exception as e:
                    return False, f"Error writing output file: {e}"

        except Exception as e:
            # Catch unexpected errors during patch loading/applying
            import traceback
            print(f"An unexpected error occurred:\n{traceback.format_exc()}") # Log detailed error to console
            return False, f"An unexpected error occurred: {e}"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PatchApp()
    ex.show()
    sys.exit(app.exec_())