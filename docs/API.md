# API Summary

Interactive OpenAPI documentation is available at `/docs`.

## Endpoints

- `GET /health`
- `POST /books/upload`
- `GET /books/{book_id}`
- `POST /api/books/{book_id}/chat`
- `POST /api/books/{book_id}/generate/summary`
- `POST /api/books/{book_id}/generate/quiz`
- `POST /api/books/{book_id}/generate/flashcards`
- `POST /api/books/{book_id}/generate/mindmap`
- `GET /api/assets/{asset_id}`
- `POST /api/assets/{asset_id}/approve`
- `POST /books/{book_id}/slides`

## Chat example

```json
{
  "question": "ارزیابی تکوینی چه تفاوتی با ارزیابی پایانی دارد؟"
}
```

The response includes `answer`, `mode`, and a list of citations with page, chapter, excerpt, and retrieval score.
