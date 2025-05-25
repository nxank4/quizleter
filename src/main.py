import os
import sys
import time
from pathlib import Path

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from src.utils.split_chunks import split_raw_text_data
from src.utils.gemini_corrector import GeminiCorrector
from src.utils.manual_merge import merge_corrected_chunks
from src.utils.answer_checker import AnswerChecker
from src.utils.duplicate_checker import QuizDuplicateChecker


class QuizProcessingWorkflow:
    def __init__(self):
        """Initialize the workflow processor."""
        self.steps_completed = 0
        self.total_steps = 7

    def print_step(self, step_num: int, title: str, description: str = ""):
        """Print a formatted step header."""
        print("\n" + "=" * 80)
        print(f"STEP {step_num}/{self.total_steps}: {title.upper()}")
        if description:
            print(f"Description: {description}")
        print("=" * 80)

    def print_progress(self, message: str):
        """Print a progress message."""
        print(f"📊 {message}")

    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")

    def step1_extract_pdf(
        self, pdf_file: str, raw_output: str = "raw_extracted_text.txt"
    ) -> bool:
        """
        Step 1: Extract raw text from PDF file.

        Args:
            pdf_file (str): Path to the PDF file
            raw_output (str): Output file for raw text

        Returns:
            bool: Success status
        """
        self.print_step(1, "PDF Text Extraction", "Extract raw text from PDF file")

        if not os.path.exists(pdf_file):
            self.print_error(f"PDF file not found: {pdf_file}")
            return False

        try:
            # Try to import PyMuPDF for PDF processing
            import fitz

            self.print_progress("Opening PDF file...")
            doc = fitz.open(pdf_file)

            text_content = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    text_content.append(text)
                self.print_progress(f"Processed page {page_num + 1}/{len(doc)}")

            doc.close()

            # Save raw text
            with open(raw_output, "w", encoding="utf-8") as f:
                f.write("\n\n".join(text_content))

            self.print_success(f"Raw text extracted to: {raw_output}")
            self.print_progress(f"Total pages processed: {len(doc)}")
            return True

        except ImportError:
            self.print_error(
                "PyMuPDF not installed. Please install with: pip install pymupdf"
            )
            return False
        except Exception as e:
            self.print_error(f"Failed to extract PDF: {str(e)}")
            return False

    def step2_split_chunks(
        self,
        raw_file: str = "raw_extracted_text.txt",
        chunk_size: int = 30,
        output_dir: str = "raw_chunks",
    ) -> bool:
        """
        Step 2: Split raw text into manageable chunks.

        Args:
            raw_file (str): Raw text file to split
            chunk_size (int): Target questions per chunk
            output_dir (str): Directory for chunk files

        Returns:
            bool: Success status
        """
        self.print_step(
            2,
            "Split into Chunks",
            f"Split raw text into chunks of ~{chunk_size} questions",
        )

        if not os.path.exists(raw_file):
            self.print_error(f"Raw text file not found: {raw_file}")
            return False

        try:
            split_raw_text_data(raw_file, chunk_size, output_dir)

            # Count created chunks
            if os.path.exists(output_dir):
                chunk_files = [
                    f
                    for f in os.listdir(output_dir)
                    if f.startswith("raw_chunk_") and f.endswith(".txt")
                ]
                self.print_success(
                    f"Created {len(chunk_files)} chunks in: {output_dir}"
                )
                return True
            else:
                self.print_error("Failed to create chunks directory")
                return False

        except Exception as e:
            self.print_error(f"Failed to split chunks: {str(e)}")
            return False

    def step3_gemini_correction(
        self,
        api_key: str,
        input_dir: str = "raw_chunks",
        output_dir: str = "corrected_chunks",
    ) -> bool:
        """
        Step 3: Process chunks with Gemini API for correction.

        Args:
            api_key (str): Google Gemini API key
            input_dir (str): Directory containing raw chunks
            output_dir (str): Directory for corrected chunks

        Returns:
            bool: Success status
        """
        self.print_step(
            3,
            "Gemini AI Correction",
            "Process raw chunks with Gemini AI for formatting and correction",
        )

        if not api_key:
            self.print_error("Gemini API key is required")
            return False

        if not os.path.exists(input_dir):
            self.print_error(f"Input directory not found: {input_dir}")
            return False

        try:
            corrector = GeminiCorrector(api_key)
            results = corrector.process_chunks_directory(
                input_dir, output_dir, delay_seconds=2
            )

            if results and results.get("successful", 0) > 0:
                self.print_success(
                    f"Successfully corrected {results['successful']}/{results['processed']} chunks"
                )
                if results.get("failed", 0) > 0:
                    self.print_warning(f"Failed to correct {results['failed']} chunks")
                return True
            else:
                self.print_error("No chunks were successfully corrected")
                return False

        except Exception as e:
            self.print_error(f"Gemini correction failed: {str(e)}")
            return False

    def step4_merge_chunks(
        self,
        corrected_dir: str = "corrected_chunks",
        output_file: str = "final_corrected_quiz_data.txt",
    ) -> bool:
        """
        Step 4: Merge corrected chunks into a single file.

        Args:
            corrected_dir (str): Directory containing corrected chunks
            output_file (str): Output file for merged content

        Returns:
            bool: Success status
        """
        self.print_step(
            4,
            "Merge Corrected Chunks",
            "Combine all corrected chunks into a single file",
        )

        try:
            success = merge_corrected_chunks(corrected_dir, output_file)

            if success:
                # Count Q&A pairs
                if os.path.exists(output_file):
                    with open(output_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    qa_count = len(
                        [pair for pair in content.split("\n\n") if pair.strip()]
                    )
                    self.print_success(f"Merged chunks into: {output_file}")
                    self.print_progress(f"Total Q&A pairs: {qa_count}")
                return success
            else:
                self.print_error("Failed to merge corrected chunks")
                return False

        except Exception as e:
            self.print_error(f"Merge failed: {str(e)}")
            return False

    def step5_answer_checking(
        self, input_file: str = "final_corrected_quiz_data.txt"
    ) -> bool:
        """
        Step 5: Check and validate answers in the merged file.

        Args:
            input_file (str): File to check for answer issues

        Returns:
            bool: Success status
        """
        self.print_step(
            5,
            "Answer Validation",
            "Check for missing answers, formatting issues, and placeholder content",
        )

        if not os.path.exists(input_file):
            self.print_error(f"Input file not found: {input_file}")
            return False

        try:
            checker = AnswerChecker()
            report_file = f"answer_check_report_{os.path.splitext(os.path.basename(input_file))[0]}.json"

            report = checker.generate_report(input_file, report_file)

            if "error" in report:
                self.print_error(f"Answer checking failed: {report['error']}")
                return False

            total = report["total_questions"]
            issues = report["questions_with_issues"]
            good = report["questions_without_issues"]

            self.print_success(
                f"Answer validation completed: {good}/{total} questions OK"
            )

            if issues > 0:
                self.print_warning(f"Found {issues} questions with issues")

                # Auto-fix placeholder options if found
                placeholder_count = report["issue_breakdown"]["placeholder_options"][
                    "count"
                ]
                if placeholder_count > 0:
                    self.print_progress(
                        f"Auto-fixing {placeholder_count} placeholder options..."
                    )
                    fixed_file = (
                        f"fixed_placeholder_options_{os.path.basename(input_file)}"
                    )
                    checker.fix_placeholder_options(input_file, fixed_file)
                    self.print_success(f"Fixed file saved as: {fixed_file}")

            return True

        except Exception as e:
            self.print_error(f"Answer checking failed: {str(e)}")
            return False

    def step6_duplicate_checking(
        self,
        input_file: str = "final_corrected_quiz_data.txt",
        similarity_threshold: float = 0.8,
    ) -> bool:
        """
        Step 6: Check for duplicate questions and similar content.

        Args:
            input_file (str): File to check for duplicates
            similarity_threshold (float): Threshold for similarity detection

        Returns:
            bool: Success status
        """
        self.print_step(
            6,
            "Duplicate Detection",
            f"Find duplicate and similar questions (threshold: {similarity_threshold})",
        )

        if not os.path.exists(input_file):
            self.print_error(f"Input file not found: {input_file}")
            return False

        try:
            checker = QuizDuplicateChecker(similarity_threshold=similarity_threshold)
            report_file = f"duplicate_report_{os.path.splitext(os.path.basename(input_file))[0]}.json"

            report = checker.generate_report(input_file, report_file)

            if "error" in report:
                self.print_error(f"Duplicate checking failed: {report['error']}")
                return False

            total = report["total_questions"]
            exact_dupes = report["exact_duplicates"]["count"]
            similar_groups = report["similar_questions"]["count"]

            self.print_success(f"Duplicate detection completed on {total} questions")

            if exact_dupes > 0:
                self.print_warning(f"Found {exact_dupes} exact duplicate groups")

                # Auto-create cleaned file
                self.print_progress(
                    "Auto-creating cleaned file without exact duplicates..."
                )
                cleaned_file = f"cleaned_{os.path.basename(input_file)}"
                checker.create_cleaned_file(
                    input_file, cleaned_file, remove_exact_duplicates=True
                )
                self.print_success(f"Cleaned file saved as: {cleaned_file}")

            if similar_groups > 0:
                self.print_warning(
                    f"Found {similar_groups} groups of similar questions"
                )

            return True

        except Exception as e:
            self.print_error(f"Duplicate checking failed: {str(e)}")
            return False

    def step7_finalize(self, base_file: str = "final_corrected_quiz_data.txt") -> str:
        """
        Step 7: Determine the final output file and provide completion summary.

        Args:
            base_file (str): Base filename to check for variations

        Returns:
            str: Path to the final recommended file
        """
        self.print_step(
            7, "Finalization", "Determine final output file and provide summary"
        )

        # Check for different versions of the file
        possible_files = [
            f"cleaned_fixed_placeholder_options_{base_file}",
            f"cleaned_{base_file}",
            f"fixed_placeholder_options_{base_file}",
            base_file,
        ]

        final_file = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                final_file = file_path
                break

        if final_file:
            # Get final stats
            with open(final_file, "r", encoding="utf-8") as f:
                content = f.read()

            qa_pairs = [pair.strip() for pair in content.split("\n\n") if pair.strip()]

            self.print_success("Quiz processing workflow completed successfully!")
            print("\n📈 FINAL SUMMARY:")
            print(f"   📄 Final file: {final_file}")
            print(f"   📊 Total questions: {len(qa_pairs)}")
            print(f"   🔧 Applied corrections and formatting")
            print(f"   ✅ Validated answers and removed duplicates")

            return final_file
        else:
            self.print_error("No final output file found")
            return ""

    def run_full_workflow(
        self,
        pdf_file: str,
        api_key: str,
        chunk_size: int = 30,
        similarity_threshold: float = 0.8,
    ) -> str:
        """
        Run the complete quiz processing workflow.

        Args:
            pdf_file (str): Path to input PDF file
            api_key (str): Google Gemini API key
            chunk_size (int): Target questions per chunk
            similarity_threshold (float): Similarity threshold for duplicate detection

        Returns:
            str: Path to final output file, empty string if failed
        """
        print("🚀 STARTING QUIZ PROCESSING WORKFLOW")
        print(f"Input PDF: {pdf_file}")
        print(f"Chunk size: {chunk_size} questions")
        print(f"Similarity threshold: {similarity_threshold}")

        start_time = time.time()

        # Step 1: Extract PDF
        if not self.step1_extract_pdf(pdf_file):
            return ""

        # Step 2: Split chunks
        if not self.step2_split_chunks(chunk_size=chunk_size):
            return ""

        # Step 3: Gemini correction
        if not self.step3_gemini_correction(api_key):
            return ""

        # Step 4: Merge chunks
        if not self.step4_merge_chunks():
            return ""

        # Step 5: Answer checking
        if not self.step5_answer_checking():
            return ""

        # Step 6: Duplicate checking
        if not self.step6_duplicate_checking(similarity_threshold=similarity_threshold):
            return ""

        # Step 7: Finalize
        final_file = self.step7_finalize()

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"\n⏱️  Total processing time: {processing_time:.1f} seconds")
        print("🎉 Workflow completed successfully!")

        return final_file


def main():
    """Main function to run the quiz processing workflow."""
    print("Quiz Processing Workflow")
    print("=" * 24)

    # Get inputs
    pdf_file = input("Enter PDF file path: ").strip()
    if not pdf_file:
        print("Error: PDF file path is required.")
        return

    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found.")
        return

    api_key = input("Enter Google Gemini API key: ").strip()
    if not api_key:
        print("Error: Gemini API key is required.")
        return

    # Optional parameters
    try:
        chunk_size = int(input("Enter chunk size (default: 30): ").strip() or "30")
    except ValueError:
        chunk_size = 30

    try:
        similarity_threshold = float(
            input("Enter similarity threshold (default: 0.8): ").strip() or "0.8"
        )
    except ValueError:
        similarity_threshold = 0.8

    # Run workflow
    workflow = QuizProcessingWorkflow()
    final_file = workflow.run_full_workflow(
        pdf_file, api_key, chunk_size, similarity_threshold
    )

    if final_file:
        print(f"\n✨ SUCCESS! Final file created: {final_file}")
        print("\nYou can now use this file for your quiz/study needs!")
    else:
        print("\n💥 FAILED! Workflow did not complete successfully.")
        print("Check the error messages above for details.")


if __name__ == "__main__":
    main()
