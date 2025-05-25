#!/usr/bin/env python3
"""
Batch processor for multiple PDF files.
Processes all PDF files in a directory through the complete workflow.
"""

import os
import sys
import glob
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from main import QuizProcessingWorkflow


def batch_process():
    """Process multiple PDF files in batch."""
    print("📚 Quiz Processing Workflow - Batch Mode")
    print("=" * 42)

    # Get input directory
    input_dir = input(
        "Enter directory containing PDF files (default: current): "
    ).strip()
    if not input_dir:
        input_dir = "."

    if not os.path.exists(input_dir):
        print(f"❌ Directory '{input_dir}' not found!")
        return

    # Find PDF files
    pdf_pattern = os.path.join(input_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        print(f"❌ No PDF files found in '{input_dir}'")
        return

    print(f"📄 Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"   - {os.path.basename(pdf)}")

    # Get API key
    api_key = input("\nEnter Google Gemini API key: ").strip()
    if not api_key:
        print("❌ API key is required!")
        return

    # Get settings
    try:
        chunk_size = int(input("Chunk size (default: 30): ").strip() or "30")
    except ValueError:
        chunk_size = 30

    try:
        similarity_threshold = float(
            input("Similarity threshold (default: 0.8): ").strip() or "0.8"
        )
    except ValueError:
        similarity_threshold = 0.8

    # Create output directory
    output_dir = (
        input("Output directory (default: processed_quizzes): ").strip()
        or "processed_quizzes"
    )
    os.makedirs(output_dir, exist_ok=True)

    # Process each PDF
    successful = 0
    failed = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n📖 Processing {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print("-" * 60)

        # Create subdirectory for this PDF
        pdf_name = Path(pdf_file).stem
        pdf_output_dir = os.path.join(output_dir, pdf_name)
        os.makedirs(pdf_output_dir, exist_ok=True)

        # Change to PDF output directory for processing
        original_dir = os.getcwd()
        os.chdir(pdf_output_dir)

        try:
            workflow = QuizProcessingWorkflow()
            final_file = workflow.run_full_workflow(
                pdf_file=os.path.abspath(pdf_file),
                api_key=api_key,
                chunk_size=chunk_size,
                similarity_threshold=similarity_threshold,
            )

            if final_file:
                print(f"✅ Completed: {pdf_name}")
                successful += 1
            else:
                print(f"❌ Failed: {pdf_name}")
                failed += 1

        except Exception as e:
            print(f"❌ Error processing {pdf_name}: {str(e)}")
            failed += 1

        finally:
            os.chdir(original_dir)

    # Summary
    print(f"\n📊 BATCH PROCESSING COMPLETE")
    print("=" * 30)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    batch_process()
