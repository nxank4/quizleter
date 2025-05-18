from bs4 import BeautifulSoup
import json
import re
from typing import List, Optional, Dict

# Regex patterns as constants
ANSWER_MARKER_PATTERN = re.compile(r";;([A-E])\s*$")
OPTION_PATTERN = re.compile(r"^[A-E][.)]?\s")
CLEAN_OPTION_PATTERN = re.compile(r"^[A-E][.)]?\s*")


def clean_text(
    text: str,
    words_to_remove: Optional[List[str]] = None,
    chars_to_remove: Optional[str] = None,
) -> str:
    """
    Clean text by removing specified words and characters.

    Args:
        text (str): The input text to clean
        words_to_remove (list): List of words to remove from the text
        chars_to_remove (str): String of characters to remove

    Returns:
        str: Cleaned text
    """
    if not text:
        return text

    # Remove specific words
    if words_to_remove:
        for word in words_to_remove:
            text = re.sub(
                r"\b" + re.escape(word) + r"\b",
                "",
                text,
                flags=re.IGNORECASE,
            )

    # Remove specific characters
    if chars_to_remove:
        for char in chars_to_remove:
            text = text.replace(char, "")

    # Clean up any extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_answer_letters(soup: BeautifulSoup) -> List[str]:
    """
    Extract answer letters from Quizlet HTML (span.TermText notranslate lang-vi).
    Returns a list of answer letters (A-E) in order.
    """
    return [
        span.get_text(strip=True)
        for span in soup.find_all("span", class_="TermText notranslate lang-vi")
        if re.fullmatch(r"[A-E]", span.get_text(strip=True))
    ]


def fallback_detect_answer(question_block: Dict, soup: BeautifulSoup) -> Optional[str]:
    """
    Try to detect the correct answer from HTML if not provided.
    """
    # Method 1: Look for highlighted or marked correct answers
    correct_spans = soup.select("span.TermText.correct, span.TermText.is-correct")
    for span in correct_spans:
        match = re.search(r"\b([A-E])[.)]", span.get_text())
        if match:
            return match.group(1)
    # Method 2: Look for specific answer classes or attributes
    correct_elements = soup.select("div.correct-answer, span.is-correct")
    for element in correct_elements:
        text = element.get_text().strip()
        match = re.search(r"\b([A-E])[.)]", text)
        if match:
            return match.group(1)
    # Fallback: use first option if available
    if question_block["options"]:
        return question_block["options"][0]["letter"]
    return None


def extract_qa_pairs(
    html_file: str,
    words_to_remove: Optional[List[str]] = None,
    chars_to_remove: Optional[str] = None,
) -> List[Dict]:
    """
    Extract multiple choice questions and answers from HTML file

    Args:
        html_file (str): Path to the HTML file
        words_to_remove (list): List of words to remove from the text
        chars_to_remove (str): String of characters to remove

    Returns:
        list: List of dictionaries containing questions, options, and the correct answer
    """
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")

    if words_to_remove is None:
        words_to_remove = ["NHUNG HOÀNG"]

    # Extract answer letters in order
    answer_letters = extract_answer_letters(soup)

    # Parse questions and options
    question_blocks = []
    paragraphs = (p.get_text().strip() for p in soup.find_all("p"))
    current_question_text = None
    current_options = []
    current_answer = None

    for text in paragraphs:
        if not text:
            continue

        # Detect answer marker (e.g., ;;A at the end)
        answer_marker = None
        answer_match = ANSWER_MARKER_PATTERN.search(text)
        if answer_match:
            answer_marker = answer_match.group(1)
            text = ANSWER_MARKER_PATTERN.sub("", text)

        cleaned_text = clean_text(text, words_to_remove, chars_to_remove)
        if not cleaned_text:
            continue

        if "NHUNG HOÀNG" in text:
            if current_question_text and current_options:
                question_blocks.append(
                    {
                        "question_text": current_question_text,
                        "options": current_options,
                        "answer": current_answer,
                    }
                )
            current_question_text = cleaned_text
            current_options = []
            current_answer = answer_marker
        elif OPTION_PATTERN.match(text):
            option_letter = text[0]
            option_text = CLEAN_OPTION_PATTERN.sub("", cleaned_text)
            current_options.append({"letter": option_letter, "text": option_text})
            if answer_marker:
                current_answer = answer_marker

    if current_question_text and current_options:
        question_blocks.append(
            {
                "question_text": current_question_text,
                "options": current_options,
                "answer": current_answer,
            }
        )

    # Assign extracted answer letters to questions in order
    for idx, qb in enumerate(question_blocks):
        if idx < len(answer_letters):
            qb["answer"] = answer_letters[idx]

    # Build qa_pairs
    qa_pairs = []
    for question_block in question_blocks:
        answer = question_block.get("answer") or fallback_detect_answer(
            question_block, soup
        )
        qa_pairs.append(
            {
                "question": question_block["question_text"],
                "options": [opt["text"] for opt in question_block["options"]],
                "answer": answer,
            }
        )

    return qa_pairs


def format_qa_pairs(
    qa_pairs: List[Dict],
    qa_separator: str = ";;",
    card_separator: str = "\n\n",
) -> str:
    """
    Format question-answer pairs with custom separators
    qa_separator: separator between question and answers (default: tab)
    card_separator: separator between cards/questions (default: newline)
    """
    formatted_cards = []
    for qa in qa_pairs:
        question = qa["question"]

        # Format the question with options
        formatted_question = question
        if "options" in qa:
            for i, option_text in enumerate(qa["options"]):
                option_letter = chr(65 + i)  # A, B, C, D...

                # Here's the fix - don't duplicate the option letter
                formatted_question += f"\n{option_letter}. {option_text}"

        # Get the answer
        answer = qa.get("answer", "")

        # Combine question and answer with qa_separator
        formatted_cards.append(f"{formatted_question}{qa_separator}{answer}")

    # Join all cards with card_separator
    return card_separator.join(formatted_cards)


def save_to_txt(
    qa_pairs: List[Dict],
    output_file: str = "flashcards.txt",
    qa_separator: str = ";;",
    card_separator: str = "\n\n",
):
    """
    Save the question-answer pairs to a text file with custom formatting
    """
    formatted_content = format_qa_pairs(qa_pairs, qa_separator, card_separator)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_content)


def save_to_json(qa_pairs: List[Dict], output_file: str = "flashcards.json"):
    """
    Save the question-answer pairs to a JSON file
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)


def main():
    html_file = "MLN111 - Chuẩn từ đề nhung Hoàng Flashcards _ Quizlet.html"

    # Example use of the new parameters
    words_to_remove = ["NHUNG HOÀNG", "INCORRECT", "CORRECT"]
    chars_to_remove = "[](){}"

    qa_pairs = extract_qa_pairs(html_file, words_to_remove, chars_to_remove)

    if qa_pairs:
        # Save in different formats
        save_to_txt(qa_pairs, "flashcards.txt")  # Default tab and newline separators
        save_to_json(qa_pairs, "flashcards.json")
        print(f"Found {len(qa_pairs)} questions")
        print("Data saved to flashcards.txt and flashcards.json")
    else:
        print("No questions found")


if __name__ == "__main__":
    main()
