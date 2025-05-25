#!/usr/bin/env python3
"""
Quick workflow runner for quiz processing.
Run this to process a PDF through the complete workflow.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from main import QuizProcessingWorkflow


def quick_run():
    """Quick run with minimal prompts."""
    print("🚀 Quiz Processing Workflow - Quick Run")
    print("=" * 42)

    # Check for PDF files in current directory
    pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]

    if pdf_files:
        print(f"Found {len(pdf_files)} PDF file(s) in current directory:")
        for i, pdf in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf}")

        if len(pdf_files) == 1:
            pdf_file = pdf_files[0]
            print(f"Using: {pdf_file}")
        else:
            try:
                choice = int(input("Select PDF file (number): ").strip()) - 1
                pdf_file = pdf_files[choice]
            except (ValueError, IndexError):
                pdf_file = input("Enter PDF file path: ").strip()
    else:
        pdf_file = input("Enter PDF file path: ").strip()

    # Get API key
    api_key = input("Enter Google Gemini API key: ").strip()

    if not pdf_file or not api_key:
        print("❌ PDF file and API key are required!")
        return

    # Run with defaults
    workflow = QuizProcessingWorkflow()
    final_file = workflow.run_full_workflow(
        pdf_file=pdf_file, api_key=api_key, chunk_size=30, similarity_threshold=0.8
    )

    if final_file:
        print(f"\n🎉 SUCCESS! Your quiz file is ready: {final_file}")
    else:
        print("\n💥 Processing failed. Check the logs above.")


if __name__ == "__main__":
    quick_run()
