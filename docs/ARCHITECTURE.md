# Architecture

## Design goal

Prove one thing quickly: a university textbook can become a grounded educational assistant whose answers and generated assets remain traceable to the source pages.

## Components

1. **Web application:** FastAPI + Jinja + vanilla JavaScript.
2. **Document ingestion:** PyMuPDF extracts ordered blocks and page numbers.
3. **Chunking:** page-local overlapping chunks preserve page provenance.
4. **Persistence:** SQLite stores books, chunks, generated assets, and chat logs.
5. **Retrieval:** TF-IDF is always available. Optional OpenAI embeddings add semantic similarity.
6. **Generation:** OpenAI Responses API when configured; deterministic local fallbacks otherwise.
7. **Exports:** python-pptx creates editable PowerPoint files.
8. **Review:** every generated asset starts as `draft` and may be marked `approved` by an instructor.

## Why a modular monolith

A modular monolith is deliberate for the MVP. It reduces deployment cost, avoids premature queues and microservices, and makes a six-to-eight-week pilot realistic. Service boundaries in `app/services/` make later extraction possible.

## Scale-out path

- PostgreSQL instead of SQLite
- Qdrant or pgvector instead of JSON embeddings
- Object storage for PDFs and exports
- Worker queue for ingestion and generation
- University SSO and role-based access
- LMS integration through LTI 1.3
- Audit log, rate limiting, backup, monitoring, and data-retention controls
