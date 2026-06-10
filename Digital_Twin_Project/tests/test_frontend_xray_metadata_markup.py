from pathlib import Path


def test_frontend_mentions_image_quality_score():
    html = Path("services/report-gateway/src/static/index.html").read_text(encoding="utf-8")
    assert "image_quality_score" in html
    assert "analysis_meta" in html
    assert "review_required" in html
