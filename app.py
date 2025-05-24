import json
import os
import sys
import threading
import concurrent.futures

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QStatusBar,
)

from src.retrieve_pdf import extract_qa_pairs_from_pdf as extract_qa_pairs, save_to_txt
from src.theme import ModernTheme
from src.worker import PreviewWorker
from src.ui_components import UIComponents, resource_path

try:
    from version_converter import __version__
except ImportError:
    __version__ = "0.0.0-dev"


# These classes are now imported from src modules


class QuizletConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None  # Track the current PreviewWorker
        self.setup_window()
        self.setup_layout()
        self.create_ui()
        self.setup_statusbar()
        self.apply_stylesheets()
        self.show()

    def setup_window(self):
        """Setup window properties and icon."""
        self.setWindowTitle("Quizlet Converter")
        self.setGeometry(200, 100, 700, 800)
        self.setMinimumSize(600, 700)
        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"Icon file not found at {icon_path}")
        except Exception as e:
            print(f"Could not set icon: {e}")

    def setup_layout(self):
        """Setup central widget and main layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

    # --- UI Creation ---
    def create_ui(self):
        """Create all UI components using the UIComponents class."""
        UIComponents.create_menu_bar(self)
        UIComponents.create_input_section(self)
        UIComponents.create_format_options(self)
        UIComponents.create_separator_section(self)
        UIComponents.create_cleaning_section(self)
        UIComponents.create_preview_section(self)
        UIComponents.create_action_buttons(self)

    def setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(
            "Ready | Ctrl+O: Open | Ctrl+S: Save | Ctrl+P: Preview"
        )

    def apply_stylesheets(self):
        """Apply the modern theme stylesheet."""
        self.setStyleSheet(ModernTheme.get_stylesheet())

    # Event handlers and utility methods remain the same
    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "PDF files (*.pdf);;All files (*)"
        )
        if filename:
            self.file_path_input.setText(filename)

    def on_input_change(self, text: str):
        if os.path.isfile(text):
            self.statusBar.showMessage(f"File loaded: {text}")
            if not text.lower().endswith(".pdf"):
                self.statusBar.showMessage("Selected file is not a PDF file")
        else:
            self.statusBar.showMessage("Invalid file. Please select a valid file.")

    def toggle_separator_options(self):
        """Toggle the visibility of separator options based on format selection."""
        pass

    def on_separator_changed(self, text: str):
        """Handle changes to the separator selection."""
        pass

    def get_separators(self):
        """Get the selected separator for Q&A pairs and the newline separator for cards."""
        qa_sep = self.qa_separator_combo.currentText()
        
        # For simplicity, always use newline as card separator
        card_sep = "\n"
        
        return qa_sep, card_sep

    def preview(self):
        file_path = self.file_path_input.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.critical(self, "Error", "Please select a valid input file")
            return
        # --- Prevent multiple workers running at the same time ---
        if hasattr(self, "worker") and self.worker is not None:
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
            self.worker = None
        # Disable preview button and show busy cursor to prevent spamming
        self.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # ---------------------------------------------------------
        self.loading_label.setText("Loading...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        words_to_remove = [
            word.strip()
            for word in self.words_to_remove_input.text().split(",")
            if word.strip()
        ]
        chars_to_remove = self.chars_to_remove_input.text()
        format_type = "json" if self.format_json_radio.isChecked() else "txt"
        qa_sep, card_sep = "", ""
        if format_type == "txt":
            qa_sep, card_sep = self.get_separators()
        self.worker = PreviewWorker(
            file_path, words_to_remove, chars_to_remove, format_type, qa_sep, card_sep
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_preview_completed)
        self.worker.error.connect(self.on_preview_error)
        self.worker.finished.connect(self.cleanup_worker)
        self.worker.error.connect(self.cleanup_worker)
        self.worker.start()

    def cleanup_worker(self, *args, **kwargs):
        """Ensure worker is cleaned up after finishing/error."""
        if hasattr(self, "worker") and self.worker is not None:
            self.worker.quit()
            self.worker.wait()
            self.worker = None
        # Re-enable UI and restore cursor
        self.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    def on_preview_completed(self, qa_pairs, preview_content):
        self.preview_text.setText(preview_content)
        if qa_pairs:
            self.loading_label.setText(f"Found {len(qa_pairs)} question-answer pairs")
            self.statusBar.showMessage(
                f"Preview successful - {len(qa_pairs)} question-answer pairs found"
            )
        else:
            self.loading_label.setText("No questions found")
            self.statusBar.showMessage("No questions found in the file")
        self.progress_bar.setVisible(False)

    def on_preview_error(self, error_message: str):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.loading_label.setText("")
        self.statusBar.showMessage(f"Error: {error_message}")
        self.progress_bar.setVisible(False)

    def save(self):
        file_path = self.file_path_input.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.critical(self, "Error", "Please select an input file first.")
            return
        if not self.preview_text.toPlainText().strip():
            QMessageBox.warning(
                self, "Warning", "Preview is empty. Please generate a preview first."
            )
            return

        words_to_remove = [
            word.strip()
            for word in self.words_to_remove_input.text().split(",")
            if word.strip()
        ]
        chars_to_remove = self.chars_to_remove_input.text()

        # Use CPU count - 1 for worker threads to leave one core free for the UI
        max_workers = max(1, os.cpu_count() - 1) if os.cpu_count() else 2
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            self.statusBar.showMessage("Processing...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(25)

            # Submit extraction task
            future = executor.submit(
                extract_qa_pairs,
                file_path,
                words_to_remove=words_to_remove,
                chars_to_remove=chars_to_remove,
            )

            # Use a more efficient progress update mechanism
            update_interval = 200  # ms
            self.save_timer = QTimer()
            self.save_timer.timeout.connect(
                lambda: self.progress_bar.setValue(
                    min(
                        95, self.progress_bar.value() + 2
                    )  # Slower increment for smoother progress
                )
            )
            self.save_timer.start(update_interval)

            try:
                qa_pairs = future.result()
                self.save_timer.stop()
                self.progress_bar.setValue(95)

                if not qa_pairs:
                    QMessageBox.information(self, "Info", "No questions found")
                    self.progress_bar.setVisible(False)
                    self.statusBar.showMessage("No questions found, save cancelled.")
                    return

                is_json = self.format_json_radio.isChecked()
                default_ext = ".json" if is_json else ".txt"
                output_file, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Output",
                    "",
                    f"{'JSON' if is_json else 'Text'} Files (*{default_ext});;All Files (*)",
                )

                if not output_file:
                    self.progress_bar.setVisible(False)
                    self.statusBar.showMessage("Save cancelled by user.")
                    return

                self.progress_bar.setValue(100)
                qa_sep, card_sep = self.get_separators()

                # Use a more efficient save mechanism
                def save_and_notify_task():
                    try:
                        # Process in chunks for better memory management
                        if is_json:
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
                        else:
                            save_to_txt(qa_pairs, output_file, qa_sep, card_sep)
                        QTimer.singleShot(
                            0, lambda: self.show_save_success(output_file)
                        )
                    except Exception as e:
                        error_message = str(e)
                        QTimer.singleShot(
                            0, lambda: self.show_save_error(error_message)
                        )

                save_thread = threading.Thread(target=save_and_notify_task, daemon=True)
                save_thread.start()

            except Exception as e_extract:
                self.save_timer.stop()
                self.progress_bar.setVisible(False)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred during data extraction: {str(e_extract)}",
                )
                self.statusBar.showMessage(f"Error during extraction: {str(e_extract)}")

    def show_save_success(self, output_file: str):
        QMessageBox.information(self, "Success", f"File saved: {output_file}")
        self.statusBar.showMessage(f"File saved: {output_file}")
        self.progress_bar.setVisible(False)

    def show_save_error(self, error_message: str):
        QMessageBox.critical(self, "Error", f"Failed to save file: {error_message}")
        self.statusBar.showMessage(f"Failed to save file: {error_message}")
        self.progress_bar.setVisible(False)

    def copy_to_clipboard(self):
        text = self.preview_text.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self.statusBar.showMessage("Copied to clipboard!")
        else:
            self.statusBar.showMessage("Nothing to copy - preview is empty")

    def clear_all(self):
        self.file_path_input.clear()
        self.preview_text.clear()
        self.loading_label.setText("")
        self.progress_bar.setVisible(False)
        self.statusBar.showMessage("All cleared!")

    def show_help(self):
        help_text = """
Quizlet Converter Help

1. Load PDF: Click 'Browse' or drag-drop a PDF file
2. Choose Format: Select TXT or JSON output format
3. For TXT format, customize separators
4. Click 'Preview' to see how the output will look
5. Click 'Save' to save the output to a file

Keyboard Shortcuts:
- Ctrl+O: Open file
- Ctrl+S: Save output
- Ctrl+P: Preview
- F1: Show this help
        """
        QMessageBox.information(self, "Help", help_text)

    def show_about(self):
        about_text = f"""
Quizlet Converter

A simple tool to convert PDF files to 
structured text or JSON files for flashcard studies.

Version: {__version__}
        """
        QMessageBox.information(self, "About", about_text)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    window = QuizletConverterApp()
    # Keep reference to window to prevent garbage collection
    app.window = window
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
