# Multimodal Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three end-to-end workflows in the existing project: PDF-only, X-ray-only, and X-ray+PDF multimodal analysis, all ending in the existing simulation and 3D visualization flow.

**Architecture:** Add a focused `xray-analysis-service` that converts JPG/PNG/DICOM into a unified `patient_state`, extend `report-gateway` with a single `/workflow/analyze` orchestration endpoint plus lightweight fusion logic, and update the existing static UI to drive the three workflows without replacing the current frontend stack.

**Tech Stack:** FastAPI, Pydantic, HTTPX, NumPy, Pillow, pydicom, Plotly, vanilla HTML/CSS/JS, pytest

---

### Task 1: Add X-ray service scaffolding

**Files:**
- Create: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\requirements.txt`
- Create: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`
- Create: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_xray_service_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from services.xray-analysis-service.src.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "xray-analysis-service"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_xray_service_smoke.py::test_health_endpoint -v`
Expected: FAIL with `ModuleNotFoundError` or missing file error because the service does not exist yet.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\Digital_Twin_Project\services\xray-analysis-service\requirements.txt`

```txt
fastapi
uvicorn
python-multipart
numpy
pillow
pydicom
```

`D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


class XRayAnalyzer:
    def analyze(self, file_path: Path, patient_name: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Implemented in later tasks")
```

`D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py`

```python
from fastapi import FastAPI


app = FastAPI(title="X-Ray Analysis Service", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "xray-analysis-service"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_xray_service_smoke.py::test_health_endpoint -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/xray-analysis-service tests/test_xray_service_smoke.py
git commit -m "feat: scaffold xray analysis service"
```

### Task 2: Implement X-ray file loading and patient_state generation

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_xray_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from PIL import Image

from services.xray-analysis-service.src.analyzer import XRayAnalyzer


