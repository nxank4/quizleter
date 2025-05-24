import os
import concurrent.futures
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
import json
from .retrieve_pdf import (
    extract_qa_pairs_from_pdf as extract_qa_pairs,
    format_qa_pairs,
)


class PreviewWorker(QThread):
    """Worker thread for processing PDF files and generating preview content"""

    finished = pyqtSignal(list, str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(
        self,
        file_path: str,
        words_to_remove: List[str],
        chars_to_remove: str,
        format_type: str,
        qa_sep: str = "",
        card_sep: str = "",
    ):
        super().__init__()
        self.file_path = file_path
        self.words_to_remove = words_to_remove
        self.chars_to_remove = chars_to_remove
        self.format_type = format_type
        self.qa_sep = qa_sep
        self.card_sep = card_sep
        # Use CPU count - 1 for worker threads to leave one core free for the UI
        max_workers = max(1, os.cpu_count() - 1) if os.cpu_count() else 2
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def run(self):
        try:
            self.progress.emit(0)

            # Start the extraction in a separate thread
            future = self.executor.submit(
                extract_qa_pairs,
                self.file_path,
                words_to_remove=self.words_to_remove,
                chars_to_remove=self.chars_to_remove,
            )

            # Monitor progress without blocking the UI
            while not future.done():
                QThread.msleep(50)  # Short sleep to prevent CPU hogging
                self.progress.emit(25)  # Indicate ongoing extraction

            qa_pairs = future.result()
            self.progress.emit(50)

            if not qa_pairs:
                self.finished.emit([], "No questions found in this file")
                return

            # Format data in another thread
            format_future = self.executor.submit(self._format_data, qa_pairs)

            # Monitor formatting progress
            while not format_future.done():
                QThread.msleep(50)
                self.progress.emit(75)

            preview_content = format_future.result()
            self.progress.emit(100)
            self.finished.emit(qa_pairs, preview_content)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.executor.shutdown(wait=False)

    def _format_data(self, qa_pairs):
        """Handle data formatting in a separate method for better organization"""
        if self.format_type == "json":
            return json.dumps(qa_pairs, ensure_ascii=False, indent=2)
        return format_qa_pairs(qa_pairs, self.qa_sep, self.card_sep)
