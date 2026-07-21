from pathlib import Path

import fitz

OUTPUT = Path("data/demo-university-book.pdf")

chapters = [
    ("Chapter 1: Learning and Technology", [
        "Educational technology is the purposeful use of tools, methods, and evidence to improve learning outcomes.",
        "A learning objective should describe an observable result rather than a vague intention.",
        "Formative assessment gives feedback during learning, while summative assessment evaluates achievement at the end.",
    ]),
    ("Chapter 2: Instructional Design", [
        "Instructional design aligns learning objectives, activities, content, and assessment.",
        "Cognitive load can be reduced by segmenting complex material and removing irrelevant details.",
        "Worked examples are especially useful for novice learners because they reveal problem-solving structure.",
    ]),
    ("Chapter 3: Evaluation", [
        "A trustworthy educational system should be evaluated for accuracy, usefulness, fairness, and transparency.",
        "Grounded answers cite the source material and explicitly admit when evidence is insufficient.",
        "Human review remains necessary for generated quizzes, summaries, and teaching materials.",
    ]),
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for title, paragraphs in chapters:
        page = doc.new_page(width=595, height=842)
        page.insert_text((60, 70), title, fontsize=17)
        y = 115
        for paragraph in paragraphs:
            page.insert_textbox((60, y, 535, y + 120), paragraph * 4, fontsize=11, lineheight=1.4)
            y += 175
    doc.save(OUTPUT)
    doc.close()
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
