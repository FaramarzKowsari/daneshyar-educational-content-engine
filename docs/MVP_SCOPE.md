# MVP Scope

## Included

- One or more text-based PDF textbooks
- Source-grounded question answering
- Page-level citations
- Summary, quiz, flashcard, mind map, and PowerPoint generation
- Instructor approval state
- Local fallback mode and optional OpenAI mode
- Dockerized deployment and automated tests

## Explicitly deferred

- OCR for scanned Persian PDFs
- student accounts, grades, and personalized learning paths
- production SSO and LMS integration
- full knowledge graph database
- microservices, queues, autoscaling, and GPU orchestration
- analytics dashboards beyond stored interaction logs

## Pilot acceptance criteria

- At least 80% of benchmark questions retrieve a relevant source page in top 5.
- At least 70% of generated questions are accepted or accepted after minor edits by the subject instructor.
- The system refuses unsupported answers in the benchmark set.
- Slide and summary generation reduce instructor preparation time by at least 40% in a timed comparison.
