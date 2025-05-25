import os
import math
import re


def split_raw_text_data(input_file, chunk_size=50, output_dir="raw_chunks"):
    """
    Split raw text data into smaller chunks for Gemini processing.
    Each chunk will contain a reasonable amount of raw text that can be processed by Gemini.

    Args:
        input_file (str): Path to the raw text file
        chunk_size (int): Approximate number of questions per chunk (estimated)
        output_dir (str): Directory to save chunk files
    """

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # Read the raw text data
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print("No content found in the input file.")
            return

        # Estimate chunk size based on content length and target questions per chunk
        lines = content.split("\n")
        total_lines = len(lines)

        # Estimate lines per question (rough approximation)
        lines_per_question = max(
            8, total_lines // (chunk_size * 10)
        )  # Conservative estimate
        lines_per_chunk = chunk_size * lines_per_question

        print(f"Total lines in file: {total_lines}")
        print(f"Estimated lines per question: {lines_per_question}")
        print(f"Target lines per chunk: {lines_per_chunk}")

        # Split content into chunks
        chunks = []
        start_idx = 0

        while start_idx < total_lines:
            end_idx = min(start_idx + lines_per_chunk, total_lines)

            # Try to find a good breaking point (avoid splitting in middle of questions)
            if end_idx < total_lines:
                # Look for a good break point within the last 20% of the chunk
                search_start = max(
                    start_idx + int(lines_per_chunk * 0.8), start_idx + 1
                )

                # Look for empty lines or question patterns as break points
                for i in range(end_idx, search_start - 1, -1):
                    if i < len(lines):
                        line = lines[i].strip()
                        # Good break points: empty lines, or lines that look like question starts
                        if (
                            not line
                            or re.match(r"^[A-Z].*\?$", line)  # Question ending with ?
                            or re.match(r"^\d+\.", line)  # Numbered questions
                            or len(line) > 50
                            and "?" in line
                        ):  # Likely question text
                            end_idx = i + 1
                            break

            chunk_lines = lines[start_idx:end_idx]
            chunk_content = "\n".join(chunk_lines).strip()

            if chunk_content:
                chunks.append(chunk_content)

            start_idx = end_idx

        total_chunks = len(chunks)
        print(f"Created {total_chunks} chunks for processing")

        # Save chunks to files
        for chunk_num, chunk_content in enumerate(chunks):
            chunk_filename = f"raw_chunk_{chunk_num + 1:03d}.txt"
            chunk_path = os.path.join(output_dir, chunk_filename)

            # Write chunk to file
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(chunk_content)

            # Count approximate questions in chunk (rough estimate)
            question_marks = chunk_content.count("?")
            print(
                f"Created {chunk_filename} with ~{question_marks} potential questions ({len(chunk_content.split())} words)"
            )

        # Create summary file
        summary_filename = os.path.join(output_dir, "raw_chunk_summary.txt")
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(f"Raw Text Split Summary\n")
            f.write(f"=" * 25 + "\n\n")
            f.write(f"Original file: {input_file}\n")
            f.write(f"Total lines: {total_lines}\n")
            f.write(f"Target chunk size: {chunk_size} questions\n")
            f.write(f"Total chunks created: {total_chunks}\n\n")
            f.write("Chunk Details:\n")
            f.write("-" * 15 + "\n")

            for chunk_num in range(total_chunks):
                chunk_filename = f"raw_chunk_{chunk_num + 1:03d}.txt"
                chunk_path = os.path.join(output_dir, chunk_filename)

                # Get chunk stats
                with open(chunk_path, "r", encoding="utf-8") as cf:
                    chunk_text = cf.read()
                    word_count = len(chunk_text.split())
                    question_count = chunk_text.count("?")

                f.write(
                    f"{chunk_filename}: ~{question_count} questions, {word_count} words\n"
                )

        print(f"\nSummary saved to: {summary_filename}")
        print(f"All raw chunks saved to directory: {output_dir}")
        print(f"\nNext step: Run these chunks through Gemini corrector for processing")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error processing file: {e}")


def merge_chunks(chunks_dir="raw_chunks", output_file="merged_raw_data.txt"):
    """
    Merge chunk files back into a single file (for verification).

    Args:
        chunks_dir (str): Directory containing chunk files
        output_file (str): Output file for merged content
    """

    try:
        if not os.path.exists(chunks_dir):
            print(f"Error: Chunks directory '{chunks_dir}' not found.")
            return

        # Get all chunk files and sort them
        chunk_files = [
            f
            for f in os.listdir(chunks_dir)
            if f.startswith("raw_chunk_") and f.endswith(".txt")
        ]
        chunk_files.sort()

        if not chunk_files:
            print(f"No raw chunk files found in '{chunks_dir}'")
            return

        merged_content = []

        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunks_dir, chunk_file)
            with open(chunk_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    merged_content.append(content)

        # Write merged content
        final_content = "\n\n".join(merged_content)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)

        print(f"Merged {len(chunk_files)} chunk files")
        print(f"Merged content saved to: {output_file}")

    except Exception as e:
        print(f"Error merging chunks: {e}")


if __name__ == "__main__":
    # Default settings
    input_file = "raw_extracted_text.txt"
    chunk_size = 30  # Target questions per chunk (estimated)
    output_dir = "raw_chunks"

    print("Raw Text Splitter for Gemini Processing")
    print("=" * 40)

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        print("Please make sure the raw text file exists.")
    else:
        # Ask user for chunk size
        try:
            user_chunk_size = input(
                f"Enter target questions per chunk (default {chunk_size}): "
            ).strip()
            if user_chunk_size:
                chunk_size = int(user_chunk_size)
        except ValueError:
            print(f"Invalid input. Using default chunk size: {chunk_size}")

        # Split the data
        split_raw_text_data(input_file, chunk_size, output_dir)

        # Ask if user wants to test merge (for verification)
        test_merge = input("\nTest merge chunks back together? (y/n): ").strip().lower()
        if test_merge == "y":
            merge_chunks(output_dir, "test_merged_raw_data.txt")

        print(f"\n{'=' * 50}")
        print("NEXT STEPS:")
        print("1. Use gemini_corrector.py to process the raw chunks")
        print("2. Point the corrector to input_dir='raw_chunks'")
        print(
            "3. The corrector will clean and format the raw text into proper Q&A format"
        )
        print("=" * 50)
