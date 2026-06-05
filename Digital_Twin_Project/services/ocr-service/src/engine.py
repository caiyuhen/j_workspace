import pdfplumber
import numpy as np
import logging
import fitz # PyMuPDF
from PIL import Image
import io
from typing import List, Dict, Any, Union

logger = logging.getLogger("OCREngine")

class SpineOCREngine:
    def __init__(self):
        self.ocr_engine = None
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr_engine = RapidOCR()
            logger.info("RapidOCR initialized successfully.")
        except ImportError:
            logger.error("RapidOCR not found. Please install rapidocr_onnxruntime.")
            
    def extract_from_pdf(self, file_path: str, pages_to_process: List[int] = [5, 6, 7]) -> Dict[str, Any]:
        """
        从 PDF 文件的特定页面提取文本，使用 OCR 识别 PDF 中的图像。
        根据项目需求，默认目标是第 6、7、8 页（索引 5、6、7）。
        """
        full_text = ""
        extracted_pages = []

        try:
            # 1. 尝试使用 pdfplumber 提取文本 (适用于包含文本层的 PDF)
            with pdfplumber.open(file_path) as pdf:
                for page_num in pages_to_process:
                    if page_num < len(pdf.pages):
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        if text:
                            logger.info(f"第 {page_num + 1} 页: 使用 pdfplumber 提取文本")
                            full_text += f"\n--- 第 {page_num + 1} 页 ---\n{text}"
                            extracted_pages.append({
                                "page": page_num + 1,
                                "content": text,
                                "method": "text_extraction"
                            })

            # 2. 如果 pdfplumber 提取失败或内容过少，尝试使用 OCR (适用于扫描件)
            if not full_text or len(full_text.strip()) < 10:
                logger.info("文本提取失败或内容不足。切换到 OCR 模式...")
                doc = fitz.open(file_path)
                for page_num in pages_to_process:
                    if page_num < len(doc):
                        page = doc.load_page(page_num)
                        # 将页面渲染为图像
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2倍缩放提高识别率
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        
                        # 使用 RapidOCR 处理
                        if self.ocr_engine:
                            result, elapsed = self.ocr_engine(np.array(img))
                            if result:
                                # 提取识别到的文本行
                                page_text = "\n".join([line[1] for line in result])
                                full_text += f"\n--- 第 {page_num + 1} 页 (OCR) ---\n{page_text}"
                                extracted_pages.append({
                                    "page": page_num + 1,
                                    "content": page_text,
                                    "method": "ocr"
                                })
                                logger.info(f"第 {page_num + 1} 页: 使用 OCR 提取文本")
                doc.close()
            
            return {
                "raw_text": full_text,
                "extracted_pages": extracted_pages,
                "note": "使用了 pdfplumber 和/或 RapidOCR 提取。"
            }

        except Exception as e:
            logger.error(f"PDF 提取错误: {e}")
            return {"error": str(e)}
