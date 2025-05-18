from bs4 import BeautifulSoup
import json
import re


def clean_text(text, words_to_remove=None, chars_to_remove=None):
    """
    Clean text by removing specified words and characters

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


def extract_qa_pairs(html_file, words_to_remove=None, chars_to_remove=None):
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

    # Default words to remove if none specified
    if words_to_remove is None:
        words_to_remove = ["NHUNG HOÀNG"]

    # Find all question blocks
    question_blocks = []
    paragraphs = soup.find_all("p")

    current_question_text = None
    current_options = []
    current_block = None

    for p in paragraphs:
        text = p.get_text().strip()

        # Skip empty paragraphs
        if not text:
            continue

        # Clean the text
        cleaned_text = clean_text(text, words_to_remove, chars_to_remove)

        # Skip if text is empty after cleaning
        if not cleaned_text:
            continue

        # Check if this is a new question
        if "NHUNG HOÀNG" in text:
            # Save previous question block if it exists
            if current_question_text and current_options:
                question_blocks.append(
                    {"question_text": current_question_text, "options": current_options}
                )

            # Start new question
            current_question_text = cleaned_text
            current_options = []

        # Check if this is an option (A, B, C, D, E)
        elif re.match(r"^[A-E]\.\s", text) or re.match(r"^[A-E]\)\s", text):
            # Extract the option letter
            option_letter = text[0]

            # Remove the letter prefix from the option text
            # This fixes the "A. A. Option" redundancy
            option_text = re.sub(r"^[A-E]\.?\s*", "", cleaned_text)

            current_options.append({"letter": option_letter, "text": option_text})

    # Add the last question block if it exists
    if current_question_text and current_options:
        question_blocks.append(
            {"question_text": current_question_text, "options": current_options}
        )

    # Try to find the correct answers
    qa_pairs = []

    # Look for correct answer indicators in the HTML
    for i, question_block in enumerate(question_blocks):
        correct_answer = None

        # Method 1: Look for highlighted or marked correct answers
        # This is a simplified approach - you'll need to adapt based on actual Quizlet HTML structure
        correct_spans = soup.select("span.TermText.correct, span.TermText.is-correct")

        for span in correct_spans:
            # Look for A, B, C, D in the text
            match = re.search(r"\b([A-E])[.)]", span.get_text())
            if match:
                correct_answer = match.group(1)
                break

        # Method 2: Look for specific answer classes or attributes
        # If marked in a different way in Quizlet HTML
        if not correct_answer:
            # Example: find elements with correct answer class
            correct_elements = soup.select("div.correct-answer, span.is-correct")

            for element in correct_elements:
                text = element.get_text().strip()
                match = re.search(r"\b([A-E])[.)]", text)
                if match:
                    correct_answer = match.group(1)
                    break

        # If still no correct answer found, try to infer from HTML structure or class names
        if not correct_answer and question_block["options"]:
            # For now, just use the first option as a fallback
            # You should replace this with actual logic based on Quizlet's specific HTML
            correct_answer = question_block["options"][0]["letter"]

        # Create the QA pair
        qa_pair = {
            "question": question_block["question_text"],
            "options": [opt["text"] for opt in question_block["options"]],
            "answer": correct_answer,
        }

        qa_pairs.append(qa_pair)

    return qa_pairs


def format_qa_pairs(qa_pairs, qa_separator="\t", card_separator="\n"):
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
    qa_pairs, output_file="flashcards.txt", qa_separator="\t", card_separator="\n\n"
):
    """
    Save the question-answer pairs to a text file with custom formatting
    """
    formatted_content = format_qa_pairs(qa_pairs, qa_separator, card_separator)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_content)


def save_to_json(qa_pairs, output_file="flashcards.json"):
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