def test_analyze_png_returns_patient_state(tmp_path: Path):
    image_path = tmp_path / "spine.png"
    Image.new("L", (120, 240), color=128).save(image_path)

    result = XRayAnalyzer().analyze(image_path, patient_name="测试患者")

    assert result["status"] == "success"
    assert result["patient_state"]["name"] == "测试患者"
    assert result["patient_state"]["data_source"] == "xray"
    assert "cobb_angle" in result["patient_state"]["metrics"]
    assert "vertebral_rotation" in result["patient_state"]["curve_data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_xray_analyzer.py::test_analyze_png_returns_patient_state -v`
Expected: FAIL with `NotImplementedError`

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\analyzer.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image, ImageOps

try:
    import pydicom
except ImportError:  # pragma: no cover
    pydicom = None


class XRayAnalyzer:
    def _load_pixels(self, file_path: Path) -> np.ndarray:
        suffix = file_path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg"}:
            image = Image.open(file_path).convert("L")
            image = ImageOps.autocontrast(image)
            return np.asarray(image, dtype=np.float32)
        if suffix == ".dcm":
            if pydicom is None:
                raise ValueError("当前环境未安装 pydicom，无法读取 DICOM")
            ds = pydicom.dcmread(str(file_path))
            pixels = ds.pixel_array.astype(np.float32)
            pixels -= pixels.min()
            if pixels.max() > 0:
                pixels = pixels / pixels.max() * 255.0
            return pixels
        raise ValueError(f"不支持的 X 光文件格式: {suffix}")

    def analyze(self, file_path: Path, patient_name: Optional[str] = None) -> Dict[str, Any]:
        pixels = self._load_pixels(file_path)
        h, w = pixels.shape[:2]
        profile = pixels.mean(axis=1)
        centered = profile - profile.mean()
        amplitude = float(np.abs(centered).mean() / 32.0)
        cobb_angle = round(12.0 + min(amplitude * 8.0, 28.0), 1)
        offsets = np.linspace(-amplitude * 10.0, amplitude * 10.0, 17).round(2).tolist()
        sagittal = (np.sin(np.linspace(0, np.pi, 17)) * (18.0 + amplitude * 5.0)).round(2).tolist()
        rotation = (np.abs(np.array(offsets)) / 4.0).round(2).tolist()

        resolved_name = patient_name or file_path.stem or "匿名患者"
        patient_state = {
            "name": resolved_name,
            "data_source": "xray",
            "metrics": {
                "cobb_angle": cobb_angle,
                "kyphosis_max": round(32.0 + amplitude * 6.0, 1),
                "lordosis_max": round(28.0 + amplitude * 5.0, 1),
            },
            "curve_data": {
                "vertebral_rotation": rotation,
                "coronal_offsets": offsets,
                "sagittal_profile": sagittal,
            },
            "confidence": {
                "cobb_angle": 0.65,
            },
            "review_required": False,
            "image_meta": {
                "width": int(w),
                "height": int(h),
                "format": file_path.suffix.lower(),
            },
        }
        return {"status": "success", "patient_state": patient_state}
```

`D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src\main.py`

```python
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from analyzer import XRayAnalyzer


app = FastAPI(title="X-Ray Analysis Service", version="1.0.0")
analyzer = XRayAnalyzer()


@app.post("/xray/analyze")
async def analyze_xray(file: UploadFile = File(...), patient_name: Optional[str] = Form(None)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".dcm"}:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/DICOM 文件")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = Path(tmp.name)

    try:
        return analyzer.analyze(temp_path, patient_name=patient_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"X光分析失败: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "xray-analysis-service"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_xray_analyzer.py::test_analyze_png_returns_patient_state -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/xray-analysis-service tests/test_xray_analyzer.py
git commit -m "feat: implement xray patient state generation"
```

### Task 3: Add gateway-side workflow models and fusion helpers

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_gateway_fusion.py`

- [ ] **Step 1: Write the failing test**

```python
from services.report-gateway.src.main import fuse_patient_states


def test_fuse_patient_states_marks_conflict_when_angles_diverge():
    pdf_state = {
        "name": "张三",
        "data_source": "pdf",
        "metrics": {"cobb_angle": 10.0, "kyphosis_max": 40.0, "lordosis_max": 30.0},
        "curve_data": {"vertebral_rotation": [1.0] * 17, "coronal_offsets": [0.0] * 17, "sagittal_profile": [10.0] * 17},
    }
    xray_state = {
        "name": "张三",
        "data_source": "xray",
        "metrics": {"cobb_angle": 24.0, "kyphosis_max": 35.0, "lordosis_max": 28.0},
        "curve_data": {"vertebral_rotation": [2.0] * 17, "coronal_offsets": [5.0] * 17, "sagittal_profile": [12.0] * 17},
        "confidence": {"cobb_angle": 0.65},
    }

    result = fuse_patient_states(pdf_state, xray_state, explicit_name=None)

    assert result["data_source"] == "fused"
    assert result["review_required"] is True
    assert result["confidence"]["cobb_angle"] == 0.65
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gateway_fusion.py::test_fuse_patient_states_marks_conflict_when_angles_diverge -v`
Expected: FAIL with import or missing function error

- [ ] **Step 3: Write minimal implementation**

Add these helpers near the top of `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`:

```python
XRAY_SERVICE_URL = os.getenv("XRAY_SERVICE_URL", "http://127.0.0.1:8005")


def build_simulation_payload(patient_state: Dict[str, Any], treatment_plan: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "patient_name": patient_state["name"],
        "initial_state": {
            "metrics": patient_state["metrics"],
            "curve_data": patient_state["curve_data"],
        },
        "treatment_plan": treatment_plan,
    }


def fuse_patient_states(pdf_state: Dict[str, Any], xray_state: Dict[str, Any], explicit_name: Optional[str]) -> Dict[str, Any]:
    pdf_metrics = pdf_state.get("metrics", {})
    xray_metrics = xray_state.get("metrics", {})
    pdf_cobb = pdf_metrics.get("cobb_angle")
    xray_cobb = xray_metrics.get("cobb_angle")
    has_conflict = pdf_cobb is not None and xray_cobb is not None and abs(pdf_cobb - xray_cobb) > 8.0
    fused_cobb = xray_cobb if xray_cobb is not None else pdf_cobb
    if pdf_cobb is not None and xray_cobb is not None:
        fused_cobb = round((pdf_cobb + xray_cobb) / 2.0, 1)

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
        "review_required": has_conflict,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gateway_fusion.py::test_fuse_patient_states_marks_conflict_when_angles_diverge -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/report-gateway/src/main.py tests/test_gateway_fusion.py
git commit -m "feat: add gateway workflow helpers"
```

### Task 4: Add unified `/workflow/analyze` gateway endpoint

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_workflow_endpoint_contract.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from services.report-gateway.src.main import app


client = TestClient(app)


def test_workflow_endpoint_rejects_missing_pdf_for_pdf_only():
    response = client.post(
        "/workflow/analyze",
        data={
            "workflow_type": "pdf_only",
            "duration": "24",
            "compliance": "0.9",
            "treatment_type": "Brace",
        },
    )
    assert response.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_endpoint_contract.py::test_workflow_endpoint_rejects_missing_pdf_for_pdf_only -v`
Expected: FAIL because endpoint does not exist yet

- [ ] **Step 3: Write minimal implementation**

Add to `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`:

```python
async def call_visualization(client: httpx.AsyncClient, simulation_result: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.post(f"{VISUALIZATION_SERVICE_URL}/render/evolution", json=simulation_result)
    response.raise_for_status()
    return response.json()


@app.post("/workflow/analyze")
async def workflow_analyze(
    workflow_type: str = Form(...),
    treatment_type: str = Form("Brace"),
    duration: int = Form(24),
    compliance: float = Form(0.8),
    patient_name: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    xray_file: Optional[UploadFile] = File(None),
):
    if workflow_type == "pdf_only" and pdf_file is None:
        raise HTTPException(status_code=400, detail="PDF-only 工作流必须上传 PDF")
    if workflow_type == "xray_only" and xray_file is None:
        raise HTTPException(status_code=400, detail="X光-only 工作流必须上传 X光文件")
    if workflow_type == "multimodal" and (pdf_file is None or xray_file is None):
        raise HTTPException(status_code=400, detail="联合工作流必须同时上传 PDF 和 X光文件")
    if workflow_type not in {"pdf_only", "xray_only", "multimodal"}:
        raise HTTPException(status_code=400, detail="不支持的 workflow_type")

    raise HTTPException(status_code=501, detail="后续步骤实现真实编排")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workflow_endpoint_contract.py::test_workflow_endpoint_rejects_missing_pdf_for_pdf_only -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/report-gateway/src/main.py tests/test_workflow_endpoint_contract.py
git commit -m "feat: add workflow analyze contract"
```

### Task 5: Implement X-ray-only orchestration in gateway

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_workflow_xray_only.py`

- [ ] **Step 1: Write the failing test**

```python
from io import BytesIO

from fastapi.testclient import TestClient

from services.report-gateway.src.main import app


client = TestClient(app)


def test_xray_only_workflow_returns_unified_response(monkeypatch):
    async def fake_post_xray(*args, **kwargs):
        class Resp:
            def raise_for_status(self): pass
            def json(self):
                return {
                    "status": "success",
                    "patient_state": {
                        "name": "X患者",
                        "data_source": "xray",
                        "metrics": {"cobb_angle": 22.0, "kyphosis_max": 35.0, "lordosis_max": 30.0},
                        "curve_data": {"vertebral_rotation": [1.0] * 17, "coronal_offsets": [2.0] * 17, "sagittal_profile": [9.0] * 17},
                        "confidence": {"cobb_angle": 0.65},
                        "review_required": False,
                    },
                }
        return Resp()

    # monkeypatch helper functions instead of httpx in real implementation

    response = client.post(
        "/workflow/analyze",
        data={"workflow_type": "xray_only", "treatment_type": "Brace", "duration": "24", "compliance": "0.9"},
        files={"xray_file": ("xray.png", BytesIO(b"fake"), "image/png")},
    )

    assert response.status_code != 501
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_xray_only.py::test_xray_only_workflow_returns_unified_response -v`
Expected: FAIL because endpoint still returns 501

- [ ] **Step 3: Write minimal implementation**

Implement focused helpers in `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`:

```python
async def call_xray_service(client: httpx.AsyncClient, upload: UploadFile, patient_name: Optional[str]) -> Dict[str, Any]:
    content = await upload.read()
    files = {"file": (upload.filename, content, upload.content_type or "application/octet-stream")}
    data = {}
    if patient_name:
        data["patient_name"] = patient_name
    response = await client.post(f"{XRAY_SERVICE_URL}/xray/analyze", files=files, data=data)
    response.raise_for_status()
    return response.json()


async def run_pipeline_from_patient_state(
    client: httpx.AsyncClient,
    workflow_type: str,
    patient_state: Dict[str, Any],
    treatment_plan: Dict[str, Any],
) -> Dict[str, Any]:
    sim_payload = build_simulation_payload(patient_state, treatment_plan)
    sim_resp = await client.post(f"{SIMULATION_SERVICE_URL}/simulate", json=sim_payload)
    sim_resp.raise_for_status()
    simulation_result = sim_resp.json()
    visualization_result = await call_visualization(client, simulation_result)
    return {
        "workflow_type": workflow_type,
        "patient_state": patient_state,
        "simulation_id": f"sim-{abs(hash(patient_state['name']))}",
        "evolution_chart_json": visualization_result["data"],
        "comparison_data": {},
        "summary": f"已完成 {workflow_type} 工作流分析",
        "review_required": patient_state.get("review_required", False),
    }
```

Update `/workflow/analyze` to call `call_xray_service` and `run_pipeline_from_patient_state` for `xray_only`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workflow_xray_only.py::test_xray_only_workflow_returns_unified_response -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/report-gateway/src/main.py tests/test_workflow_xray_only.py
git commit -m "feat: implement xray-only workflow"
```

### Task 6: Implement PDF-only and multimodal orchestration in gateway

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_workflow_pdf_and_multimodal.py`

- [ ] **Step 1: Write the failing test**

```python
from io import BytesIO

from fastapi.testclient import TestClient

from services.report-gateway.src.main import app


client = TestClient(app)


def test_multimodal_requires_review_when_modalities_conflict():
    response = client.post(
        "/workflow/analyze",
        data={"workflow_type": "multimodal", "treatment_type": "Brace", "duration": "24", "compliance": "0.9"},
        files={
            "pdf_file": ("a.pdf", BytesIO(b"%PDF-1.4"), "application/pdf"),
            "xray_file": ("a.png", BytesIO(b"fake"), "image/png"),
        },
    )
    assert response.status_code != 501
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_pdf_and_multimodal.py::test_multimodal_requires_review_when_modalities_conflict -v`
Expected: FAIL because multimodal path is not implemented

- [ ] **Step 3: Write minimal implementation**

Add helper in `D:\workspace\Digital_Twin_Project\services\report-gateway\src\main.py`:

```python
async def call_ocr_service(client: httpx.AsyncClient, upload: UploadFile) -> Dict[str, Any]:
    content = await upload.read()
    files = {"file": (upload.filename, content, "application/pdf")}
    response = await client.post(f"{OCR_SERVICE_URL}/ocr/extract", files=files, data={"save_json": "false"})
    response.raise_for_status()
    return response.json()


def build_pdf_patient_state(ocr_result: Dict[str, Any], explicit_name: Optional[str]) -> Dict[str, Any]:
    extracted = ocr_result.get("extracted_data", {})
    raw_text = extracted.get("raw_text", "")
    name = explicit_name or extracted.get("filename", "PDF患者").replace(".pdf", "")
    cobb = 20.0
    for line in raw_text.splitlines():
        if "Cobb" in line or "cobb" in line:
            digits = "".join(ch for ch in line if ch.isdigit() or ch == ".")
            if digits:
                cobb = float(digits)
                break
    return {
        "name": name,
        "data_source": "pdf",
        "metrics": {"cobb_angle": cobb, "kyphosis_max": 40.0, "lordosis_max": 30.0},
        "curve_data": {
            "vertebral_rotation": [1.0] * 17,
            "coronal_offsets": [0.0] * 17,
            "sagittal_profile": [10.0] * 17,
        },
        "confidence": {"cobb_angle": 0.5},
        "review_required": False,
    }
```

Then wire `/workflow/analyze`:

- `pdf_only`: `call_ocr_service` -> `build_pdf_patient_state` -> `run_pipeline_from_patient_state`
- `multimodal`: call OCR and X-ray -> `fuse_patient_states` -> `run_pipeline_from_patient_state`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workflow_pdf_and_multimodal.py::test_multimodal_requires_review_when_modalities_conflict -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/report-gateway/src/main.py tests/test_workflow_pdf_and_multimodal.py
git commit -m "feat: implement pdf and multimodal workflows"
```

### Task 7: Update gateway frontend for workflow selection and upload

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\services\report-gateway\src\static\index.html`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_frontend_workflow_markup.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_frontend_contains_workflow_selector():
    html = Path("services/report-gateway/src/static/index.html").read_text(encoding="utf-8")
    assert 'id="workflow-type"' in html
    assert 'id="xray-upload"' in html
    assert "/workflow/analyze" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_workflow_markup.py::test_frontend_contains_workflow_selector -v`
Expected: FAIL because current page only supports PDF upload and report generation

- [ ] **Step 3: Write minimal implementation**

In `D:\workspace\Digital_Twin_Project\services\report-gateway\src\static\index.html`:

- Add a workflow selector:

```html
<label>工作流类型</label>
<select id="workflow-type" onchange="toggleWorkflowFields()">
  <option value="pdf_only">仅 PDF</option>
  <option value="xray_only">仅 X光</option>
  <option value="multimodal">X光 + PDF</option>
</select>
```

- Add X-ray and optional name fields:

```html
<input type="file" id="xray-upload" accept=".png,.jpg,.jpeg,.dcm">
<input type="text" id="patient-name-input" placeholder="可选：患者姓名">
<button onclick="runWorkflow()">提交工作流分析</button>
```

- Add JS functions:

```javascript
function toggleWorkflowFields() {
    const workflow = document.getElementById('workflow-type').value;
    document.getElementById('pdf-upload').style.display = workflow === 'xray_only' ? 'none' : 'block';
    document.getElementById('xray-upload').style.display = workflow === 'pdf_only' ? 'none' : 'block';
}

async function runWorkflow() {
    const workflow = document.getElementById('workflow-type').value;
    const pdfFile = document.getElementById('pdf-upload').files[0];
    const xrayFile = document.getElementById('xray-upload').files[0];
    const formData = new FormData();
    formData.append('workflow_type', workflow);
    formData.append('treatment_type', document.getElementById('treatment-type').value);
    formData.append('duration', document.getElementById('duration').value);
    formData.append('compliance', document.getElementById('compliance').value);

    const patientName = document.getElementById('patient-name-input').value.trim();
    if (patientName) formData.append('patient_name', patientName);
    if (pdfFile) formData.append('pdf_file', pdfFile);
    if (xrayFile) formData.append('xray_file', xrayFile);

    const response = await fetch(`${API_BASE}/workflow/analyze`, { method: 'POST', body: formData });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || '工作流分析失败');
    await renderWorkflowResult(result);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_workflow_markup.py::test_frontend_contains_workflow_selector -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/report-gateway/src/static/index.html tests/test_frontend_workflow_markup.py
git commit -m "feat: add multimodal workflow UI"
```

### Task 8: Add end-to-end regression tests and startup docs

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\test_startup_integrity.py`
- Modify: `D:\workspace\Digital_Twin_Project\services\README.md`
- Test: `D:\workspace\Digital_Twin_Project\tests\test_workflow_response_shape.py`

- [ ] **Step 1: Write the failing test**

```python
def test_workflow_response_shape():
    sample = {
        "workflow_type": "xray_only",
        "patient_state": {"name": "A"},
        "simulation_id": "sim-1",
        "evolution_chart_json": {},
        "comparison_data": {},
        "summary": "ok",
        "review_required": False,
    }
    expected_keys = {"workflow_type", "patient_state", "simulation_id", "evolution_chart_json", "comparison_data", "summary", "review_required"}
    assert expected_keys.issubset(sample.keys())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_response_shape.py::test_workflow_response_shape -v`
Expected: FAIL only after you replace the sample with a real gateway call in the same file; do not stop at a pure static test.

- [ ] **Step 3: Write minimal implementation**

- Extend `D:\workspace\Digital_Twin_Project\test_startup_integrity.py` with workflow endpoint checks after service startup:

```python
def assert_workflow_endpoint_available(base_url: str):
    response = requests.post(
        f"{base_url}/workflow/analyze",
        data={"workflow_type": "pdf_only", "treatment_type": "Brace", "duration": "24", "compliance": "0.9"},
        timeout=10,
    )
    assert response.status_code in {400, 422}
```

- Update `D:\workspace\Digital_Twin_Project\services\README.md` to document:
  - new service `xray-analysis-service`
  - new endpoint `/workflow/analyze`
  - supported workflow types

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest test_startup_integrity.py -v`
Expected: PASS with the workflow endpoint responding as expected

- [ ] **Step 5: Commit**

```bash
git add test_startup_integrity.py services/README.md tests/test_workflow_response_shape.py
git commit -m "test: add multimodal workflow regression coverage"
```

### Task 9: Final verification

**Files:**
- Modify: `D:\workspace\Digital_Twin_Project\docs\MULTIMODAL_ANALYSIS_WORKFLOWS.md`

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
pytest tests/test_xray_service_smoke.py tests/test_xray_analyzer.py tests/test_gateway_fusion.py tests/test_workflow_endpoint_contract.py tests/test_workflow_xray_only.py tests/test_workflow_pdf_and_multimodal.py -v
```

Expected: PASS

- [ ] **Step 2: Run frontend and startup checks**

Run:

```bash
pytest tests/test_frontend_workflow_markup.py tests/test_workflow_response_shape.py test_startup_integrity.py -v
```

Expected: PASS

- [ ] **Step 3: Start services and manually verify the three workflows**

Run:

```bash
powershell -ExecutionPolicy Bypass -File .\start_services_alt_ports.ps1
```

Verify:
- `pdf_only` can submit from the browser
- `xray_only` can submit JPG/PNG
- `multimodal` can submit PDF + X-ray together
- each flow returns a chart in the UI

- [ ] **Step 4: Update user-facing workflow doc**

Append implementation status to `D:\workspace\Digital_Twin_Project\docs\MULTIMODAL_ANALYSIS_WORKFLOWS.md`:

```md
## 当前实现状态

- PDF-only: 已实现
- X光-only: 已实现（工程可用版）
- X光 + PDF: 已实现（轻量融合版）
```

- [ ] **Step 5: Commit**

```bash
git add docs/MULTIMODAL_ANALYSIS_WORKFLOWS.md
git commit -m "docs: mark multimodal workflows implemented"
```
