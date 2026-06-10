from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_start_script_starts_xray_service():
    script = (ROOT / "start_services_alt_ports.ps1").read_text(encoding="utf-8")
    assert "xray-analysis-service" in script
    assert "XRAY_SERVICE_URL" in script


def test_services_readme_mentions_xray_and_workflow_endpoint():
    readme = (ROOT / "services" / "README.md").read_text(encoding="utf-8")
    assert "xray-analysis-service" in readme
    assert "/workflow/analyze" in readme
