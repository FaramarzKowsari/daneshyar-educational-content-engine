from app.services.pdf_ingestion import _looks_corrupted
from app.services.text_utils import normalize_text


def test_detects_fragmented_persian_text():
    broken = "ه د ف ا ز ی ا د گ ی ر ی ع م ی ق ا ی ن ا س ت"
    assert _looks_corrupted(broken)


def test_accepts_normal_persian_text():
    normal = "هدف یادگیری عمیق، ایجاد ارتباط معنادار میان مفاهیم و کاربرد آن‌ها در موقعیت‌های تازه است."
    assert not _looks_corrupted(normal)


def test_normalizes_arabic_presentation_forms_and_controls():
    value = "\u202bكتاب ي ك\u202c"
    result = normalize_text(value)
    assert "ک" in result
    assert "ی" in result
