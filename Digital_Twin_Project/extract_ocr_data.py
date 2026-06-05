import os
import json
import pdfplumber
import numpy as np
from PIL import Image

# 初始化 OCR
ocr_engine = None
try:
    from rapidocr_onnxruntime import RapidOCR
    ocr_engine = RapidOCR()
except ImportError:
    try:
        from rapidocr import RapidOCR
        ocr_engine = RapidOCR()
    except ImportError:
        print("未找到 RapidOCR。无法继续提取文本。")
        exit(1)

source_dir = r"d:\workspace\Digital_Twin_Project\source_data\10"
json_output_path = r"d:\workspace\Digital_Twin_Project\extracted_data.json"

pdf_files = [f for f in os.listdir(source_dir) if f.endswith('.pdf')]
all_data = []

print(f"找到 {len(pdf_files)} 个 PDF 文件待处理。")

for filename in pdf_files:
    file_path = os.path.join(source_dir, filename)
    print(f"正在处理: {filename}")
    
    file_entry = {
        "filename": filename,
        "extracted_pages": {}
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # 第 6, 7, 8 页的索引为 5, 6, 7
            for page_num in [5, 6, 7]:
                page_key = f"page_{page_num + 1}"
                
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    images = page.images
                    
                    if images:
                        # 处理页面上找到的第一张图片
                        img_meta = images[0]
                        bbox = (img_meta['x0'], img_meta['top'], img_meta['x1'], img_meta['bottom'])
                        cropped = page.crop(bbox)
                        pil_img = cropped.to_image().original
                        
                        # 转换为 numpy 数组以进行 OCR
                        img_np = np.array(pil_img)
                        
                        # 运行 OCR
                        if ocr_engine:
                            try:
                                ocr_result = ocr_engine(img_np)
                                
                                # 提取文本行
                                texts = []
                                if hasattr(ocr_result, 'txts'):
                                    texts = list(ocr_result.txts)
                                elif isinstance(ocr_result, tuple) and len(ocr_result) >= 2:
                                    # 针对返回元组的旧版本/不同版本的回退
                                    # 假设文本是第二个元素
                                    texts = list(ocr_result[1])
                                elif isinstance(ocr_result, list):
                                    # 标准列表输出 [[box, text, score], ...]
                                    texts = [line[1] for line in ocr_result]
                                
                                file_entry["extracted_pages"][page_key] = {
                                    "status": "success",
                                    "text_content": texts
                                }
                                print(f"  {page_key}: 提取了 {len(texts)} 行文本。")
                                
                            except Exception as e:
                                print(f"  {page_key}: OCR 错误 - {e}")
                                file_entry["extracted_pages"][page_key] = {"status": "ocr_error", "error": str(e)}
                        else:
                             file_entry["extracted_pages"][page_key] = {"status": "ocr_engine_missing"}
                    else:
                        print(f"  {page_key}: 未找到图片。")
                        file_entry["extracted_pages"][page_key] = {"status": "no_image"}
                else:
                    print(f"  {page_key}: 页面超出范围。")
                    file_entry["extracted_pages"][page_key] = {"status": "page_not_found"}
                    
        all_data.append(file_entry)
        
    except Exception as e:
        print(f"处理 {filename} 时出错: {e}")
        all_data.append({
            "filename": filename,
            "error": str(e)
        })

# 保存为 JSON
with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"\n提取完成。数据已保存至 {json_output_path}")
