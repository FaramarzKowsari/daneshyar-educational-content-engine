# Evaluation Protocol

## 1. Ground-truth set

A subject-matter instructor prepares 50 questions:

- 30 answerable factual/conceptual questions
- 10 multi-section synthesis questions
- 10 deliberately unanswerable questions

For each answerable question, record the expected chapter and page range.

## 2. Retrieval metrics

- Hit@1 and Hit@5 for the expected page
- Mean Reciprocal Rank
- percentage of queries with no relevant hit

## 3. Answer metrics

Two instructors independently score each answer from 0 to 2:

- 0: unsupported or incorrect
- 1: partially correct or incomplete
- 2: correct and grounded

Also record hallucination, citation correctness, clarity, and usefulness.

## 4. Generated-asset review

For summaries, quizzes, flashcards, and slides, classify each item as:

- accepted unchanged
- accepted with minor edits
- major revision required
- rejected

## 5. Time-saved study

Measure the time needed for an instructor to create equivalent assets manually versus with Daneshyar plus review.

## 6. Go/no-go gate

Continue to the institutional phase only if the acceptance criteria in `MVP_SCOPE.md` are met and copyright/privacy approval is documented.
