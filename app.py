import json
import os
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QRadioButton,
    QComboBox,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QStatusBar,
    QAction,
)
import threading
import concurrent.futures
from functools import partial
from retrieve import extract_qa_pairs, save_to_txt, save_to_json, format_qa_pairs

# Import version information
try:
    from quizlet_converter_version import __version__
except ImportError:
    __version__ = "0.0.0-dev"


class ModernTheme:
    # Light theme colors only
    BG_COLOR = "#f5f5f5"
    FG_COLOR = "#333333"
    ACCENT_COLOR = "#0064e7"
    ACCENT_DARK = "#1d418f"
    FRAME_BG = "#ffffff"
    ENTRY_BG = "#ffffff"
    ENTRY_FG = "#333333"
    BORDER_COLOR = "#cccccc"
    HIGHLIGHT_COLOR = ACCENT_COLOR
    BUTTON_BG = ACCENT_COLOR
    BUTTON_FG = "#ffffff"
    SUCCESS_COLOR = "#4caf50"
    WARNING_COLOR = "#ff9800"
    ERROR_COLOR = "#f44336"
    # Button properties
    BUTTON_RADIUS = 15  # Pixel radius for rounded buttons


class PreviewWorker(QThread):
    """Worker thread for processing HTML files and generating preview content"""

    finished = pyqtSignal(list, str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(
        self,
        file_path,
        words_to_remove,
        chars_to_remove,
        format_type,
        qa_sep="",
        card_sep="",
    ):
        super().__init__()
        self.file_path = file_path
        self.words_to_remove = words_to_remove
        self.chars_to_remove = chars_to_remove
        self.format_type = format_type
        self.qa_sep = qa_sep
        self.card_sep = card_sep
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def run(self):
        try:
            # Progress: 0%
            self.progress.emit(0)

            # Extract data using executor to better handle CPU-bound tasks
            future = self.executor.submit(
                extract_qa_pairs,
                self.file_path,
                words_to_remove=self.words_to_remove,
                chars_to_remove=self.chars_to_remove,
            )

            # Show intermediate progress (this is a bit artificial but helps UX)
            for i in range(1, 5):
                QThread.msleep(100)  # Sleep for 100ms
                self.progress.emit(i * 10)  # Update progress from 10% to 40%

            # Wait for the result
            qa_pairs = future.result()

            # Progress: 50%
            self.progress.emit(50)

            if not qa_pairs:
                self.finished.emit([], "No questions found in this file")
                return

            # Format data - also execute in the thread pool for better performance
            if self.format_type == "json":
                format_future = self.executor.submit(
                    json.dumps, qa_pairs, ensure_ascii=False, indent=2
                )
            else:
                format_future = self.executor.submit(
                    format_qa_pairs, qa_pairs, self.qa_sep, self.card_sep
                )

            # Show intermediate progress
            for i in range(6, 9):
                QThread.msleep(100)  # Sleep for 100ms
                self.progress.emit(i * 10)  # Update progress from 60% to 80%

            # Get the formatted content
            preview_content = format_future.result()

            # Progress: 100%
            self.progress.emit(100)

            # Send result
            self.finished.emit(qa_pairs, preview_content)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Always shut down the executor
            self.executor.shutdown(wait=False)


class QuizletConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Setup window properties
        self.setWindowTitle("Quizlet Converter")
        self.setGeometry(100, 100, 900, 900)
        self.setMinimumSize(900, 900)

        # Set application icon
        try:
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico"
            )
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"Icon file not found at {icon_path}")
        except Exception as e:
            print(f"Could not set icon: {e}")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Setup UI elements
        self.create_ui()

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(
            "Ready | Ctrl+O: Open | Ctrl+S: Save | Ctrl+P: Preview"
        )

        # Setup stylesheets
        self.apply_stylesheets()

        # Show the app
        self.show()

    def create_ui(self):
        """Create all UI elements"""
        # Create menus
        self.create_menus()

        # Input section
        self.create_input_section()

        # Format options
        self.create_format_options()

        # Separator options
        self.create_separator_section()

        # Cleaning options
        self.create_cleaning_section()

        # Preview section
        self.create_preview_section()

        # Bottom action buttons
        self.create_action_buttons()

    def create_menus(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open HTML File", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Output", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")

        copy_action = QAction("&Copy to Clipboard", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        clear_action = QAction("C&lear All", self)
        clear_action.triggered.connect(self.clear_all)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        preview_action = QAction("&Preview", self)
        preview_action.setShortcut("Ctrl+P")
        preview_action.triggered.connect(self.preview)
        view_menu.addAction(preview_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        help_action = QAction("&Help", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_input_section(self):
        """Create the input file selection section"""
        # Label
        input_label = QLabel("Quizlet HTML File (Select or Drag & Drop)")
        input_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.main_layout.addWidget(input_label)

        # Input layout with text field and browse button
        input_layout = QHBoxLayout()

        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select an HTML file...")
        self.file_path_input.textChanged.connect(self.on_input_change)
        input_layout.addWidget(self.file_path_input)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        browse_button.setFixedWidth(100)
        input_layout.addWidget(browse_button)

        self.main_layout.addLayout(input_layout)
        self.main_layout.addSpacing(10)

    def create_format_options(self):
        """Create the output format selection section"""
        format_group = QGroupBox("Output Format")
        format_layout = QVBoxLayout(format_group)

        # Radio buttons for format selection
        self.format_txt_radio = QRadioButton("Text File (.txt)")
        self.format_txt_radio.setChecked(True)
        self.format_txt_radio.toggled.connect(self.toggle_separator_options)
        format_layout.addWidget(self.format_txt_radio)

        self.format_json_radio = QRadioButton("JSON File (.json)")
        self.format_json_radio.toggled.connect(self.toggle_separator_options)
        format_layout.addWidget(self.format_json_radio)

        self.main_layout.addWidget(format_group)
        self.main_layout.addSpacing(10)

    def create_separator_section(self):
        """Create the separator options section"""
        self.separator_group = QGroupBox("Separator Options")
        separator_layout = QVBoxLayout(self.separator_group)

        # Question-Answer separator
        qa_sep_label = QLabel("Question-Answer Separator:")
        separator_layout.addWidget(qa_sep_label)

        self.qa_separator_combo = QComboBox()
        self.qa_separator_combo.addItems(["\\t", ",", "|", ";;", "=>", " - "])
        separator_layout.addWidget(self.qa_separator_combo)

        # Card separator
        card_sep_label = QLabel("Card Separator:")
        separator_layout.addWidget(card_sep_label)

        self.card_separator_combo = QComboBox()
        self.card_separator_combo.addItems(
            ["\\n", "\\n\\n", ";", "===", "---", "*****"]
        )
        separator_layout.addWidget(self.card_separator_combo)

        self.main_layout.addWidget(self.separator_group)
        self.main_layout.addSpacing(10)

    def create_cleaning_section(self):
        """Create the text cleaning options section"""
        cleaning_group = QGroupBox("Text Cleaning Options")
        cleaning_layout = QVBoxLayout(cleaning_group)

        # Words to remove
        words_label = QLabel("Words/Phrases to Remove (comma-separated):")
        cleaning_layout.addWidget(words_label)

        self.words_to_remove_input = QLineEdit("NHUNG HOÀNG")
        cleaning_layout.addWidget(self.words_to_remove_input)

        # Characters to remove
        chars_label = QLabel("Characters to Remove (no spaces):")
        cleaning_layout.addWidget(chars_label)

        self.chars_to_remove_input = QLineEdit("[](){}")
        cleaning_layout.addWidget(self.chars_to_remove_input)

        self.main_layout.addWidget(cleaning_group)
        self.main_layout.addSpacing(10)

    def create_preview_section(self):
        """Create the preview section with progress bar"""
        # Header with label and status
        preview_header = QHBoxLayout()

        preview_label = QLabel("Preview")
        preview_label.setFont(QFont("Arial", 12, QFont.Bold))
        preview_header.addWidget(preview_label)

        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet(f"color: {ModernTheme.ACCENT_COLOR};")
        preview_header.addWidget(self.loading_label, alignment=Qt.AlignRight)

        self.main_layout.addLayout(preview_header)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # Preview text area
        self.preview_text = QTextEdit()
        self.preview_text.setFont(QFont("Consolas", 10))
        self.preview_text.setReadOnly(True)
        self.main_layout.addWidget(self.preview_text)

    def create_action_buttons(self):
        """Create bottom action buttons"""
        button_layout = QHBoxLayout()

        # Left side buttons
        preview_btn = QPushButton("Preview (Ctrl+P)")
        preview_btn.clicked.connect(self.preview)
        button_layout.addWidget(preview_btn)

        save_btn = QPushButton("Save (Ctrl+S)")
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)

        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(clear_btn)

        # Spacing
        button_layout.addStretch()

        # Right side buttons
        help_btn = QPushButton("Help (F1)")
        help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(help_btn)

        self.main_layout.addLayout(button_layout)

    def apply_stylesheets(self):
        """Apply stylesheets to give the application a modern look"""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ 
                background-color: {ModernTheme.BG_COLOR}; 
                color: {ModernTheme.FG_COLOR};
            }}
            QLabel {{ 
                background-color: transparent; 
                color: {ModernTheme.FG_COLOR};
            }}
            QPushButton {{ 
                background-color: {ModernTheme.BUTTON_BG}; 
                color: {ModernTheme.BUTTON_FG}; 
                border: none; 
                padding: 8px 15px; 
                border-radius: 4px;
            }}
            QPushButton:hover {{ 
                background-color: {ModernTheme.ACCENT_DARK}; 
            }}
            QLineEdit, QTextEdit, QComboBox {{ 
                background-color: {ModernTheme.ENTRY_BG}; 
                color: {ModernTheme.ENTRY_FG}; 
                border: 1px solid {ModernTheme.BORDER_COLOR}; 
                border-radius: 4px; 
                padding: 5px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ 
                border: 1px solid {ModernTheme.HIGHLIGHT_COLOR}; 
            }}
            QGroupBox {{ 
                background-color: {ModernTheme.FRAME_BG}; 
                border: 1px solid {ModernTheme.BORDER_COLOR}; 
                border-radius: 4px; 
                margin-top: 10px;
                padding: 15px;
            }}
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px 0 5px; 
            }}
            QRadioButton {{ 
                background-color: {ModernTheme.FRAME_BG}; 
                color: {ModernTheme.FG_COLOR};
            }}
            QProgressBar {{
                border: 1px solid {ModernTheme.BORDER_COLOR};
                border-radius: 4px;
                background-color: {ModernTheme.FRAME_BG};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ModernTheme.ACCENT_COLOR};
                width: 5px;
            }}
            QStatusBar {{
                background-color: {ModernTheme.FRAME_BG};
                color: {ModernTheme.FG_COLOR};
            }}
        """)

    def browse_file(self):
        """Open file dialog to select HTML file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select HTML File", "", "HTML files (*.html);;All files (*)"
        )
        if filename:
            self.file_path_input.setText(filename)

    def on_input_change(self, text):
        """Handle changes in the input file path"""
        # Simple validation: check if the file exists
        if os.path.isfile(text):
            self.statusBar.showMessage(f"File loaded: {text}")
            # Auto-preview for supported files
            if text.lower().endswith((".html", ".htm")):
                QTimer.singleShot(500, self.preview)
            else:
                self.statusBar.showMessage("Selected file is not an HTML file")
        else:
            self.statusBar.showMessage("Invalid file. Please select a valid HTML file.")

    def toggle_separator_options(self):
        """Toggle visibility of separator options based on format type"""
        # Show separator options only for TXT format
        self.separator_group.setVisible(self.format_txt_radio.isChecked())

        # Auto-preview when format changes
        if self.file_path_input.text():
            QTimer.singleShot(500, self.preview)

    def get_separators(self):
        """Get the actual separator characters from the UI strings"""
        qa_sep = (
            self.qa_separator_combo.currentText()
            .replace("\\t", "\t")
            .replace("\\n", "\n")
        )
        card_sep = (
            self.card_separator_combo.currentText()
            .replace("\\t", "\t")
            .replace("\\n", "\n")
        )
        return qa_sep, card_sep

    def preview(self):
        """Generate a preview of the converted content"""
        file_path = self.file_path_input.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.critical(self, "Error", "Please select a valid input file")
            return

        # Show loading and progress indicators
        self.loading_label.setText("Loading...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Get cleaning options
        words_to_remove = [
            word.strip()
            for word in self.words_to_remove_input.text().split(",")
            if word.strip()
        ]
        chars_to_remove = self.chars_to_remove_input.text()

        # Determine format type
        format_type = "json" if self.format_json_radio.isChecked() else "txt"

        # Get separators if format type is txt
        qa_sep, card_sep = "", ""
        if format_type == "txt":
            qa_sep, card_sep = self.get_separators()

        # Use both QThread for UI updates and ThreadPoolExecutor for CPU-bound work
        # Create and start worker thread
        self.worker = PreviewWorker(
            file_path, words_to_remove, chars_to_remove, format_type, qa_sep, card_sep
        )

        # Connect worker signals
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_preview_completed)
        self.worker.error.connect(self.on_preview_error)

        # For CPU-bound tasks in the worker, we'll use the ThreadPoolExecutor
        # This helps better utilize multiple cores
        self.worker.start()

    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)

    def on_preview_completed(self, qa_pairs, preview_content):
        """Handle completion of preview generation"""
        # Update preview text
        self.preview_text.setText(preview_content)

        # Update status and labels
        if qa_pairs:
            self.loading_label.setText(f"Found {len(qa_pairs)} question-answer pairs")
            self.statusBar.showMessage(
                f"Preview successful - {len(qa_pairs)} question-answer pairs found"
            )
        else:
            self.loading_label.setText("No questions found")
            self.statusBar.showMessage("No questions found in the file")

        # Hide progress bar
        self.progress_bar.setVisible(False)

    def on_preview_error(self, error_message):
        """Handle errors from the preview worker"""
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.loading_label.setText("")
        self.statusBar.showMessage(f"Error: {error_message}")
        self.progress_bar.setVisible(False)

    def save(self):
        """Save the converted content to a file"""
        file_path = self.file_path_input.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.critical(self, "Error", "Please select an input file first.")
            return

        if not self.preview_text.toPlainText().strip():
            QMessageBox.warning(
                self, "Warning", "Preview is empty. Please generate a preview first."
            )
            return

        # Get cleaning options
        words_to_remove = [
            word.strip()
            for word in self.words_to_remove_input.text().split(",")
            if word.strip()
        ]
        chars_to_remove = self.chars_to_remove_input.text()

        # Use ThreadPoolExecutor for I/O and CPU-bound operations
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Show a temporary "processing" message
            self.statusBar.showMessage("Processing...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(25)  # Initial progress

            # Extract QA pairs in a separate thread
            future = executor.submit(
                extract_qa_pairs,
                file_path,
                words_to_remove=words_to_remove,
                chars_to_remove=chars_to_remove,
            )

            # Create a Timer to update progress periodically while waiting for future
            self.save_timer = QTimer()
            self.save_timer.timeout.connect(
                lambda: self.progress_bar.setValue(
                    min(95, self.progress_bar.value() + 5)
                )  # Gradual progress
            )
            self.save_timer.start(200)  # Update every 200ms

            try:
                # Get the result (this blocks until the thread completes)
                qa_pairs = future.result()  # This call blocks

                # Once future.result() returns, stop the timer and set progress to near completion
                self.save_timer.stop()
                self.progress_bar.setValue(95)  # Indicates extraction is done

                if not qa_pairs:
                    QMessageBox.information(self, "Info", "No questions found")
                    self.progress_bar.setVisible(False)
                    self.statusBar.showMessage("No questions found, save cancelled.")
                    return

                # Determine format type and file extension
                is_json = self.format_json_radio.isChecked()
                default_ext = ".json" if is_json else ".txt"

                # Get output file path from user
                output_file, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Output",
                    "",  # Default directory
                    f"{'JSON' if is_json else 'Text'} Files (*{default_ext});;All Files (*)",
                )

                if not output_file:
                    self.progress_bar.setVisible(False)
                    self.statusBar.showMessage("Save cancelled by user.")
                    return  # User cancelled

                # Prepare to save the file in a background thread
                # (actual saving can still be I/O bound)
                self.progress_bar.setValue(100)  # Indicate saving process starts

                qa_sep, card_sep = self.get_separators()
                save_func = (
                    save_to_json
                    if is_json
                    else partial(
                        save_to_txt, qa_separator=qa_sep, card_separator=card_sep
                    )
                )

                # Define the function to run in the saving thread
                def save_and_notify_task():
                    try:
                        save_func(
                            qa_pairs, output_file
                        )  # Corrected: pass qa_pairs first
                        # Use QTimer.singleShot to ensure UI updates run on the main thread
                        QTimer.singleShot(
                            0, lambda: self.show_save_success(output_file)
                        )
                    except Exception:
                        QTimer.singleShot(
                            0, lambda: self.show_save_error(str(Exception))
                        )

                # Start a new Python thread for the saving operation
                save_thread = threading.Thread(target=save_and_notify_task, daemon=True)
                save_thread.start()

            except Exception as e_extract:  # Handles exceptions from future.result() (extract_qa_pairs)
                self.save_timer.stop()
                self.progress_bar.setVisible(False)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred during data extraction: {str(e_extract)}",
                )
                self.statusBar.showMessage(f"Error during extraction: {str(e_extract)}")

    def copy_to_clipboard(self):
        """Copy the preview text to clipboard"""
        text = self.preview_text.toPlainText()
        if text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
        else:
            self.statusBar.showMessage("Nothing to copy - preview is empty")

    def clear_all(self):
        """Clear all inputs and preview"""
        self.file_path_input.clear()
        self.preview_text.clear()
        self.loading_label.setText("")
        self.progress_bar.setVisible(False)
        self.statusBar.showMessage("All cleared!")

    def show_help(self):
        """Show help information"""
        help_text = """
Quizlet Converter Help

1. Load HTML: Click 'Browse' or drag-drop an HTML file
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
        """Show about information"""
        about_text = f"""
Quizlet Converter

A simple tool to convert Quizlet HTML files to 
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
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
