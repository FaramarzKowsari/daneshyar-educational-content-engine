from pathlib import Path

import fitz

from app.services.pdf_ingestion import parse_pdf


def test_parse_text_pdf(tmp_path: Path):
    path = tmp_path / "book.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Chapter 1 Introduction")
    page.insert_text((72, 100), "This is a sufficiently long educational paragraph for testing PDF extraction.")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "More educational content explains concepts and examples in detail.")
    doc.save(path)
    doc.close()

    parsed = parse_pdf(path)
    assert parsed.page_count == 2
    assert len(parsed.pages) == 2
    assert "educational" in parsed.pages[0].text
