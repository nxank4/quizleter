import os
import time
import json
import google.generativeai as genai
from typing import List, Dict, Optional


class GeminiCorrector:
    def __init__(self, api_key: str):
        """
        Initialize the Gemini corrector with API key.

        Args:
            api_key (str): Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def create_correction_prompt(self, chunk_content: str) -> str:
        """
        Create a prompt for correcting quiz data.

        Args:
            chunk_content (str): Content of the chunk file

        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = f"""
Please correct and format the following Vietnamese quiz data. Each question should follow this exact format:

Question text here?
A. Option A
B. Option B  
C. Option C
D. Option D;;CORRECT_ANSWER

Rules for correction:
1. Fix any formatting issues (missing separators, malformed options)
2. Ensure each question has exactly 4 options or more (A, B, C, D, E, ...)
3. Ensure each question has a correct answer marked with ;;
4. Remove any duplicate content or metadata
5. Fix any obvious OCR errors in Vietnamese text
6. Ensure proper spacing and line breaks
7. Keep the original meaning and content intact
8. If a question is missing an answer, mark it as ;;? for manual review
9. Remove any text that appears to be navigation, headers, or footers
10. Each Q&A pair should be separated by double newlines
11. If an answer has additional context or explanation, format it as: ;;ANSWER (explanation)
12. For example: ;;A (Vì đây là nguyên lý cơ bản) or ;;C (Theo quan điểm của Marx)

Answer format examples:
- Simple answer: ;;A
- Answer with explanation: ;;B (Đây là định nghĩa chuẩn theo triết học Mác-Lênin)
- Answer with reference: ;;D (Theo Ph.Ăngghen trong "Biện chứng của tự nhiên")

Original content:
{chunk_content}

Please return only the corrected quiz data in the specified format, nothing else.
"""
        return prompt

    def correct_chunk(self, chunk_content: str, max_retries: int = 3) -> Optional[str]:
        """
        Correct a single chunk using Gemini API.

        Args:
            chunk_content (str): Content to correct
            max_retries (int): Maximum number of retry attempts

        Returns:
            Optional[str]: Corrected content or None if failed
        """
        prompt = self.create_correction_prompt(chunk_content)

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)

                if response.text:
                    return response.text.strip()
                else:
                    print(
                        f"Warning: Empty response from Gemini (attempt {attempt + 1})"
                    )

            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Max retries reached. Skipping this chunk.")

        return None

    def process_chunks_directory(
        self,
        input_dir: str = "chunks",
        output_dir: str = "corrected_chunks",
        delay_seconds: int = 2,
    ) -> Dict[str, str]:
        """
        Process all chunk files in a directory.

        Args:
            input_dir (str): Directory containing chunk files
            output_dir (str): Directory to save corrected files
            delay_seconds (int): Delay between API calls to avoid rate limiting

        Returns:
            Dict[str, str]: Results summary
        """
        if not os.path.exists(input_dir):
            print(f"Error: Input directory '{input_dir}' not found.")
            return {}

        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Get all chunk files - support both raw_chunk_ and quiz_chunk_ patterns
        chunk_files = [
            f
            for f in os.listdir(input_dir)
            if (f.startswith("quiz_chunk_") or f.startswith("raw_chunk_"))
            and f.endswith(".txt")
        ]
        chunk_files.sort()

        if not chunk_files:
            print(f"No chunk files found in '{input_dir}'")
            print("Looking for files starting with 'quiz_chunk_' or 'raw_chunk_'")
            return {}

        # Determine chunk type
        raw_chunks = [f for f in chunk_files if f.startswith("raw_chunk_")]
        quiz_chunks = [f for f in chunk_files if f.startswith("quiz_chunk_")]

        if raw_chunks and quiz_chunks:
            print(
                f"Found both raw chunks ({len(raw_chunks)}) and quiz chunks ({len(quiz_chunks)})"
            )
            print("Processing all chunk types...")
        elif raw_chunks:
            print(f"Found {len(raw_chunks)} raw chunk files to process")
        else:
            print(f"Found {len(quiz_chunks)} quiz chunk files to process")

        results = {"processed": 0, "successful": 0, "failed": 0, "failed_files": []}

        # Process each chunk
        for i, chunk_file in enumerate(chunk_files, 1):
            print(f"\nProcessing {chunk_file} ({i}/{len(chunk_files)})")

            input_path = os.path.join(input_dir, chunk_file)
            output_path = os.path.join(output_dir, f"corrected_{chunk_file}")

            try:
                # Read chunk content
                with open(input_path, "r", encoding="utf-8") as f:
                    chunk_content = f.read().strip()

                if not chunk_content:
                    print(f"Warning: {chunk_file} is empty, skipping")
                    continue

                # Correct using Gemini
                print("Sending to Gemini API...")
                corrected_content = self.correct_chunk(chunk_content)

                if corrected_content:
                    # Save corrected content
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(corrected_content)

                    print(f"✓ Successfully corrected and saved to {output_path}")
                    results["successful"] += 1
                else:
                    print(f"✗ Failed to correct {chunk_file}")
                    results["failed"] += 1
                    results["failed_files"].append(chunk_file)

                results["processed"] += 1

                # Delay to avoid rate limiting
                if i < len(chunk_files):  # Don't delay after the last file
                    print(f"Waiting {delay_seconds} seconds...")
                    time.sleep(delay_seconds)

            except Exception as e:
                print(f"Error processing {chunk_file}: {str(e)}")
                results["failed"] += 1
                results["failed_files"].append(chunk_file)
                results["processed"] += 1

        # Save processing summary
        summary_path = os.path.join(output_dir, "correction_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n" + "=" * 50)
        print("CORRECTION SUMMARY")
        print("=" * 50)
        print(f"Total files processed: {results['processed']}")
        print(f"Successfully corrected: {results['successful']}")
        print(f"Failed: {results['failed']}")

        if results["failed_files"]:
            print(f"Failed files: {', '.join(results['failed_files'])}")

        print(f"Summary saved to: {summary_path}")
        print(f"Corrected files saved to: {output_dir}")

        return results

    def merge_corrected_chunks(
        self,
        corrected_dir: str = "corrected_chunks",
        output_file: str = "final_corrected_quiz_data.txt",
    ) -> bool:
        """
        Merge all corrected chunks into a single file.

        Args:
            corrected_dir (str): Directory containing corrected chunks
            output_file (str): Output file for merged content

        Returns:
            bool: Success status
        """
        try:
            if not os.path.exists(corrected_dir):
                print(f"Error: Corrected directory '{corrected_dir}' not found.")
                return False

            # Get all corrected chunk files - support both raw and quiz chunk patterns
            chunk_files = [
                f
                for f in os.listdir(corrected_dir)
                if (
                    f.startswith("corrected_quiz_chunk_")
                    or f.startswith("corrected_raw_chunk_")
                )
                and f.endswith(".txt")
            ]
            chunk_files.sort()

            if not chunk_files:
                print(f"No corrected chunk files found in '{corrected_dir}'")
                print(
                    "Looking for files starting with 'corrected_quiz_chunk_' or 'corrected_raw_chunk_'"
                )
                return False

            merged_content = []

            for chunk_file in chunk_files:
                chunk_path = os.path.join(corrected_dir, chunk_file)
                with open(chunk_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        merged_content.append(content)

            # Write merged content
            final_content = "\n\n".join(merged_content)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_content)

            # Count Q&A pairs
            qa_pairs = final_content.split("\n\n")
            qa_pairs = [pair.strip() for pair in qa_pairs if pair.strip()]

            print(f"✓ Merged {len(chunk_files)} corrected chunks")
            print(f"✓ Total Q&A pairs in final file: {len(qa_pairs)}")
            print(f"✓ Final corrected file saved to: {output_file}")

            return True

        except Exception as e:
            print(f"Error merging corrected chunks: {str(e)}")
            return False


