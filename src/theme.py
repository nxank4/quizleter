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

    @classmethod
    def get_stylesheet(cls):
        return f"""
            QMainWindow, QWidget {{ 
                background-color: {cls.BG_COLOR}; 
                color: {cls.FG_COLOR};
            }}
            QLabel {{ 
                background-color: transparent; 
                color: {cls.FG_COLOR};
            }}
            QPushButton {{ 
                background-color: {cls.BUTTON_BG}; 
                color: {cls.BUTTON_FG}; 
                border: none; 
                padding: 8px 15px; 
                border-radius: 4px;
            }}
            QPushButton:hover {{ 
                background-color: {cls.ACCENT_DARK}; 
            }}
            QLineEdit, QTextEdit, QComboBox {{ 
                background-color: {cls.ENTRY_BG}; 
                color: {cls.ENTRY_FG}; 
                border: 1px solid {cls.BORDER_COLOR}; 
                border-radius: 4px; 
                padding: 5px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ 
                border: 1px solid {cls.HIGHLIGHT_COLOR}; 
            }}
            QGroupBox {{ 
                background-color: {cls.FRAME_BG}; 
                border: 1px solid {cls.BORDER_COLOR}; 
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
                background-color: {cls.FRAME_BG}; 
                color: {cls.FG_COLOR};
            }}
            QProgressBar {{
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: 4px;
                background-color: {cls.FRAME_BG};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {cls.ACCENT_COLOR};
                width: 5px;
            }}
            QStatusBar {{
                background-color: {cls.FRAME_BG};
                color: {cls.FG_COLOR};
            }}
            /* Fix QComboBox popup background */
            QComboBox QAbstractItemView {{
                background-color: {cls.ENTRY_BG};
                color: {cls.ENTRY_FG};
                selection-background-color: {cls.ACCENT_COLOR};
                selection-color: {cls.BUTTON_FG};
            }}
        """
