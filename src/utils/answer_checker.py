import os
import re
import json
from typing import List, Dict, Set


class AnswerChecker:
    def __init__(self):
        """Initialize the answer checker."""
        self.valid_answers = {"A", "B", "C", "D", "E"}
        self.placeholder_patterns = [
            r"\(missing option\)",
            r"\(missing\)",
            r"\(placeholder\)",
            r"\(todo\)",
            r"\(fix\)",
            r"\(check\)",
            r"\(unknown\)",
            r"\(tbd\)",
            r"\(to be determined\)",
            r"missing option",
            r"placeholder",
            r"todo",
            r"fix",
            r"check answer",
            r"unknown",
            r"tbd",
        ]
        self.problems = []

    def parse_qa_file(self, file_path: str) -> List[Dict]:
        """
        Parse Q&A pairs from file and check for answer issues.

        Args:
            file_path (str): Path to the quiz file

        Returns:
            List[Dict]: List of Q&A pairs with issue flags
        """
        qa_pairs = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Split by double newlines to get individual Q&A pairs
            pairs = content.split("\n\n")

            for i, pair in enumerate(pairs):
                pair = pair.strip()
                if not pair:
                    continue

                lines = pair.split("\n")
                if len(lines) < 5:  # Question + 4 options minimum
                    continue

                question = lines[0].strip()
                options = []
                answer = None
                answer_line = None

                # Parse options and find answer
                for line_idx, line in enumerate(lines[1:], 1):
                    line = line.strip()
                    if line.startswith(("A.", "B.", "C.", "D.", "E.")):
                        if ";;" in line:
                            # Answer is in this line
                            parts = line.split(";;")
                            options.append(parts[0].strip())
                            answer = parts[1].strip()
                            answer_line = line_idx
                        else:
                            options.append(line)
                    elif ";;" in line and answer is None:
                        # Answer is on separate line
                        answer = line.replace(";;", "").strip()
                        answer_line = line_idx

                # Check for issues
                issues = self.check_answer_issues(question, options, answer, i)

                qa_pairs.append(
                    {
                        "index": i,
                        "question": question,
                        "options": options,
                        "answer": answer,
                        "answer_line": answer_line,
                        "full_text": pair,
                        "issues": issues,
                    }
                )

        except Exception as e:
            print(f"Error parsing file {file_path}: {str(e)}")

        return qa_pairs

    def check_answer_issues(
        self, question: str, options: List[str], answer: str, index: int
    ) -> List[str]:
        """
        Check for various answer-related issues.

        Args:
            question (str): The question text
            options (List[str]): List of options
            answer (str): The answer
            index (int): Question index

        Returns:
            List[str]: List of issues found
        """
        issues = []

        # Check if answer is missing
        if not answer or answer.strip() == "":
            issues.append("Missing answer")

        # Check if answer is just a question mark
        elif answer.strip() == "?":
            issues.append("Answer is question mark")

        # Check for placeholder answers
        elif self.is_placeholder_answer(answer):
            issues.append(f"Placeholder answer: '{answer}'")

        # Check for valid single letter answers
        elif len(answer.strip()) == 1:
            if answer.strip().upper() not in self.valid_answers:
                issues.append(f"Invalid answer format: '{answer}'")
            elif answer.strip().upper() not in [opt[0] for opt in options if opt]:
                issues.append(f"Answer '{answer}' doesn't match available options")

        # Check for actual multi-answer format (multiple letters without explanation)
        elif self.is_multi_answer(answer):
            # Multi-answer like "A B C" or "A (Tự giác) B (Tích cực) C (Sáng tạo)"
            answers = re.findall(r"([A-E])", answer.upper())
            if not answers:
                issues.append(f"No valid answers found in multi-answer: '{answer}'")
            else:
                for ans in answers:
                    if ans not in [opt[0] for opt in options if opt]:
                        issues.append(
                            f"Multi-answer '{ans}' doesn't match available options"
                        )

        # Check for single answer with explanation in parentheses
        elif "(" in answer and ")" in answer:
            # Extract the main answer (letter before parentheses)
            main_answer = re.match(r"^([A-E])", answer.upper())
            if main_answer:
                ans_letter = main_answer.group(1)
                if ans_letter not in [opt[0] for opt in options if opt]:
                    issues.append(
                        f"Answer '{ans_letter}' doesn't match available options"
                    )
            else:
                issues.append(
                    f"Answer with explanation doesn't start with valid option: '{answer}'"
                )

        # Check for other unusual formats
        else:
            if len(answer.strip()) > 10:
                issues.append(f"Unusually long answer: '{answer[:20]}...'")
            elif not re.match(r"^[A-E]", answer.upper()):
                issues.append(f"Answer doesn't start with valid option: '{answer}'")

        # Check if we have enough options
        if len(options) < 4:
            issues.append(f"Only {len(options)} options found, expected at least 4")

        # Check for malformed options
        for i, option in enumerate(options):
            if not option.startswith(("A.", "B.", "C.", "D.", "E.")):
                issues.append(
                    f"Option {i + 1} doesn't start with letter: '{option[:30]}...'"
                )

        # Check for placeholder options like "D. (Missing Option)"
        for i, option in enumerate(options):
            if self.has_placeholder_option(option):
                issues.append(f"Option {chr(65 + i)} has placeholder: '{option}'")

        return issues

    def is_placeholder_answer(self, answer: str) -> bool:
        """
        Check if the answer is a placeholder.

        Args:
            answer (str): The answer to check

        Returns:
            bool: True if it's a placeholder answer
        """
        if not answer:
            return False

        answer_lower = answer.lower().strip()

        # Check against known placeholder patterns
        for pattern in self.placeholder_patterns:
            if re.search(pattern, answer_lower, re.IGNORECASE):
                return True

        return False

    def has_placeholder_option(self, option: str) -> bool:
        """
        Check if an option contains placeholder text like "(Missing Option)".

        Args:
            option (str): The option to check

        Returns:
            bool: True if it contains placeholder text
        """
        if not option:
            return False

        option_lower = option.lower()

        # Check for placeholder patterns in options
        for pattern in self.placeholder_patterns:
            if re.search(pattern, option_lower, re.IGNORECASE):
                return True

        return False

    def generate_report(self, file_path: str, output_file: str = None) -> Dict:
        """
        Generate a comprehensive answer check report.

        Args:
            file_path (str): Path to the quiz file
            output_file (str): Path to save the report (optional)

        Returns:
            Dict: Report summary
        """
        print(f"Checking answers in: {file_path}")

        # Parse Q&A pairs
        qa_pairs = self.parse_qa_file(file_path)
        total_questions = len(qa_pairs)

        print(f"Found {total_questions} Q&A pairs")

        if total_questions == 0:
            return {"error": "No valid Q&A pairs found"}

        # Categorize issues
        missing_answers = []
        question_mark_answers = []
        placeholder_answers = []
        placeholder_options = []
        invalid_formats = []
        multi_answers = []
        malformed_options = []
        other_issues = []

        for qa in qa_pairs:
            if qa["issues"]:
                for issue in qa["issues"]:
                    if "Missing answer" in issue:
                        missing_answers.append(qa)
                    elif "question mark" in issue:
                        question_mark_answers.append(qa)
                    elif "Placeholder answer" in issue:
                        placeholder_answers.append(qa)
                    elif "has placeholder" in issue:
                        placeholder_options.append(qa)
                    elif "Invalid answer format" in issue:
                        invalid_formats.append(qa)
                    elif "Multi-answer" in issue or "multi-answer" in issue:
                        multi_answers.append(qa)
                    elif (
                        "options found" in issue or "doesn't start with letter" in issue
                    ):
                        malformed_options.append(qa)
                    else:
                        other_issues.append(qa)

        # Calculate statistics
        questions_with_issues = len([qa for qa in qa_pairs if qa["issues"]])
        questions_without_issues = total_questions - questions_with_issues

        # Create report
        report = {
            "file_analyzed": file_path,
            "total_questions": total_questions,
            "questions_without_issues": questions_without_issues,
            "questions_with_issues": questions_with_issues,
            "issue_breakdown": {
                "missing_answers": {
                    "count": len(missing_answers),
                    "questions": missing_answers[:10],  # Show first 10
                },
                "question_mark_answers": {
                    "count": len(question_mark_answers),
                    "questions": question_mark_answers[:10],
                },
                "placeholder_answers": {
                    "count": len(placeholder_answers),
                    "questions": placeholder_answers[:10],
                },
                "placeholder_options": {
                    "count": len(placeholder_options),
                    "questions": placeholder_options[:10],
                },
                "invalid_formats": {
                    "count": len(invalid_formats),
                    "questions": invalid_formats[:10],
                },
                "multi_answers": {
                    "count": len(multi_answers),
                    "questions": multi_answers[:10],
                },
                "malformed_options": {
                    "count": len(malformed_options),
                    "questions": malformed_options[:10],
                },
                "other_issues": {
                    "count": len(other_issues),
                    "questions": other_issues[:10],
                },
            },
        }

        # Print summary
        self.print_summary(report)

        # Save report if requested
        if output_file:
            self.save_report(report, output_file)

        return report

    def print_summary(self, report: Dict):
        """
        Print a summary of the answer check results.

        Args:
            report (Dict): Report data
        """
        print("\n" + "=" * 60)
        print("ANSWER CHECK SUMMARY")
        print("=" * 60)

        total = report["total_questions"]
        good = report["questions_without_issues"]
        issues = report["questions_with_issues"]

        print(f"Total questions: {total}")
        print(f"Questions without issues: {good} ({good / total * 100:.1f}%)")
        print(f"Questions with issues: {issues} ({issues / total * 100:.1f}%)")

        print("\nISSUE BREAKDOWN:")
        breakdown = report["issue_breakdown"]

        for issue_type, data in breakdown.items():
            count = data["count"]
            if count > 0:
                issue_name = issue_type.replace("_", " ").title()
                print(f"  {issue_name}: {count} questions")

                # Show a few examples
                if data["questions"]:
                    print(f"    Examples:")
                    for i, qa in enumerate(data["questions"][:3]):
                        print(f"      {qa['index']}: {qa['question'][:50]}...")
                        if qa["answer"]:
                            print(f"         Answer: '{qa['answer']}'")
                        for issue in qa["issues"]:
                            print(f"         Issue: {issue}")
                        print()

        print("=" * 60)

    def save_report(self, report: Dict, output_file: str):
        """
        Save the report to a JSON file.

        Args:
            report (Dict): Report data
            output_file (str): Output file path
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Detailed report saved to: {output_file}")
        except Exception as e:
            print(f"Error saving report: {str(e)}")

    def fix_missing_answers(self, file_path: str, output_file: str):
        """
        Create a file highlighting questions with missing answers.

        Args:
            file_path (str): Input file path
            output_file (str): Output file path
        """
        qa_pairs = self.parse_qa_file(file_path)

        missing_answer_questions = []
        for qa in qa_pairs:
            if any("Missing answer" in issue for issue in qa["issues"]):
                missing_answer_questions.append(qa)

        if not missing_answer_questions:
            print("No questions with missing answers found.")
            return

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("QUESTIONS WITH MISSING ANSWERS\n")
                f.write("=" * 50 + "\n\n")

                for qa in missing_answer_questions:
                    f.write(f"Question {qa['index']}:\n")
                    f.write(qa["full_text"])
                    f.write("\n\n" + "-" * 30 + "\n\n")

            print(
                f"✓ {len(missing_answer_questions)} questions with missing answers saved to: {output_file}"
            )

        except Exception as e:
            print(f"Error saving missing answers file: {str(e)}")

    def fix_placeholder_options(self, file_path: str, output_file: str):
        """
        Create a fixed file by removing placeholder options like "(Missing Option)".

        Args:
            file_path (str): Input file path
            output_file (str): Output file path
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            pairs = content.split("\n\n")
            fixed_pairs = []
            fixed_count = 0

            for pair in pairs:
                if not pair.strip():
                    continue

                lines = pair.strip().split("\n")
                if len(lines) < 5:  # Need question + 4 options minimum
                    fixed_pairs.append(pair)
                    continue

                question = lines[0]
                fixed_options = []
                current_answer = None

                # Process each line
                for line in lines[1:]:
                    if ";;" in line:
                        # This line contains the answer
                        parts = line.split(";;")
                        option_part = parts[0].strip()
                        current_answer = parts[1].strip()

                        # Check if this option has placeholder
                        if self.has_placeholder_option(option_part):
                            # Remove this option, save the answer for later
                            fixed_count += 1
                            print(f"Removing placeholder option: {option_part}")
                        else:
                            # Keep this option with answer
                            fixed_options.append(line)
                    else:
                        # Regular option line
                        if self.has_placeholder_option(line):
                            # Skip this placeholder option
                            fixed_count += 1
                            print(f"Removing placeholder option: {line}")
                        else:
                            fixed_options.append(line)

                # If we have an answer but no option contains it, attach to last option
                if current_answer and not any(";;" in opt for opt in fixed_options):
                    if fixed_options:
                        # Attach answer to the last option
                        last_option = fixed_options[-1]
                        fixed_options[-1] = f"{last_option};;{current_answer}"

                # Reconstruct the question
                fixed_question = [question] + fixed_options
                fixed_pairs.append("\n".join(fixed_question))

            # Write fixed content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n\n".join(fixed_pairs))

            print(f"✓ Fixed {fixed_count} placeholder options")
            print(f"✓ Fixed file saved to: {output_file}")

        except Exception as e:
            print(f"Error fixing placeholder options: {str(e)}")

    def is_multi_answer(self, answer: str) -> bool:
        """
        Check if the answer is actually a multi-answer format.

        Args:
            answer (str): The answer to check

        Returns:
            bool: True if it's a genuine multi-answer (multiple separate letters)
        """
        if not answer:
            return False

        # Extract all letter answers
        letters = re.findall(r"([A-E])", answer.upper())

        # If there's only one letter, it's not multi-answer
        if len(letters) <= 1:
            return False

        # Check if letters are spread across the text (multi-answer pattern)
        # vs single letter with explanation
        answer_upper = answer.upper()
        first_letter_pos = answer_upper.find(letters[0])

        # If first letter is at the beginning and followed by explanation in parentheses,
        # it's likely a single answer with explanation
        if first_letter_pos == 0 and "(" in answer:
            # Check if other letters are just part of the explanation text
            explanation_part = answer[answer.find("(") :]
            other_letters_in_explanation = [
                l for l in letters[1:] if l in explanation_part.upper()
            ]

            # If all other letters are just in the explanation, it's not multi-answer
            if len(other_letters_in_explanation) == len(letters) - 1:
                return False

        # Look for pattern like "A B C" or "A (something) B (something) C (something)"
        # where letters are intentionally separated
        letter_pattern = r"([A-E])\s*(?:\([^)]*\))?\s*([A-E])"
        if re.search(letter_pattern, answer.upper()):
            return True

        return False


