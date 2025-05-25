import os


def merge_corrected_chunks(
    corrected_dir="corrected_chunks", output_file="final_corrected_quiz_data.txt"
):
    """Manually merge all corrected chunks into a single file."""
    try:
        if not os.path.exists(corrected_dir):
            print(f"Error: Directory '{corrected_dir}' not found.")
            return False

        # Get all corrected chunk files - support both raw and quiz chunk patterns
        # Exclude summary files
        chunk_files = [
            f
            for f in os.listdir(corrected_dir)
            if (
                f.startswith("corrected_quiz_chunk_")
                or f.startswith("corrected_raw_chunk_")
            )
            and f.endswith(".txt")
            and "summary" not in f.lower()
        ]
        chunk_files.sort()

        # Debug: Show what files are in the directory
        all_files = os.listdir(corrected_dir)
        print(f"Debug: Directory '{corrected_dir}' contains {len(all_files)} files:")
        for f in all_files:
            print(f"  - {f}")

        if not chunk_files:
            print(f"\nNo corrected chunk files found in '{corrected_dir}'")
            print(
                "Looking for files starting with 'corrected_quiz_chunk_' or 'corrected_raw_chunk_'"
            )

            # Try to find files with similar patterns
            similar_files = [
                f
                for f in all_files
                if f.endswith(".txt")
                and ("corrected" in f.lower() or "chunk" in f.lower())
            ]

            if similar_files:
                print(
                    f"\nFound {len(similar_files)} files with 'corrected' or 'chunk' in name:"
                )
                for f in similar_files:
                    print(f"  - {f}")

                use_similar = (
                    input("\nTry to merge these files instead? (y/n): ").strip().lower()
                )
                if use_similar == "y":
                    chunk_files = similar_files
                    chunk_files.sort()
                else:
                    return False
            else:
                return False

        print(f"\nFound {len(chunk_files)} corrected chunk files to merge:")
        for f in chunk_files:
            print(f"  - {f}")

        merged_content = []

        for chunk_file in chunk_files:
            chunk_path = os.path.join(corrected_dir, chunk_file)
            with open(chunk_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    merged_content.append(content)
                    print(f"✓ Added {chunk_file}")

        # Write merged content
        final_content = "\n\n".join(merged_content)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)

        # Count Q&A pairs
        qa_pairs = final_content.split("\n\n")
        qa_pairs = [pair.strip() for pair in qa_pairs if pair.strip()]

        print(f"\n✓ Successfully merged {len(chunk_files)} corrected chunks")
        print(f"✓ Total Q&A pairs in final file: {len(qa_pairs)}")
        print(f"✓ Final corrected file saved to: {output_file}")

        return True

    except Exception as e:
        print(f"Error merging corrected chunks: {str(e)}")
        return False


if __name__ == "__main__":
    print("Manual Merge Tool for Corrected Chunks")
    print("=" * 40)

    corrected_dir = (
        input("Enter corrected chunks directory (default: corrected_chunks): ").strip()
        or "corrected_chunks"
    )
    output_file = (
        input(
            "Enter output filename (default: final_corrected_quiz_data.txt): "
        ).strip()
        or "final_corrected_quiz_data.txt"
    )

    success = merge_corrected_chunks(corrected_dir, output_file)

    if not success:
        print("\n" + "=" * 50)
        print("TROUBLESHOOTING TIPS:")
        print("1. Make sure you have run the gemini_corrector.py first")
        print("2. Check if your corrected files are in a different directory")
        print("3. Verify the file naming pattern matches:")
        print("   - corrected_quiz_chunk_*.txt")
        print("   - corrected_raw_chunk_*.txt")
        print("4. Try running: python gemini_corrector.py")
        print("=" * 50)
