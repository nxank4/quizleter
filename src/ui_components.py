import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QRadioButton,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QComboBox,
)


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class UIComponents:
    @staticmethod
    def create_menu_bar(parent):
        menu_bar = parent.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("📂 Open PDF File", parent)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(parent.browse_file)
        file_menu.addAction(open_action)

        save_action = QAction("💾 Save Output", parent)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(parent.save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        exit_action = QAction("❌ Exit", parent)
        exit_action.triggered.connect(parent.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        copy_action = QAction("📋 Copy to Clipboard", parent)
        copy_action.triggered.connect(parent.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        clear_action = QAction("🧹 Clear All", parent)
        clear_action.triggered.connect(parent.clear_all)
        edit_menu.addAction(clear_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        preview_action = QAction("👁️ Preview", parent)
        preview_action.setShortcut("Ctrl+P")
        preview_action.triggered.connect(parent.preview)
        view_menu.addAction(preview_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        help_action = QAction("❓ Help", parent)
        help_action.setShortcut("F1")
        help_action.triggered.connect(parent.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("ℹ️ About", parent)
        about_action.triggered.connect(parent.show_about)
        help_menu.addAction(about_action)

    @staticmethod
    def create_input_section(parent):
        input_label = QLabel("1. Select PDF File")
        input_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        parent.main_layout.addWidget(input_label)

        input_layout = QHBoxLayout()
        parent.file_path_input = QLineEdit()
        parent.file_path_input.setPlaceholderText(
            "Drag & drop or browse for a PDF file..."
        )
        parent.file_path_input.setClearButtonEnabled(True)
        parent.file_path_input.textChanged.connect(parent.on_input_change)
        input_layout.addWidget(parent.file_path_input)

        browse_button = QPushButton("Browse")
        browse_button.setToolTip("Browse for a PDF file")
        browse_button.clicked.connect(parent.browse_file)
        browse_button.setFixedWidth(90)
        input_layout.addWidget(browse_button)

        parent.main_layout.addLayout(input_layout)
        parent.main_layout.addSpacing(8)

    @staticmethod
    def create_format_options(parent):
        format_group = QGroupBox("2. Output Format")
        format_layout = QHBoxLayout(format_group)

        parent.format_txt_radio = QRadioButton("Text (.txt)")
        parent.format_txt_radio.setChecked(True)
        parent.format_txt_radio.toggled.connect(parent.toggle_separator_options)
        format_layout.addWidget(parent.format_txt_radio)

        parent.format_json_radio = QRadioButton("JSON (.json)")
        parent.format_json_radio.toggled.connect(parent.toggle_separator_options)
        format_layout.addWidget(parent.format_json_radio)

        format_layout.addStretch()
        parent.main_layout.addWidget(format_group)
        parent.main_layout.addSpacing(8)

    @staticmethod
    def create_separator_section(parent):
        separator_group = QGroupBox("3. Q&A Separator")
        separator_layout = QHBoxLayout(separator_group)

        separator_label = QLabel("Separator:")
        separator_layout.addWidget(separator_label)

        parent.qa_separator_combo = QComboBox()
        parent.qa_separator_combo.addItems(["→", "=", "⇒", ":", ">>", "-"])
        parent.qa_separator_combo.setFixedWidth(100)
        separator_layout.addWidget(parent.qa_separator_combo)

        separator_layout.addStretch()
        parent.main_layout.addWidget(separator_group)
        parent.main_layout.addSpacing(8)

    @staticmethod
    def create_cleaning_section(parent):
        cleaning_group = QGroupBox("4. Text Cleaning")
        cleaning_layout = QHBoxLayout(cleaning_group)

        words_label = QLabel("Remove words/phrases:")
        cleaning_layout.addWidget(words_label)

        parent.words_to_remove_input = QLineEdit("NHUNG HOÀNG")
        parent.words_to_remove_input.setToolTip(
            "Comma-separated words/phrases to remove"
        )
        cleaning_layout.addWidget(parent.words_to_remove_input)

        chars_label = QLabel("Remove characters:")
        cleaning_layout.addWidget(chars_label)

        parent.chars_to_remove_input = QLineEdit("[](){}")
        parent.chars_to_remove_input.setToolTip("Characters to remove (no spaces)")
        cleaning_layout.addWidget(parent.chars_to_remove_input)

        cleaning_layout.addStretch()
        parent.main_layout.addWidget(cleaning_group)
        parent.main_layout.addSpacing(8)

    @staticmethod
    def create_preview_section(parent):
        preview_header = QHBoxLayout()
        preview_label = QLabel("5. Preview")
        preview_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        preview_header.addWidget(preview_label)

        parent.loading_label = QLabel("")
        parent.loading_label.setStyleSheet("color: #0064e7;")
        preview_header.addWidget(
            parent.loading_label, alignment=Qt.AlignmentFlag.AlignRight
        )

        parent.main_layout.addLayout(preview_header)

        parent.progress_bar = QProgressBar()
        parent.progress_bar.setRange(0, 100)
        parent.progress_bar.setValue(0)
        parent.progress_bar.setVisible(False)
        parent.progress_bar.setFixedHeight(18)
        parent.main_layout.addWidget(parent.progress_bar)

        parent.preview_text = QTextEdit()
        parent.preview_text.setFont(QFont("Consolas", 11))
        parent.preview_text.setReadOnly(True)
        parent.preview_text.setPlaceholderText(
            "Preview will appear here after processing..."
        )
        parent.main_layout.addWidget(parent.preview_text)

    @staticmethod
    def create_action_buttons(parent):
        button_layout = QHBoxLayout()

        preview_btn = QPushButton("👁️ Preview (Ctrl+P)")
        preview_btn.setToolTip("Preview the converted content")
        preview_btn.clicked.connect(parent.preview)
        button_layout.addWidget(preview_btn)

        save_btn = QPushButton("💾 Save (Ctrl+S)")
        save_btn.setToolTip("Save the converted content")
        save_btn.clicked.connect(parent.save)
        button_layout.addWidget(save_btn)

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setToolTip("Copy preview to clipboard")
        copy_btn.clicked.connect(parent.copy_to_clipboard)
        button_layout.addWidget(copy_btn)

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setToolTip("Clear all fields")
        clear_btn.clicked.connect(parent.clear_all)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        help_btn = QPushButton("❓ Help (F1)")
        help_btn.setToolTip("Show help")
        help_btn.clicked.connect(parent.show_help)
        button_layout.addWidget(help_btn)

        parent.main_layout.addLayout(button_layout)