def main():
    print("Quiz Answer Checker")
    print("=" * 19)

    # Get input file
    input_file = input(
        "Enter quiz file path (default: final_corrected_quiz_data.txt): "
    ).strip()
    if not input_file:
        input_file = "final_corrected_quiz_data.txt"

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    # Initialize checker
    checker = AnswerChecker()

    # Generate report
    report_file = (
        f"answer_check_report_{os.path.splitext(os.path.basename(input_file))[0]}.json"
    )
    report = checker.generate_report(input_file, report_file)

    if "error" in report:
        print(f"Error: {report['error']}")
        return

    # Ask about creating missing answers file
    if report["issue_breakdown"]["missing_answers"]["count"] > 0:
        create_missing = (
            input("\nCreate file with missing answer questions? (y/n): ")
            .strip()
            .lower()
        )
        if create_missing == "y":
            missing_file = f"missing_answers_{os.path.basename(input_file)}"
            checker.fix_missing_answers(input_file, missing_file)

    # Ask about fixing placeholder options
    placeholder_options_count = report["issue_breakdown"]["placeholder_options"][
        "count"
    ]
    if placeholder_options_count > 0:
        fix_placeholders = (
            input(
                f"\nFix {placeholder_options_count} questions with placeholder options like '(Missing Option)'? (y/n): "
            )
            .strip()
            .lower()
        )
        if fix_placeholders == "y":
            fixed_file = f"fixed_placeholder_options_{os.path.basename(input_file)}"
            checker.fix_placeholder_options(input_file, fixed_file)


if __name__ == "__main__":
    main()
