import sys
import os

LOG_FILE = "import_check.log"

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

try:
    log("Checking imports...")
    import fastapi
    log("fastapi ok")
    import uvicorn
    log("uvicorn ok")
    import pdfplumber
    log("pdfplumber ok")
    import numpy
    log("numpy ok")
    import rapidocr_onnxruntime
    log("rapidocr_onnxruntime ok")
    from engine import SpineOCREngine
    log("SpineOCREngine import ok")
    
except Exception as e:
    log(f"Import Error: {e}")
    sys.exit(1)

log("All imports successful")
