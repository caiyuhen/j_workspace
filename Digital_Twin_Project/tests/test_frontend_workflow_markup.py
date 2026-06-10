from pathlib import Path


def test_frontend_contains_workflow_selector():
    html = Path("services/report-gateway/src/static/index.html").read_text(encoding="utf-8")
    assert 'id="workflow-type"' in html
    assert 'id="xray-upload"' in html
    assert "/workflow/analyze" in html
