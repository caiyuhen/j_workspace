# Workflow Integration and X-Ray Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start the full service stack, improve X-ray feature extraction quality, and complete one real end-to-end verification run for `pdf_only`, `xray_only`, and `multimodal` workflows using the existing gateway entrypoint.

**Architecture:** Keep the current microservice layout intact. Improve `xray-analysis-service` in place with foreground detection, centerline estimation, quality scoring, and format-aware loading; then extend `report-gateway` and the static console only where needed to surface the new metadata and support real integration verification through `/workflow/analyze`.

**Tech Stack:** FastAPI, HTTPX, NumPy, Pillow, pydicom, Plotly, vanilla HTML/CSS/JS, pytest, PowerShell

---

### Task 1: Add failing tests for enhanced X-ray feature extraction

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\tests\test_xray_analyzer_enhanced.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\Digital_Twin_Project\tests\test_xray_analyzer_enhanced.py`

```python
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_analyze_png_returns_quality_and_analysis_meta(tmp_path: Path):
    module = load_module("services/xray-analysis-service/src/analyzer.py", "xray_analyzer_enhanced")
    image_path = tmp_path / "coronal_spine.png"

    canvas = np.zeros((240, 120), dtype=np.uint8)
    for y in range(20, 220):
        x = int(60 + 15 * np.sin((y - 20) / 30.0))
        canvas[y, max(0, x - 2):min(120, x + 3)] = 220
    Image.fromarray(canvas).save(image_path)

    result = module.XRayAnalyzer().analyze(image_path, patient_name="增强患者")

    assert result["status"] == "success"
    state = result["patient_state"]
    assert state["image_quality_score"] > 0
    assert state["analysis_meta"]["foreground_detected"] is True
    assert state["analysis_meta"]["centerline_points"] >= 10
    assert state["analysis_meta"]["view_hint"] == "coronal"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_xray_analyzer_enhanced.py::test_analyze_png_returns_quality_and_analysis_meta -v`

Expected: FAIL with missing `image_quality_score`, missing `analysis_meta`, or missing enhanced metadata keys.

- [ ] **Step 3: Write minimal implementation**

Update `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py` by adding focused helpers for preprocessing, foreground extraction, centerline estimation, and metadata emission:

```python
def _smooth_vector(values: np.ndarray, window: int = 9) -> np.ndarray:
    if len(values) < window:
        return values
    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(values, kernel, mode="same")