def main():
    print("Gemini Quiz Corrector")
    print("=" * 20)

    # Get API key
    api_key = input("Enter your Google Gemini API key: ").strip()

    if not api_key:
        print("Error: API key is required.")
        return

    try:
        corrector = GeminiCorrector(api_key)

        # Get settings with better defaults for raw chunks
        input_dir = (
            input("Enter input directory (default: raw_chunks): ").strip()
            or "raw_chunks"
        )
        output_dir = (
            input("Enter output directory (default: corrected_chunks): ").strip()
            or "corrected_chunks"
        )

        try:
            delay = int(
                input("Enter delay between API calls in seconds (default: 2): ").strip()
                or "2"
            )
        except ValueError:
            delay = 2

        # Process chunks
        print(f"\nStarting correction process...")
        results = corrector.process_chunks_directory(input_dir, output_dir, delay)

        if results and results["successful"] > 0:
            # Automatically merge corrected chunks
            print("\nAutomatically merging corrected chunks...")
            output_file = "final_corrected_quiz_data.txt"
            success = corrector.merge_corrected_chunks(output_dir, output_file)

            if success:
                print(f"✓ Final merged file created: {output_file}")
            else:
                print(
                    "✗ Failed to merge chunks, but individual corrected files are available"
                )
        else:
            print("No successful corrections to merge.")

        print("\n✓ Process completed!")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your API key and try again.")


if __name__ == "__main__":
    main()
