# Quizleter

![Quizleter Banner](assets/banner.png) [![Release Builder](https://github.com/lunovian/quizleter/actions/workflows/manual-release.yml/badge.svg)](https://github.com/lunovian/quizleter/actions/workflows/manual-release.yml)

Quizleter is a tool for converting Quizlet HTML exports into structured formats for better studying, flashcard creation, and content reuse.

## Overview

Quizleter extracts multiple-choice questions and answers from Quizlet HTML files and converts them into more usable formats like text or JSON. This is particularly useful for students and educators who want to:

- Export their Quizlet study sets to other flashcard applications
- Create printable study materials
- Format question sets for integration with other learning tools
- Clean up and standardize the formatting of questions and answers

## Features

- **HTML Parsing**: Extract questions, options, and answers from Quizlet exports
- **Text Cleaning**:
  - Remove specific words or phrases (like author names)
  - Strip unwanted characters from text
  - Standardize formatting across all questions
- **Multiple Output Formats**:
  - Text files with customizable separators
  - JSON format for programmatic use
- **User-Friendly Interface**:
  - Simple drag-and-drop interface
  - Preview feature to check output before saving
  - Progress tracking for large files
- **Customization Options**:
  - Define question-answer separators (tab, comma, etc.)
  - Set card separators (newlines, special characters, etc.)
  - Specify words and characters to remove

## Getting Started

### Installation

1. Download the latest release from the [Releases page](https://github.com/your-username/quizlet-tool/releases)
2. Extract the ZIP file
3. Run the `Quizleter.exe` executable (Windows) or the equivalent for your platform

### For Developers

If you want to run from source:

```bash
# Clone the repository
git clone https://github.com/your-username/quizlet-tool.git
cd quizlet-tool

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## How to Use

1. **Launch the application**: Open Quizleter
2. **Load the HTML file**:
   - Click "Browse" to select your Quizlet HTML export file, or
   - Drag and drop the file onto the application
3. **Choose output format**:
   - Select "Text File (.txt)" or "JSON File (.json)"
4. **Customize separators** (for text format):
   - Set the question-answer separator (tab, comma, etc.)
   - Set the card separator (newline, double newline, etc.)
5. **Text cleaning options**:
   - Enter words/phrases to remove (comma-separated)
   - Specify characters to remove
6. **Preview the results**:
   - Click "Preview" or press Ctrl+P to see how the output will look
7. **Save the file**:
   - Click "Save" or press Ctrl+S to save the processed file
   - Choose a location and filename

## Executable File

The application is distributed as a standalone executable file:

- **Windows**: `Quizleter-X.X.X.exe` (64-bit) where X.X.X is the version number
- **Automatic Updates**: The application does not currently auto-update; check the Releases page for new versions
- **No Installation Required**: The executable is portable and requires no installation
- **First Run**: Windows may show a security warning when running for the first time. Click "More info" and then "Run anyway" to proceed

### Downloading Executables

The application executable is automatically built and uploaded to GitHub Releases through GitHub Actions whenever a new version is released. To download:

1. Visit the [Releases page](https://github.com/your-username/quizlet-tool/releases)
2. Find the latest release and download the ZIP file containing the executable
3. Extract the ZIP file to a location of your choice
4. Run the executable directly - no installation needed

### Releases Versioning

Releases follow semantic versioning (X.Y.Z):

- X: Major version with significant changes
- Y: Minor version with new features
- Z: Patch version with bug fixes

## Example

Converting a Quizlet export with multiple-choice questions:

**Original Quizlet HTML content**:

```text
What is the capital of France?
A. London
B. Berlin
C. Paris
D. Madrid
```

**Cleaned Text output**:

```text
What is the capital of France?
A. London
B. Berlin
C. Paris
D. Madrid    C
```

**JSON output**:

```json
{
  "question": "What is the capital of France?",
  "options": ["London", "Berlin", "Paris", "Madrid"],
  "answer": "C"
}
```

## Requirements

- Windows 7/8/10/11, macOS 10.14+, or Linux
- No additional software required for the standalone executable
- Python 3.8+ (if running from source)

## Building

The application can be built into a standalone executable using PyInstaller:

```bash
pyinstaller --name="Quizleter" --onefile --windowed --icon=assets/icon.ico app.py
```

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
