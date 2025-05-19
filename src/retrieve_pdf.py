import re
import json
from typing import List, Optional, Dict
from pypdf import PdfReader

# Regex patterns as constants
ANSWER_MARKER_PATTERN = re.compile(r";;([A-E])\s*$")
OPTION_PATTERN = re.compile(r"^[A-E][.)]?\s")
CLEAN_OPTION_PATTERN = re.compile(r"^[A-E][.)]?\s*")


def clean_text(
    text: str,
    words_to_remove: Optional[List[str]] = None,
    chars_to_remove: Optional[str] = None,
) -> str:
    if not text:
        return text
    if words_to_remove:
        for word in words_to_remove:
            text = re.sub(
                r"\\b" + re.escape(word) + r"\\b", "", text, flags=re.IGNORECASE
            )
    if chars_to_remove:
        for char in chars_to_remove:
            text = text.replace(char, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_qa_pairs_from_pdf(
    pdf_file: str,
    words_to_remove: Optional[List[str]] = None,
    chars_to_remove: Optional[str] = None,
) -> List[Dict]:
    reader = PdfReader(pdf_file)
    print(f"Number of pages: {len(reader.pages)}")
    all_qa_pairs = []
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        print(f"Page {page_num + 1}: {len(lines)} non-empty lines.")

        # Helper to filter out noise lines
        def is_noise(line: str) -> bool:
            return (
                not line
                or "mln111" in line.lower()
                or "terms in this set" in line.lower()
                or "review" in line.lower()
                or "save" in line.lower()
                or line.startswith("http")
                or re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}", line)
                or re.match(r"^\d+/\d+$", line)
                or "quizlet.com" in line.lower()
            )

        # Group lines into question blocks
        blocks = []
        block = []
        for line in lines:
            if is_noise(line):
                continue
            if len(line) == 1 and line in "ABCDE":  # answer line
                block.append(line)
                blocks.append(block)
                block = []
            else:
                block.append(line)
        if block:
            blocks.append(block)

        for block in blocks:
            # Find first option
            opt_start = next(
                (
                    i
                    for i, line_text in enumerate(block)
                    if re.match(r"^[A-E][.)]?\s", line_text)
                ),
                None,
            )
            if opt_start is None or len(block) < opt_start + 2:
                continue
            question = " ".join(block[:opt_start]).replace("(NHUNG HOÀNG)", "").strip()
            options = []
            curr_opt = None
            for line in block[opt_start:-1]:
                m = re.match(r"^([A-E])[.)]?\s*(.*)", line)
                if m:
                    if curr_opt:
                        cleaned_opt = re.sub(r"^[.\s]+", "", curr_opt.strip())
                        if cleaned_opt.lower() != "nh" and cleaned_opt != "":
                            options.append(cleaned_opt)
                    curr_opt = f"{m.group(1)}. {m.group(2).strip()}"
                else:
                    if curr_opt is not None:
                        curr_opt += " " + line.strip()
            if curr_opt:
                cleaned_opt = re.sub(r"^[.\s]+", "", curr_opt.strip())
                if cleaned_opt.lower() != "nh" and cleaned_opt != "":
                    options.append(cleaned_opt)
            answer = block[-1] if block[-1] in "ABCDE" else None
            if answer:
                answer = re.sub(r"^[.\s]+", "", answer)
            all_qa_pairs.append(
                {"question": question, "options": options, "answer": answer}
            )
    return all_qa_pairs


def format_qa_pairs(
    qa_pairs: List[Dict],
    qa_separator: str = ";;",
    card_separator: str = "\n\n",
) -> str:
    formatted_cards = []
    for qa in qa_pairs:
        question = qa["question"]
        formatted_question = question
        if "options" in qa:
            for option_text in qa["options"]:
                formatted_question += f"\n{option_text}"
        answer = qa.get("answer", "")
        formatted_cards.append(f"{formatted_question}{qa_separator}{answer}")
    return card_separator.join(formatted_cards)


def save_to_txt(
    qa_pairs: List[Dict],
    output_file: str = "flashcards.txt",
    qa_separator: str = ";;",
    card_separator: str = "\n\n",
):
    formatted_content = format_qa_pairs(qa_pairs, qa_separator, card_separator)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_content)


def save_to_json(qa_pairs: List[Dict], output_file: str = "flashcards.json"):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)


def main():
    pdf_file = ""
    words_to_remove = []
    chars_to_remove = "[](){}"
    qa_pairs = extract_qa_pairs_from_pdf(pdf_file, words_to_remove, chars_to_remove)
    if qa_pairs:
        save_to_txt(qa_pairs, "flashcards.txt")
        save_to_json(qa_pairs, "flashcards.json")
        print(f"Found {len(qa_pairs)} questions")
        print("Data saved to flashcards.txt and flashcards.json")
    else:
        print("No questions found")


if __name__ == "__main__":
    main()
