from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional
import sys

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from analyzer import XRayAnalyzer


app = FastAPI(title="X-Ray Analysis Service", version="1.0.0")
analyzer = XRayAnalyzer()


@app.post("/xray/analyze")
async def analyze_xray(file: UploadFile = File(...), patient_name: Optional[str] = Form(None)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".dcm", ".heic", ".heif"}:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/HEIC/DICOM 文件")

    temp_path: Optional[Path] = None
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
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "xray-analysis-service"}
