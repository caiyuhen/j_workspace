from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import shutil
import tempfile
import json
from engine import SpineOCREngine

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCRService")

app = FastAPI(title="OCR Extraction Service", version="1.0.0")
ocr_engine = SpineOCREngine()

# --- 配置 ---
# 如果未设置 OUTPUT_DIR，则默认为项目根目录下的 'extracted_data'
# (假设从 services/ocr-service/src 本地运行)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
default_output_dir = os.path.join(project_root, "extracted_data")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", default_output_dir)

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Pydantic 模型 ---
class ExtractionResponse(BaseModel):
    filename: str
    extracted_data: Dict[str, Any]
    json_path: str
    status: str

# --- 端点 ---

@app.get("/health")
def health_check():
    status = "healthy" if ocr_engine.ocr_engine else "degraded (OCR engine missing)"
    return {"status": status}

@app.post("/ocr/extract", response_model=ExtractionResponse)
async def extract_text(
    file: UploadFile = File(...),
    save_json: bool = Form(True)
):
    """
    上传 PDF 文件，提取第 6, 7, 8 页（索引 5, 6, 7）的文本，
    并可选择将结果保存为 JSON 文件。
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 临时保存上传的文件
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    try:
        # 运行提取
        logger.info(f"Processing {file.filename}...")
        result = ocr_engine.extract_from_pdf(tmp_path)
        
        # 将原始文件名添加到结果中
        result['filename'] = file.filename
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        json_path = ""
        if save_json:
            # 生成 JSON 输出路径
            # 结构: OUTPUT_DIR/<filename_without_ext>.json
            base_name = os.path.splitext(file.filename)[0]
            json_filename = f"{base_name}_extracted.json"
            json_path = os.path.join(OUTPUT_DIR, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved extraction result to {json_path}")

        return {
            "filename": file.filename,
            "extracted_data": result,
            "json_path": json_path if save_json else "",
            "status": "success"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