class XRayAnalyzer:
    def _preprocess(self, pixels: np.ndarray) -> np.ndarray:
        pixels = pixels.astype(np.float32)
        pixels -= pixels.min()
        if pixels.max() > 0:
            pixels = pixels / pixels.max() * 255.0
        return pixels

    def _extract_foreground_mask(self, pixels: np.ndarray) -> np.ndarray:
        threshold = np.percentile(pixels, 75)
        mask = pixels >= threshold
        return mask

    def _estimate_centerline(self, pixels: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        h, w = pixels.shape[:2]
        ys = np.linspace(0, h - 1, 17).astype(int)
        xs = []
        valid_y = []
        for y in ys:
            row = np.where(mask[y])[0]
            if len(row) == 0:
                continue
            xs.append(float(row.mean()))
            valid_y.append(float(y))
        if len(xs) < 3:
            xs = [w / 2.0] * 17
            valid_y = np.linspace(0, h - 1, 17).tolist()
        xs = _smooth_vector(np.asarray(xs, dtype=np.float32))
        return np.asarray(valid_y, dtype=np.float32), xs
```

Then extend the returned `patient_state` shape:

```python
"image_quality_score": quality_score,
"analysis_meta": {
    "format": file_path.suffix.lower(),
    "width": int(width),
    "height": int(height),
    "foreground_detected": bool(mask.any()),
    "centerline_points": int(len(xs)),
    "image_quality_score": quality_score,
    "view_hint": view_hint,
},
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_xray_analyzer_enhanced.py::test_analyze_png_returns_quality_and_analysis_meta -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_xray_analyzer_enhanced.py services/xray-analysis-service/src/analyzer.py
git commit -m "feat: enhance xray feature extraction metadata"
```

### Task 2: Add failing tests for HEIC/DICOM format handling and clearer errors

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\tests\test_xray_format_handling.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\Digital_Twin_Project\tests\test_xray_format_handling.py`

```python
import importlib.util
from io import BytesIO

from fastapi.testclient import TestClient


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_heic_returns_clear_conversion_hint():
    module = load_module("services/xray-analysis-service/src/main.py", "xray_service_format")
    client = TestClient(module.app)

    response = client.post(
        "/xray/analyze",
        files={"file": ("sample.HEIC", BytesIO(b"not-a-real-heic"), "image/heic")},
    )

    assert response.status_code in {400, 422}
    assert "PNG" in response.json()["detail"] or "JPG" in response.json()["detail"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_xray_format_handling.py::test_heic_returns_clear_conversion_hint -v`

Expected: FAIL because `.heic` is currently rejected as unsupported without a targeted conversion hint.

- [ ] **Step 3: Write minimal implementation**

Update `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py` to recognize `.heic` and `.heif` as known-but-optional formats:

```python
        if suffix in {".heic", ".heif"}:
            try:
                image = Image.open(file_path).convert("L")
                image = ImageOps.autocontrast(image)
                return np.asarray(image, dtype=np.float32)
            except Exception as exc:
                raise ValueError("当前环境无法解码 HEIC，请先转换为 PNG 或 JPG 后再上传") from exc
```

Update `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py` to accept `.heic` and `.heif` in request validation:

```python
    if suffix not in {".png", ".jpg", ".jpeg", ".dcm", ".heic", ".heif"}:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/HEIC/DICOM 文件")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_xray_format_handling.py::test_heic_returns_clear_conversion_hint -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_xray_format_handling.py services/xray-analysis-service/src/analyzer.py services/xray-analysis-service/src/main.py
git commit -m "feat: improve heic and dicom format handling"
```

### Task 3: Add failing tests for gateway response metadata surfacing

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\tests\test_workflow_response_metadata.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\Digital_Twin_Project\tests\test_workflow_response_metadata.py`

```python
import importlib.util


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_fused_state_keeps_analysis_meta_from_xray():
    module = load_module("services/report-gateway/src/main.py", "report_gateway_meta")
    pdf_state = {
        "name": "测试患者",
        "data_source": "pdf",
        "metrics": {"cobb_angle": 12.0, "kyphosis_max": 40.0, "lordosis_max": 30.0},
        "curve_data": {"vertebral_rotation": [1.0] * 17, "coronal_offsets": [0.0] * 17, "sagittal_profile": [10.0] * 17},
    }
    xray_state = {
        "name": "测试患者",
        "data_source": "xray",
        "metrics": {"cobb_angle": 20.0, "kyphosis_max": 36.0, "lordosis_max": 28.0},
        "curve_data": {"vertebral_rotation": [1.5] * 17, "coronal_offsets": [2.0] * 17, "sagittal_profile": [9.0] * 17},
        "confidence": {"cobb_angle": 0.7},
        "image_quality_score": 0.81,
        "analysis_meta": {"view_hint": "coronal", "centerline_points": 17, "foreground_detected": True},
    }

    fused = module.fuse_patient_states(pdf_state, xray_state, explicit_name=None)

    assert fused["image_quality_score"] == 0.81
    assert fused["analysis_meta"]["view_hint"] == "coronal"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_response_metadata.py::test_fused_state_keeps_analysis_meta_from_xray -v`

Expected: FAIL because `fuse_patient_states()` currently drops `image_quality_score` and `analysis_meta`.

- [ ] **Step 3: Write minimal implementation**

Update `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`:

```python
    return {
        "name": explicit_name or pdf_state.get("name") or xray_state.get("name") or "匿名患者",
        "data_source": "fused",
        "metrics": {
            "cobb_angle": fused_cobb or 20.0,
            "kyphosis_max": xray_metrics.get("kyphosis_max", pdf_metrics.get("kyphosis_max", 40.0)),
            "lordosis_max": xray_metrics.get("lordosis_max", pdf_metrics.get("lordosis_max", 30.0)),
        },
        "curve_data": xray_state.get("curve_data") or pdf_state.get("curve_data"),
        "confidence": {
            "cobb_angle": xray_state.get("confidence", {}).get("cobb_angle", 0.5),
        },
        "image_quality_score": xray_state.get("image_quality_score", 0.0),
        "analysis_meta": xray_state.get("analysis_meta", {}),
        "review_required": has_conflict or xray_state.get("review_required", False),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workflow_response_metadata.py::test_fused_state_keeps_analysis_meta_from_xray -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_workflow_response_metadata.py services/report-gateway/src/main.py
git commit -m "feat: expose xray metadata in workflow results"
```

### Task 4: Add failing tests for frontend display of X-ray quality metadata

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\tests\test_frontend_xray_metadata_markup.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\static\index.html`

- [ ] **Step 1: Write the failing test**

`D:\workspace\Digital_Twin_Project\tests\test_frontend_xray_metadata_markup.py`

```python
from pathlib import Path


def test_frontend_mentions_image_quality_score():
    html = Path("services/report-gateway/src/static/index.html").read_text(encoding="utf-8")
    assert "image_quality_score" in html
    assert "analysis_meta" in html
    assert "review_required" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_xray_metadata_markup.py::test_frontend_mentions_image_quality_score -v`

Expected: FAIL because the current markup does not explicitly render the new quality metadata names.

- [ ] **Step 3: Write minimal implementation**

Update `D:\workspace\Digital_Twin_Project\services\report-gateway\src\static\index.html` in `renderComparison(result)` so the table explicitly renders the new fields:

```javascript
            const qualityScore = patientState.image_quality_score ?? "-";
            const analysisMeta = patientState.analysis_meta || {};

            container.innerHTML = `
                <table>
                    <tr><th>字段</th><th>值</th></tr>
                    <tr><td>工作流</td><td>${result.workflow_type || "-"}</td></tr>
                    <tr><td>患者姓名</td><td>${patientState.name || "-"}</td></tr>
                    <tr><td>数据来源</td><td>${patientState.data_source || "-"}</td></tr>
                    <tr><td>image_quality_score</td><td>${qualityScore}</td></tr>
                    <tr><td>analysis_meta</td><td><pre style="white-space: pre-wrap; text-align: left;">${JSON.stringify(analysisMeta, null, 2)}</pre></td></tr>
                    <tr><td>review_required</td><td>${result.review_required ? "true" : "false"}</td></tr>
                </table>
            `;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_xray_metadata_markup.py::test_frontend_mentions_image_quality_score -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_frontend_xray_metadata_markup.py services/report-gateway/src/static/index.html
git commit -m "feat: display xray quality metadata in frontend"
```

### Task 5: Add a reproducible integration smoke script and failing verification test

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\tests\test_integration_samples_exist.py`
- Create: `D:\workspace\Digital_Twin_Project\run_multimodal_smoke_checks.py`
- Modify: `D:\workspace\Digital_Twin_Project\start_services_alt_ports.ps1`

- [ ] **Step 1: Write the failing test**

`D:\workspace\Digital_Twin_Project\tests\test_integration_samples_exist.py`

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_samples_exist_for_three_workflows():
    assert (ROOT / "source_data" / "10" / "倪欣然.pdf").exists()
    assert (ROOT / "source_data" / "10" / "x光" / "倪欣然17岁冠状面.PNG").exists()
```

- [ ] **Step 2: Run test to verify it fails or identifies the real sample path problem**

Run: `pytest tests/test_integration_samples_exist.py::test_real_samples_exist_for_three_workflows -v`

Expected: PASS if paths are correct. If it fails, fix the exact sample paths in the test before proceeding.

- [ ] **Step 3: Write minimal implementation**

Create `D:\workspace\Digital_Twin_Project\run_multimodal_smoke_checks.py`:

```python
from __future__ import annotations

from pathlib import Path
import json
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


def main():
    results = {
        "pdf_only": call_workflow("pdf_only", True, False),
        "xray_only": call_workflow("xray_only", False, True),
        "multimodal": call_workflow("multimodal", True, True),
    }
    output = ROOT / "debug_log.txt"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Smoke checks completed.")


if __name__ == "__main__":
    main()
```

Update `D:\workspace\Digital_Twin_Project\start_services_alt_ports.ps1` to leave the service ports unchanged and keep the printed URLs, but add a line reminding the operator about the smoke script:

```powershell
Write-Host "Smoke test: python .\run_multimodal_smoke_checks.py"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_integration_samples_exist.py::test_real_samples_exist_for_three_workflows -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration_samples_exist.py run_multimodal_smoke_checks.py start_services_alt_ports.ps1
git commit -m "test: add multimodal smoke check script"
```

### Task 6: Update startup integrity and docs for the enhanced workflow run

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\test_startup_integrity.py`
- Modify: `D:\workspace\Digital_Twin_Project\docs\MULTIMODAL_ANALYSIS_WORKFLOWS.md`
- Modify: `D:\workspace\Digital_Twin_Project\services\README.md`

- [ ] **Step 1: Write the failing test**

Add this test to `D:\workspace\Digital_Twin_Project\test_startup_integrity.py`:

```python
    def test_smoke_check_script_exists(self):
        script = ROOT / "run_multimodal_smoke_checks.py"
        self.assertTrue(script.exists(), f"{script} is missing")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest test_startup_integrity.py::StartupIntegrityTests::test_smoke_check_script_exists -v`

Expected: FAIL until the smoke script is added in Task 5.

- [ ] **Step 3: Write minimal implementation**

Update `D:\workspace\Digital_Twin_Project\docs\MULTIMODAL_ANALYSIS_WORKFLOWS.md` with an implementation note:

```md
### 9.3 联调现状

- 当前联调使用 `run_multimodal_smoke_checks.py`
- 真实 DICOM 样本验证待补充
- X 光增强版输出 `image_quality_score` 与 `analysis_meta`
```

Update `D:\workspace\Digital_Twin_Project\services\README.md` with a short section:

```md
## 联调脚本

启动服务后可执行：

```bash
python .\run_multimodal_smoke_checks.py
```
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest test_startup_integrity.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add test_startup_integrity.py docs/MULTIMODAL_ANALYSIS_WORKFLOWS.md services/README.md
git commit -m "docs: add enhanced workflow integration notes"
```

### Task 7: Perform the real integration run and capture evidence

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\debug_log.txt`

- [ ] **Step 1: Start the full stack**

Run:

```bash
powershell -ExecutionPolicy Bypass -File .\start_services_alt_ports.ps1
```

Expected: New PowerShell windows start services on `9000-9005`.

- [ ] **Step 2: Verify service health**

Run:

```bash
python - <<'PY'
import requests
for path in [
    "http://127.0.0.1:9000/health",
    "http://127.0.0.1:9001/health",
    "http://127.0.0.1:9002/health",
    "http://127.0.0.1:9003/health",
    "http://127.0.0.1:9004/health",
    "http://127.0.0.1:9005/health",
]:
    resp = requests.get(path, timeout=10)
    print(path, resp.status_code)
PY
```

Expected: All return `200`

- [ ] **Step 3: Run the real smoke check script**

Run:

```bash
python .\run_multimodal_smoke_checks.py
```

Expected: Script exits successfully and writes workflow results into `debug_log.txt`.

- [ ] **Step 4: Review smoke output**

Open `D:\workspace\Digital_Twin_Project\debug_log.txt` and confirm all three entries exist:

```json
{
  "pdf_only": { "...": "..." },
  "xray_only": { "...": "..." },
  "multimodal": { "...": "..." }
}
```

- [ ] **Step 5: Commit**

```bash
git add debug_log.txt
git commit -m "test: capture real multimodal integration run"
```

### Task 8: Final verification

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\docs\superpowers\specs\2026-06-10-workflow-integration-and-xray-enhancement-design.md`

- [ ] **Step 1: Run the full automated suite introduced by this plan**

Run:

```bash
pytest tests/test_xray_service_smoke.py tests/test_xray_analyzer.py tests/test_xray_endpoint.py tests/test_xray_analyzer_enhanced.py tests/test_xray_format_handling.py tests/test_gateway_workflow_contract.py tests/test_gateway_fusion.py tests/test_workflow_xray_only.py tests/test_workflow_pdf_and_multimodal.py tests/test_workflow_response_metadata.py tests/test_frontend_workflow_markup.py tests/test_frontend_xray_metadata_markup.py tests/test_workflow_support_files.py tests/test_integration_samples_exist.py test_startup_integrity.py -v
```

Expected: PASS

- [ ] **Step 2: Re-read the spec and verify coverage**

Check `D:\workspace\Digital_Twin_Project\docs\superpowers\specs\2026-06-10-workflow-integration-and-xray-enhancement-design.md` against:
- service startup
- real workflow run
- enhanced X-ray extraction
- HEIC/DICOM handling
- docs

Expected: every spec section maps to a completed task.

- [ ] **Step 3: Note DICOM limitation in final docs if not already explicit**

Ensure this sentence exists in the spec or workflow doc:

```md
真实 DICOM 样本联调待用户补充 `.dcm` 样本后执行。
```

- [ ] **Step 4: Confirm working tree diagnostics are clean for edited files**

Run:

```bash
python -m compileall services/xray-analysis-service/src services/report-gateway/src
```

Expected: no syntax errors

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-06-10-workflow-integration-and-xray-enhancement-design.md
git commit -m "chore: finish workflow integration and xray enhancement verification"
```
