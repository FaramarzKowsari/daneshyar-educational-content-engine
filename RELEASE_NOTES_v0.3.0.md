# Daneshyar Educational Content Engine — Public Beta v0.3.0

Daneshyar is a bilingual, open-source educational content engine for turning user-supplied university PDF books into grounded educational outputs.

## Highlights

- Public PDF upload and temporary per-user book sessions
- Page-aware text extraction and preliminary chapter detection
- Persian and English OCR support
- Grounded question answering with page citations
- Local extractive fallback without an AI API key
- Optional OpenAI-based generation
- Summaries, quizzes, flashcards, concept maps, and slide drafts
- Bilingual Persian/English author profile and demo documentation
- GitHub Pages frontend connected to a FastAPI backend deployed on Render
- Docker, automated tests, GitHub Actions, and MIT licensing

## Public beta limitations

- Maximum upload size: 10 MB
- Maximum PDF length: 120 pages
- Temporary retention: 2 hours
- OCR and processing are slower on the free Render instance
- The free deployment is intended for evaluation and light testing, not institutional-scale concurrent use

## Links

- Public interface: https://faramarzkowsari.github.io/daneshyar-educational-content-engine/
- Backend health: https://daneshyar-public-beta.onrender.com/health
- Repository: https://github.com/FaramarzKowsari/daneshyar-educational-content-engine

## Authors

- Faramarz Kowsari — ORCID: https://orcid.org/0000-0003-1692-0453
- Safieh Siadat
