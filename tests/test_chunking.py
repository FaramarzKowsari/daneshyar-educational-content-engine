from app.services.chunking import build_chunks
from app.services.pdf_ingestion import PageText


def test_chunking_preserves_page_and_chapter():
    pages = [PageText(1, "فصل اول: مقدمه\n" + "این یک جمله آزمایشی است. " * 80, "فصل اول: مقدمه")]
    chunks = build_chunks(pages, chunk_size=400, overlap=60)
    assert len(chunks) > 1
    assert all(chunk.page_start == 1 for chunk in chunks)
    assert all(chunk.chapter == "فصل اول: مقدمه" for chunk in chunks)
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))
