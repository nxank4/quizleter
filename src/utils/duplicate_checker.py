import os
import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Set
import json


class QuizDuplicateChecker:
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the duplicate checker.

        Args:
            similarity_threshold (float): Threshold for considering two questions similar (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.qa_pairs = []
        self.duplicates = []

    def clean_text(self, text: str) -> str:
        """
        Clean text for better comparison.

        Args:
            text (str): Text to clean

        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", text.strip())
        # Remove punctuation for comparison
        text = re.sub(r"[^\w\s]", "", text)
        # Convert to lowercase
        text = text.lower()
        return text

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        return SequenceMatcher(
            None, self.clean_text(text1), self.clean_text(text2)
        ).ratio()

    def parse_qa_file(self, file_path: str) -> List[Dict]:
        """
        Parse Q&A pairs from file.

        Args:
            file_path (str): Path to the quiz file

        Returns:
            List[Dict]: List of Q&A pairs
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

                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith(("A.", "B.", "C.", "D.", "E.")):
                        if ";;" in line:
                            # Answer is in this line
                            parts = line.split(";;")
                            options.append(parts[0].strip())
                            answer = parts[1].strip()
                        else:
                            options.append(line)
                    elif ";;" in line and answer is None:
                        # Answer is on separate line
                        answer = line.replace(";;", "").strip()

                if question and len(options) >= 4:
                    qa_pairs.append(
                        {
                            "index": i,
                            "question": question,
                            "options": options,
                            "answer": answer or "?",
                            "full_text": pair,
                        }
                    )

        except Exception as e:
            print(f"Error parsing file {file_path}: {str(e)}")

        return qa_pairs

    def find_similar_questions(self, qa_pairs: List[Dict]) -> List[Dict]:
        """
        Find similar questions in the Q&A pairs.

        Args:
            qa_pairs (List[Dict]): List of Q&A pairs

        Returns:
            List[Dict]: List of similar question groups
        """
        similar_groups = []
        processed_indices = set()

        for i, qa1 in enumerate(qa_pairs):
            if i in processed_indices:
                continue

            similar_questions = [qa1]
            processed_indices.add(i)

            for j, qa2 in enumerate(qa_pairs[i + 1 :], i + 1):
                if j in processed_indices:
                    continue

                similarity = self.calculate_similarity(qa1["question"], qa2["question"])

                if similarity >= self.similarity_threshold:
                    similar_questions.append(qa2)
                    processed_indices.add(j)

            # Only add groups with more than one question
            if len(similar_questions) > 1:
                similar_groups.append(
                    {
                        "group_id": len(similar_groups) + 1,
                        "count": len(similar_questions),
                        "questions": similar_questions,
                        "similarities": [
                            self.calculate_similarity(
                                similar_questions[0]["question"], q["question"]
                            )
                            for q in similar_questions[1:]
                        ],
                    }
                )

        return similar_groups

    def find_exact_duplicates(self, qa_pairs: List[Dict]) -> List[Dict]:
        """
        Find exact duplicate questions.

        Args:
            qa_pairs (List[Dict]): List of Q&A pairs

        Returns:
            List[Dict]: List of exact duplicate groups
        """
        exact_groups = []
        seen_questions = {}

        for qa in qa_pairs:
            clean_question = self.clean_text(qa["question"])

            if clean_question in seen_questions:
                # Found duplicate
                existing_group = seen_questions[clean_question]
                existing_group["questions"].append(qa)
                existing_group["count"] += 1
            else:
                # New question
                group = {
                    "group_id": len(exact_groups) + 1,
                    "count": 1,
                    "questions": [qa],
                    "clean_question": clean_question,
                }
                seen_questions[clean_question] = group

        # Return only groups with duplicates
        return [group for group in seen_questions.values() if group["count"] > 1]

    def check_answer_consistency(self, similar_groups: List[Dict]) -> List[Dict]:
        """
        Check if similar questions have consistent answers.

        Args:
            similar_groups (List[Dict]): Groups of similar questions

        Returns:
            List[Dict]: Groups with answer inconsistencies
        """
        inconsistent_groups = []

        for group in similar_groups:
            answers = [q["answer"] for q in group["questions"]]
            unique_answers = set(answers)

            if len(unique_answers) > 1:
                group["answer_inconsistency"] = True
                group["different_answers"] = list(unique_answers)
                inconsistent_groups.append(group)
            else:
                group["answer_inconsistency"] = False

        return inconsistent_groups

    def generate_report(self, file_path: str, output_file: str = None) -> Dict:
        """
        Generate a comprehensive duplicate check report.

        Args:
            file_path (str): Path to the quiz file
            output_file (str): Path to save the report (optional)

        Returns:
            Dict: Report summary
        """
        print(f"Analyzing quiz file: {file_path}")

        # Parse Q&A pairs
        qa_pairs = self.parse_qa_file(file_path)
        total_questions = len(qa_pairs)

        print(f"Found {total_questions} Q&A pairs")

        if total_questions == 0:
            return {"error": "No valid Q&A pairs found"}

        # Find exact duplicates
        exact_duplicates = self.find_exact_duplicates(qa_pairs)

        # Find similar questions
        similar_groups = self.find_similar_questions(qa_pairs)

        # Check answer consistency
        inconsistent_groups = self.check_answer_consistency(similar_groups)

        # Create report
        report = {
            "file_analyzed": file_path,
            "total_questions": total_questions,
            "similarity_threshold": self.similarity_threshold,
            "exact_duplicates": {
                "count": len(exact_duplicates),
                "affected_questions": sum(group["count"] for group in exact_duplicates),
                "groups": exact_duplicates,
            },
            "similar_questions": {
                "count": len(similar_groups),
                "affected_questions": sum(group["count"] for group in similar_groups),
                "groups": similar_groups,
            },
            "answer_inconsistencies": {
                "count": len(inconsistent_groups),
                "groups": inconsistent_groups,
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
        Print a summary of the duplicate check results.

        Args:
            report (Dict): Report data
        """
        print("\n" + "=" * 60)
        print("DUPLICATE CHECK SUMMARY")
        print("=" * 60)

        print(f"Total questions analyzed: {report['total_questions']}")
        print(f"Similarity threshold: {report['similarity_threshold']}")

        # Exact duplicates
        exact = report["exact_duplicates"]
        print(
            f"\nExact duplicates: {exact['count']} groups affecting {exact['affected_questions']} questions"
        )

        if exact["groups"]:
            print("\nExact duplicate groups:")
            for group in exact["groups"][:3]:  # Show first 3 groups
                print(
                    f"  Group {group['group_id']}: {group['count']} identical questions"
                )
                print(f"    Question: {group['questions'][0]['question'][:80]}...")

        # Similar questions
        similar = report["similar_questions"]
        print(
            f"\nSimilar questions: {similar['count']} groups affecting {similar['affected_questions']} questions"
        )

        if similar["groups"]:
            print("\nTop similar question groups:")
            for group in similar["groups"][:3]:  # Show first 3 groups
                print(
                    f"  Group {group['group_id']}: {group['count']} similar questions"
                )
                print(f"    Question: {group['questions'][0]['question'][:80]}...")
                if group["similarities"]:
                    print(f"    Max similarity: {max(group['similarities']):.2f}")

        # Answer inconsistencies
        inconsistent = report["answer_inconsistencies"]
        if inconsistent["count"] > 0:
            print(f"\n⚠️  Answer inconsistencies: {inconsistent['count']} groups")
            for group in inconsistent["groups"][:3]:
                print(
                    f"  Group {group['group_id']}: Different answers {group['different_answers']}"
                )

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

    def create_cleaned_file(
        self, file_path: str, output_file: str, remove_exact_duplicates: bool = True
    ):
        """
        Create a cleaned version of the file with duplicates removed.

        Args:
            file_path (str): Input file path
            output_file (str): Output file path
            remove_exact_duplicates (bool): Whether to remove exact duplicates
        """
        qa_pairs = self.parse_qa_file(file_path)

        if remove_exact_duplicates:
            # Keep only the first occurrence of each exact duplicate
            seen_questions = set()
            cleaned_pairs = []

            for qa in qa_pairs:
                clean_question = self.clean_text(qa["question"])
                if clean_question not in seen_questions:
                    cleaned_pairs.append(qa)
                    seen_questions.add(clean_question)

            print(
                f"Removed {len(qa_pairs) - len(cleaned_pairs)} exact duplicate questions"
            )
        else:
            cleaned_pairs = qa_pairs

        # Write cleaned file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for i, qa in enumerate(cleaned_pairs):
                    if i > 0:
                        f.write("\n\n")
                    f.write(qa["full_text"])

            print(f"✓ Cleaned file saved to: {output_file}")
            print(f"  Original: {len(qa_pairs)} questions")
            print(f"  Cleaned: {len(cleaned_pairs)} questions")

        except Exception as e:
            print(f"Error saving cleaned file: {str(e)}")


def main():
    print("Quiz Duplicate Checker")
    print("=" * 22)

    # Get input file
    input_file = input(
        "Enter quiz file path (default: final_corrected_quiz_data.txt): "
    ).strip()
    if not input_file:
        input_file = "final_corrected_quiz_data.txt"

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    # Get similarity threshold
    try:
        threshold = input(
            "Enter similarity threshold (0.0-1.0, default: 0.8): "
        ).strip()
        threshold = float(threshold) if threshold else 0.8
    except ValueError:
        threshold = 0.8

    # Initialize checker
    checker = QuizDuplicateChecker(similarity_threshold=threshold)

    # Generate report
    report_file = (
        f"duplicate_report_{os.path.splitext(os.path.basename(input_file))[0]}.json"
    )
    report = checker.generate_report(input_file, report_file)

    if "error" in report:
        print(f"Error: {report['error']}")
        return

    # Ask about creating cleaned file
    if report["exact_duplicates"]["count"] > 0:
        clean = (
            input("\nCreate cleaned file with exact duplicates removed? (y/n): ")
            .strip()
            .lower()
        )
        if clean == "y":
            output_file = f"cleaned_{os.path.basename(input_file)}"
            checker.create_cleaned_file(
                input_file, output_file, remove_exact_duplicates=True
            )


if __name__ == "__main__":
    main()
