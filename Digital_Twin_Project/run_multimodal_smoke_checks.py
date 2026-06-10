from __future__ import annotations

import json
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
GATEWAY = "http://127.0.0.1:9000"
PDF_SAMPLE = ROOT / "source_data" / "10" / "倪欣然.pdf"
XRAY_SAMPLE = ROOT / "source_data" / "10" / "x光" / "倪欣然17岁冠状面.PNG"


def call_workflow(workflow_type: str, include_pdf: bool, include_xray: bool) -> dict:
    data = {
        "workflow_type": workflow_type,
        "treatment_type": "Brace",
        "duration": "24",
        "compliance": "0.9",
        "patient_name": "倪欣然",
    }
    files = {}
    if include_pdf:
        files["pdf_file"] = ("sample.pdf", PDF_SAMPLE.read_bytes(), "application/pdf")
    if include_xray:
        files["xray_file"] = ("sample.PNG", XRAY_SAMPLE.read_bytes(), "image/png")

    response = requests.post(f"{GATEWAY}/workflow/analyze", data=data, files=files, timeout=120)
    response.raise_for_status()
    payload = response.json()
    assert "patient_state" in payload
    assert "evolution_chart_json" in payload
    return payload


def main() -> None:
    results = {
        "pdf_only": call_workflow("pdf_only", include_pdf=True, include_xray=False),
        "xray_only": call_workflow("xray_only", include_pdf=False, include_xray=True),
        "multimodal": call_workflow("multimodal", include_pdf=True, include_xray=True),
    }
    output = ROOT / "debug_log.txt"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Smoke checks completed: {output}")


if __name__ == "__main__":
    main()
