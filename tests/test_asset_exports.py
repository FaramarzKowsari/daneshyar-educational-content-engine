from types import SimpleNamespace

from app.public_routes import _json_asset, _markdown_asset


def test_quiz_markdown_contains_question_and_answer():
    asset = SimpleNamespace(
        id=1,
        title="آزمون فصل اول",
        asset_type="quiz",
        chapter="فصل اول",
        status="draft",
        created_at=None,
        content='[{"question":"نمونه؟","options":["الف","ب"],"answer":"الف",'
        '"explanation":"توضیح","difficulty":"متوسط","source_page":3}]',
    )
    output = _markdown_asset(asset)
    assert "سؤال 1" in output
    assert "نمونه؟" in output
    assert "پاسخ:" in output
    assert "10.5281/zenodo.21481330" in output


def test_json_export_contains_doi_and_content():
    asset = SimpleNamespace(
        id=2,
        title="خلاصه",
        asset_type="summary",
        chapter="کل کتاب",
        status="draft",
        created_at=None,
        content="متن خلاصه",
    )
    output = _json_asset(asset)
    assert '"software_doi": "10.5281/zenodo.21481330"' in output
    assert "متن خلاصه" in output
