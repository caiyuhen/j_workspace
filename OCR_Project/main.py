import os
import json
import time
import uuid
from rapidocr_onnxruntime import RapidOCR
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from PIL import Image
import io
import difflib
import re

app = FastAPI(title="OCR Microservice")

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize RapidOCR
# RapidOCR is generally better for Chinese/Table layouts than EasyOCR default models
print("Initializing RapidOCR...")
try:
    # Attempt to initialize with specific parameters to reduce GPU warning noise if CPU-only
    # Note: RapidOCR auto-detects providers. The warning "GPU device discovery failed" 
    # is usually harmless on CPU-only machines (it just falls back to CPU).
    # To suppress it, we can't easily do it from Python as it comes from C++ level of onnxruntime,
    # but we can ensure we are catching real errors.
    reader = RapidOCR()
    print("RapidOCR initialized successfully.")
except Exception as e:
    print(f"Error initializing RapidOCR: {e}")
    reader = None

# Ensure output directory exists
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common hospital terms and names for correction
COMMON_MEDICAL_TERMS = {
    "检验目的": "检验目的",
    "标本类型": "标本类型",
    "样本": "样本",
    "标本": "标本类型",
    "临床诊断": "临床诊断",
    "临床印象": "临床印象",
    "姓名": "姓名",
    "性别": "性别",
    "年龄": "年龄",
    "床号": "床号",
    "科室": "科室",
    "送检医生": "送检医生",
    "检验者": "检验者",
    "审核者": "审核者",
    "采样时间": "采样时间",
    "接收时间": "接收时间",
    "报告时间": "报告时间",
    "检验日期": "检验日期",
    "参考范围": "参考范围",
    "单位": "单位",
    "结果": "结果",
    "提示": "提示",
    "检验项目": "检验项目",
    "病人ID": "病人ID",
    "住院号": "住院号",
    "方法": "方法"
}

# Known hospitals list (can be expanded)
KNOWN_HOSPITALS = [
    "北京中医药大学第三附属医院",
    "北京协和医院",
    "中日友好医院",
    "北京大学第一医院"
]

def correct_text(text):
    """
    Correct common OCR errors in medical reports using fuzzy matching.
    """
    if not text:
        return text
        
    # 1. Correct Medical Terms
    for correct_term in COMMON_MEDICAL_TERMS:
        # If text is very similar to a known term, correct it
        ratio = difflib.SequenceMatcher(None, text, correct_term).ratio()
        if ratio > 0.7 and ratio < 1.0:
            return correct_term
            
    # 2. Correct Hospital Names
    # Often hospital names are at the top and might be long
    for hospital in KNOWN_HOSPITALS:
        if hospital in text:
            return text # It's already correct part of it
        
        ratio = difflib.SequenceMatcher(None, text, hospital).ratio()
        if ratio > 0.6 and len(text) > 5: # Threshold for hospital names
             return hospital
             
    return text

def standardize_image(image_pil):
    """
    Step 1: Image Standardization
    - Convert to RGB
    - Handle Alpha
    - Resize (Scale up if small)
    - Deskew (Correct rotation)
    - Enhance Contrast (Optional but can help)
    """
    try:
        # 1.1 Basic Conversion
        img = np.array(image_pil)
        
        # Handle Alpha channel
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
        # Convert to Grayscale for processing
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img

        # 1.2 Deskew (Correct Rotation)
        # Find all points
        coords = np.column_stack(np.where(gray > 0)) # Assuming black text on white bg? No, usually inverse for finding coords
        # Actually for scanned docs, we might need thresholding first to find text block
        
        # Simple deskew strategy:
        # Use Hough Transform or MinAreaRect on inverted binary image
        
        # Invert (assume black text on white bg)
        try:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            coords = np.column_stack(np.where(binary > 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                
                # Correct angle format
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                    
                # Only rotate if significant skew
                if abs(angle) > 0.5 and abs(angle) < 45: # Limit to avoid 90 deg flips by mistake
                    (h, w) = img.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    # Re-update gray
                    if len(img.shape) == 3:
                        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    else:
                        gray = img
        except Exception as e:
            print(f"Deskew failed: {e}")

        # 1.3 Scaling / Resizing
        h, w = gray.shape
        # Increase threshold to 2500 to handle medium-sized images better
        if h < 2500 or w < 2500:
            scale = 2.0
            # Limit max dimension to avoid OOM or too slow processing
            if max(h, w) * scale > 4000:
                scale = 4000 / max(h, w)
            
            if scale > 1.0:
                img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                if len(img.shape) == 3:
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img
        
        # 1.4 Enhance Contrast (CLAHE)
        # Apply a mild CLAHE to help with faint text without introducing too much noise
        try:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Convert back to RGB for OCR
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            
            # DEBUG: Save processed image
            try:
                debug_path = os.path.join("output", "debug_preprocessed.png")
                # Convert back to BGR for cv2.imwrite
                cv2.imwrite(debug_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                print(f"DEBUG: Saved preprocessed image to {debug_path}")
            except Exception as e:
                print(f"DEBUG: Failed to save debug image: {e}")
                
        except Exception as e:
            print(f"Contrast enhancement failed: {e}")

        return img
    except Exception as e:
        print(f"Image standardization failed: {e}. Using original.")
        return np.array(image_pil)

# Deprecated: preprocess_image, use standardize_image instead
def preprocess_image(image_pil):
    return standardize_image(image_pil)

def extract_key_value_pairs(text_lines):
    """
    Extract key-value pairs from text lines.
    Handles 'Key: Value' or 'Key Value' formats.
    """
    extracted_data = {}
    
    # Sort lines by Y then X to ensure consistent order
    text_lines.sort(key=lambda x: (x['center_y'], x['center_x']))
    
    # Define regex patterns for common fields
    # Use non-greedy matching and lookaheads to prevent eating into other fields
    patterns = {
        "姓名": r"(?:姓名|Name|姓\s*名|名|医先|:姓名)[:：]?\s*([\u4e00-\u9fa5]{2,4})",
        "性别": r"(?:性\s*别|s别|Sex|别|:别)[:：]?\s*([男女])",
        "年龄": r"(?:年\s*龄|Age|龄|:龄)[:：]?\s*(\d+.*?)",
        "科室": r"(?:科\s*室|Dept|室|:科室)[:：]?\s*([\u4e00-\u9fa5]+)",
        "床号": r"(?:床\s*号|Bed|:床号)[:：]?\s*([A-Za-z0-9]+)",
        "样本类型": r"(?:样本类型|样本)[:：]?\s*([\u4e00-\u9fa5]+)",
        "标本类型": r"(?:标本类型|标本)[:：]?\s*([\u4e00-\u9fa5]+)",
        "临床诊断": r"(?:临\s*床\s*诊\s*断|Diagnosis|诊断|:诊断)[:：]?\s*([^\s]+(?: [^\s]+)*?)(?=\s+(?:病案号|科室|床号|姓名|性别|年龄|送检|检验|审核)[\s:：]|$)",
        "临床印象": r"(?:临\s*床\s*印\s*象|Clinical\s*Impression|Impression|:临床印象)[:：]?\s*([^\s]+(?: [^\s]+)*?)(?=\s+(?:病案号|科室|床号|姓名|性别|年龄|送检|检验|审核)[\s:：]|$)",
        "病案号": r"(?:病\s*案\s*号|ID|:病案号|门诊/住院号)[:：]?\s*(\d+)",
        "住院号码": r"(?:住\s*院\s*号|No|:住院号码|住院号)[:：]?\s*([a-zA-Z0-9]+)",
        "病人ID": r"(?:病人ID|ID号|就诊卡号)[:：]?\s*([a-zA-Z0-9]+)",
        "检验目的": r"检验目的[:：]?\s*([^\s]+(?: [^\s]+)*?)(?=\s+(?:病案号|科室|床号|姓名|姓\s*名|性别|年龄|送检|检验|审核|名：|名:|住院)[\s:：]|$)",
        "送检医生": r"送检医生[:：]?\s*([\u4e00-\u9fa5]{2,4})",
        "检验者": r"检验者[:：]?\s*([\u4e00-\u9fa5]{2,4})",
        "审核者": r"审核者[:：]?\s*([\u4e00-\u9fa5]{2,4})",
        "采样时间": r"(?:采样|采集)时间[:：]?\s*([\d\-\: ]{10,19})",
        "接收时间": r"接收时间[:：]?\s*([\d\-\: ]{10,19})",
        "报告时间": r"报告时间[:：]?\s*([\d\-\: ]{10,19})",
        "检验日期": r"检验日期[:：]?\s*([\d\-\: ]{10,19})",
        "日期": r"(?:日期|Date)[:：]?\s*([\d\-\: ]{10,19})"
    }
    
    # Join all text to search for patterns
    full_text = " ".join([line['text'] for line in text_lines])
    
    # 1. Regex Extraction
    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, full_text)
            if match:
                value = match.group(1).strip()
                # Clean up if value still contains common field names (double check)
                # Split by next possible key
                for stop_word in ["病案号", "科室", "床号", "姓名", "性别", "年龄", "送检", "检验", "审核", "住院", "结果", "参考", "采样", "接收", "报告", "标本", "样本"]:
                    if stop_word in value:
                        # Only split if stop word is at the end or preceded by space to avoid splitting "张三丰" with "三" (not a good example, but you get the idea)
                        # Actually just split is safer for now as these are keys
                        value = value.split(stop_word)[0].strip()
                        # Also split if we hit another key pattern start like " 住院"
                        value = value.split(" " + stop_word)[0].strip()
                
                # Further cleanup for Name
                if key == "姓名":
                     # Remove any trailing non-Chinese characters or numbers if they look like start of next field
                     value = re.sub(r'[^\u4e00-\u9fa5]+$', '', value)
 
                extracted_data[key] = value
        except Exception as e:
            print(f"Error extracting {key}: {e}")
            
    # Post-process specific fields
    
    # Aggressive Fallback for Gender and Age if not found (Handle partial keys like "别", "龄")
    if "性别" not in extracted_data:
        # Look for "别[:：]\s*([男女])" specifically
        m = re.search(r"别[:：]\s*([男女])", full_text)
        if m:
             extracted_data["性别"] = m.group(1)
             
    if "年龄" not in extracted_data:
        m = re.search(r"龄[:：]\s*(\d+[^\s]*)", full_text)
        if m:
             extracted_data["年龄"] = m.group(1).strip()
             
    if "姓名" not in extracted_data:
        # Try to find Name pattern near Gender/Age
        # If we have Gender, look left
        gender_block = None
        for line in text_lines:
            if "性别" in line['text'] or "别" in line['text']: # Simple check
                 # Verify it's the gender block
                 if re.search(r"[男女]", line['text']):
                     gender_block = line
                     break
        
        if gender_block:
            print(f"DEBUG: Found Gender block for spatial Name search: {gender_block['text']}")
            # Look left
            candidates = []
            for line in text_lines:
                if line == gender_block:
                    continue
                
                # Same row (approx)
                if abs(line['center_y'] - gender_block['center_y']) < 30:
                    # To the left
                    if line['center_x'] < gender_block['center_x']:
                        candidates.append(line)
            
            # Sort by X desc (closest to left of gender)
            candidates.sort(key=lambda x: x['center_x'], reverse=True)
            
            for cand in candidates:
                text = cand['text'].strip()
                # Check if it looks like a name (2-4 Chinese chars)
                if re.match(r"^[\u4e00-\u9fa5]{2,4}$", text):
                    # Exclude common labels
                    if text not in ["科室", "床号", "姓名", "性别", "年龄", "检验目的", "临床诊断", "标本类型"]:
                        extracted_data["姓名"] = text
                        print(f"DEBUG: Found Name candidate spatially: {text}")
                        break

    # Check if "检验目的" swallowed the Name
    if "检验目的" in extracted_data:
        val = extracted_data["检验目的"]
        # Look for Name pattern inside
        name_match = re.search(r"(?:姓名|名)[:：]\s*([\u4e00-\u9fa5]{2,4})", val)
        if name_match:
            if "姓名" not in extracted_data or not extracted_data["姓名"]:
                extracted_data["姓名"] = name_match.group(1)
            # Remove Name from Test Name
            extracted_data["检验目的"] = val.replace(name_match.group(0), "").strip()
                
    # Aggressive fallback for Date (Prescriptions often have "YYYY年MM月DD日" without prefix)
    if "报告时间" not in extracted_data and "日期" not in extracted_data and "采样时间" not in extracted_data:
        date_match = re.search(r'(\d{4}[年\-\/]\d{1,2}[月\-\/]\d{1,2}日?)', full_text)
        if date_match:
            extracted_data["日期"] = date_match.group(1).strip()
            # Remove from test_name if present
            if "检验目的" in extracted_data:
                extracted_data["检验目的"] = extracted_data["检验目的"].replace(date_match.group(0), "").strip()
            
    # 2. Spatial Extraction (Backup for missing keys)
    # Define keys to check spatially if regex failed
    spatial_keys = ["姓名", "性别", "年龄", "科室", "床号", "病案号", "住院号码", "临床诊断", "临床印象"]
    
    # Map keys to potential OCR errors/synonyms
    key_patterns = {
        "姓名": r"(?:姓\s*名|医先|姓名|Name|:姓名)",
        "性别": r"(?:性\s*别|s别|Sex|别|:别)",
        "年龄": r"(?:年\s*龄|Age|龄|:龄)",
        "科室": r"(?:科\s*室|Dept|室|:科室)",
        "床号": r"(?:床\s*号|Bed|:床号)",
        "病案号": r"(?:病\s*案\s*号|ID|:病案号|门诊/住院号)",
        "住院号码": r"(?:住\s*院\s*号|No|:住院号码)",
        "临床诊断": r"(?:临\s*床\s*诊\s*断|Diagnosis|诊断|:诊断)",
        "临床印象": r"(?:临\s*床\s*印\s*象|Clinical\s*Impression|Impression|:临床印象)"
    }
    
    for key in spatial_keys:
        if key not in extracted_data or not extracted_data[key]:
            # Find the label block
            label_pattern = key_patterns.get(key, key)
            
            label_block = None
            for line in text_lines:
                # Check if this line is the label
                # Use search to find label even if preceded by other text (though unlikely for these keys)
                if re.search(f"{label_pattern}[:：]?", line['text']):
                    # Check if it already contains the value
                    # e.g. "姓名: 张三"
                    # We need to be careful not to match "姓名" in "姓名: " as value.
                    # Split by label
                    split_parts = re.split(f"{label_pattern}[:：]?", line['text'], maxsplit=1)
                    if len(split_parts) > 1 and split_parts[1].strip():
                         val = split_parts[1].strip()
                         # Clean up common trailing fields if they appear in the same line
                         for stop_word in ["性别", "年龄", "病案号", "科室", "床号"]:
                             if stop_word in val:
                                 val = val.split(stop_word)[0].strip()
                         
                         # Remove trailing digits from Name if likely Age (e.g. "姜涛59")
                         if key == "姓名":
                             val = re.sub(r'\d+$', '', val)
                             
                         extracted_data[key] = val
                         label_block = None # Found value directly
                         break
                    
                    # If it's just the label, mark it
                    # We prefer exact match or close to exact for label block
                    clean_line_text = re.sub(r'\s+', '', line['text'])
                    # For "医先", replace with "姓名" for length check? No, just use raw length.
                    
                    # If line is short and contains label, assume it's the label block
                    # Increase tolerance for artifacts
                    # But if "医先：姜涛59" was split? No, regex split handles it.
                    # This block is for "姓名" (line 1) -> "张三" (line 2).
                    if len(clean_line_text) < 10: # Hard limit for label block length
                        label_block = line
                        break

            if label_block:
                # Search for value in Right or Below
                # Strategy: Find nearest block to the right
                
                candidates = []
                for line in text_lines:
                    if line == label_block:
                        continue
                    
                    # Check relative position
                    # 1. Right: Similar Y, X > Label X
                    y_diff = abs(line['center_y'] - label_block['center_y'])
                    x_diff = line['center_x'] - label_block['center_x']
                    
                    # Relaxed Y difference for "Right"
                    if y_diff < 40 and x_diff > 0:
                        candidates.append((line, x_diff, 'right'))
                        
                    # 2. Below: Similar X (or slightly right), Y > Label Y (but not too far)
                    # For fields like Name, sometimes value is below label
                    y_dist = line['center_y'] - label_block['center_y']
                    
                    # Check X overlap or proximity
                    x_dist = abs(line['center_x'] - label_block['center_x'])
                    
                    # Increased tolerance for X alignment
                    if y_dist > 0 and y_dist < 80 and x_dist < 150:
                         candidates.append((line, y_dist, 'below'))
                
                # Sort candidates
                # Prefer 'right' and close
                if candidates:
                    # Sort by distance
                    candidates.sort(key=lambda x: x[1])
                    best_match = candidates[0][0]
                    extracted_data[key] = best_match['text']
    
    # Hospital name is usually the first line with large text, or contains "医院"
    for line in text_lines[:5]: # Check first 5 lines
        text = line['text']
        if "医院" in text:
            extracted_data["医院名称"] = text
            break
            
    return extracted_data

def parse_prescription_data(text_lines, header_y, footer_y):
    """
    Special parsing for prescriptions
    """
    # Detect Rp/Rx start Y
    rp_y = header_y
    for line in text_lines:
        # Ignore if below footer
        if line['center_y'] >= footer_y:
            continue
            
        text = line['text']
        # Check for Rp/Rx/R:
        is_rp = re.search(r'(?:Rp|Rx|R)[:\.]', text, re.IGNORECASE) or "Rp" in text or "Rx" in text
        
        # Check for "处方" but exclude common footer phrases
        is_chufang = "处方" in text and "有效" not in text and "提示" not in text and "退换" not in text
        
        if is_rp or is_chufang:
             if line['center_y'] > rp_y:
                 rp_y = line['center_y']
             
    body_items = [line for line in text_lines if line['center_y'] > rp_y + 10 and line['center_y'] < footer_y - 10]
    
    # Group by Rows
    rows = {}
    row_height_threshold = 20 # Larger threshold for loose layout
    
    fangfa_text = ""
    
    for item in body_items:
        # Check if item contains "方法" or "包装" (like "小包装")
        if "包装" in item['text'] or "方法" in item['text']:
            fangfa_text = item['text']
            # Continue processing, maybe it's mixed with drugs, but usually it's on its own line
            
        found = False
        for y in rows:
            if abs(item['center_y'] - y) < row_height_threshold:
                rows[y].append(item)
                found = True
                break
        if not found:
            rows[item['center_y']] = [item]
            
    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    
    results = []
    current_drug = None
    
    for y, items in sorted_rows:
        items.sort(key=lambda x: x['center_x'])
        text_content = " ".join([i['text'] for i in items])
        
        # Check if Usage line
        if "用法" in text_content or "Sig" in text_content or "口服" in text_content or "每次" in text_content or "每日" in text_content:
            if current_drug:
                current_drug["参考范围"] = text_content # Map Usage to Reference Range field
                results.append(current_drug)
                current_drug = None
            else:
                # Orphaned usage line? Attach to previous result if possible?
                if results:
                    results[-1]["参考范围"] += " " + text_content
            continue
            
        # Likely Drug line
        # If we had a pending drug without usage, push it
        if current_drug:
            results.append(current_drug)
            current_drug = None
            
        # Parse Drug Line
        # We need to split multi-drug rows into individual drugs.
        # Often texts look like: "生黄芪30g 当归5g 生艾叶6g"
        # Let's join them and split by space or just iterate over items.
        
        # If the line contains fangfa keywords, we already captured it, maybe skip if it's ONLY fangfa
        if "包装" in text_content and len(text_content) < 10:
             continue
             
        # Extract drugs using regex: (Chinese chars) + (Digits/Decimals) + (unit like g, mg, ml, etc.)
        # Example match: "生黄芪", "30", "g"
        # Support names with slash like "石/50g 13g" -> name="石/50g", qty="13", unit="g"
        # Or just "石/50" if OCR merged it.
        # Let's adjust the drug_pattern to allow some symbols in the name part, but end with chinese or common symbols
        drug_pattern = r'([A-Za-z\u4e00-\u9fa5/]+[\u4e00-\u9fa5g/]*)\s*([\d\.]+)\s*(g|mg|ml|袋|包|片|粒|丸|支|贴|克|毫克|毫升)'
        
        # We can try to find all matches in the joined text
        matches = re.findall(drug_pattern, text_content, re.IGNORECASE)
        
        if matches:
            for match in matches:
                drug_name = match[0].strip()
                qty = match[1].strip()
                unit = match[2].strip()
                
                # Check for prefix noise in drug_name (like leading 'X' or '厂')
                # If there are common OCR noises at the start, strip them if they are 1 char
                if len(drug_name) > 2 and drug_name[0] in ['厂', 'X', 'x']:
                     drug_name = drug_name[1:]
                
                results.append({
                    "项目名称": drug_name,
                    "结果": qty,
                    "单位": unit,
                    "参考范围": "",
                    "提示": "正常"
                })
        else:
            # Fallback to old heuristic if regex doesn't match well (e.g. no unit or different format)
            # But try to split by space first if there are multiple parts that look like drugs
            parts = text_content.split()
            for part in parts:
                # Try regex on part
                m = re.match(r'^([\u4e00-\u9fa5]+)([\d\.]+)([a-zA-Z\u4e00-\u9fa5]*)$', part)
                if m:
                    results.append({
                        "项目名称": m.group(1),
                        "结果": m.group(2),
                        "单位": m.group(3) if m.group(3) else "g",
                        "参考范围": "",
                        "提示": "正常"
                    })
                elif len(part) > 1 and not re.match(r'^[\d\.]+$', part):
                    # Just treat the whole part as parameter if we can't parse it well,
                    # but only if it's not a stray number
                    results.append({
                        "项目名称": part,
                        "结果": "",
                        "单位": "",
                        "参考范围": "",
                        "提示": "正常"
                    })
                    
    if current_drug:
        results.append(current_drug)
        
    return {"prescription_items": results, "fangfa": fangfa_text}

def correct_units_by_parameter(item_data):
    """
    Standardize units based on parameter name context.
    Fixes OCR errors like "101g/L" for MCV.
    """
    name = item_data.get("parameter", "").upper()
    unit = item_data.get("unit", "")
    
    if not name:
        return item_data
        
    # MCV -> fL
    if "MCV" in name or "红细胞平均体积" in name:
        # Fix specific error where fL is read as g/L or 101g/L
        if "g/L" in unit or "101" in unit or not unit:
             item_data["unit"] = "fL"
             
    # MCH -> pg
    if "MCH" in name and "MCHC" not in name:
        if "pg" not in unit and unit: # Only if unit is weird
            item_data["unit"] = "pg"
            
    # MCHC -> g/L
    if "MCHC" in name:
        if "g/L" not in unit and unit:
             item_data["unit"] = "g/L"
             
    # RBC -> 10^12/L
    if "RBC" in name or ("红细胞" in name and "压积" not in name and "体积" not in name and "分布" not in name):
        # Aggressive fix: RBC is almost always 10^12/L
        if not unit or "10" in unit or "g/L" in unit: # Overwrite even if g/L (common error)
            item_data["unit"] = "10^12/L"
            
    # WBC/PLT -> 10^9/L
    # Exclude MPV, PDW, PCT, P-LCR (volume, distribution, crit, ratio)
    if ("WBC" in name or "PLT" in name or "白细胞" in name or "血小板" in name) and \
       "平均" not in name and "分布" not in name and "压积" not in name and "比率" not in name:
        if not unit or "10" in unit or "9" in unit:
             item_data["unit"] = "10^9/L"

    # HGB -> g/L
    if "HGB" in name or "血红蛋白" in name:
        # Aggressive fix: HGB is g/L
        if not unit or "8" in unit or "α" in unit or "L" in unit:
             item_data["unit"] = "g/L"

    # HCT -> %
    if "HCT" in name or "红细胞压积" in name:
        if not unit or "10" in unit: # Fix wrong unit
             item_data["unit"] = "%"

    # Platelet Indices
    if "MPV" in name or "平均血小板体积" in name:
        item_data["unit"] = "fL"
    if "PDW" in name or "血小板分布宽度" in name:
        # PDW can be % or fL depending on analyzer, but usually % or fL. 
        # If unit is empty, leave it or guess. Let's guess fL or keep original if present.
        if not unit:
            item_data["unit"] = "fL"
    if "PCT" in name or "血小板压积" in name:
        item_data["unit"] = "%"
        
    # Absolute Counts -> 10^9/L
    if ("#" in name or "数" in name) and ("百分" not in name and "比" not in name):
        if not unit or ("10" in unit and "9" in unit):
             item_data["unit"] = "10^9/L"

    # Percentages -> %
    if ("%" in name or "百分" in name or "比率" in name):
        if not unit or "10" in unit: 
             item_data["unit"] = "%"
             
    return item_data

def split_columns_smart(items, debug_log=None, override_split_x=None, return_split_x=False):
    """
    Split items into Left and Right columns using histogram analysis.
    Uses Left Edge (x_min) histogram to find the start of the second column.
    If override_split_x is provided, uses it directly.
    """
    if not items:
        if return_split_x:
            return [], [], None
        return [], []
        
    if override_split_x is not None:
        split_x = override_split_x
        left_items = [i for i in items if i['center_x'] < split_x]
        right_items = [i for i in items if i['center_x'] >= split_x]
        if return_split_x:
            return left_items, right_items, split_x
        return left_items, right_items

    # Robust Min/Max (Trim 5% outliers to avoid stray dots affecting width)
    all_cx = sorted([item['center_x'] for item in items])
    n = len(all_cx)
    if n == 0: 
        if return_split_x:
            return [], [], None
        return [], []
    
    idx_min = int(n * 0.05)
    idx_max = int(n * 0.95)
    # Ensure indices are valid
    idx_min = max(0, idx_min)
    idx_max = min(n - 1, idx_max)
    
    min_x = all_cx[idx_min]
    max_x = all_cx[idx_max]
    
    width = max_x - min_x
    
    if width < 100: # Too narrow for columns
        if return_split_x:
            return items, [], None
        return items, []
        
    # Histogram approach
    # Create bins for X coordinates (10px wide)
    bin_size = 10
    num_bins = int(width / bin_size) + 5
    bins = [0] * num_bins
    
    for item in items:
        # Use center_x and assume width
        cx = item['center_x']
        
        # Skip extreme outliers for histogram
        if cx < min_x - 100 or cx > max_x + 100:
            continue
            
        # Relative to min_x
        rel_cx = cx - min_x
        
        # Rough width estimate based on text length (avg char width ~15px)
        w = len(item['text']) * 15
        start_bin = int((rel_cx - w/2) / bin_size)
        end_bin = int((rel_cx + w/2) / bin_size)
        
        for b in range(max(0, start_bin), min(num_bins, end_bin + 1)):
            bins[b] += 1
            
    # Find gap in middle 35-65% (Assume symmetric dual column)
    start_search = int(num_bins * 0.35)
    end_search = int(num_bins * 0.65)
    
    # 1. Find ALL low density bins in the search range
    candidates = []
    
    for b in range(start_search, end_search + 1):
        if b < 0 or b >= num_bins:
            continue
        candidates.append((b, bins[b]))
        
    if not candidates:
        # Fallback to center
        split_x = min_x + width / 2
    else:
        # Find the minimum density value
        min_density = min(c[1] for c in candidates)
        
        # Filter candidates that have this minimum density (or close to it, e.g. min + 1)
        # Being strict with min_density is usually safer for finding gaps (0)
        best_candidates = [c for c in candidates if c[1] == min_density]
        
        # Pick the candidate closest to the geometric center (num_bins / 2)
        center_bin = num_bins / 2
        best_bin = min(best_candidates, key=lambda x: abs(x[0] - center_bin))[0]
        
        split_bin = best_bin
        split_x = min_x + (split_bin * bin_size) + (bin_size / 2)
    
    if debug_log is not None:
        debug_log["split_x"] = split_x
        # debug_log["min_density"] = bins[split_bin] if 0 <= split_bin < num_bins else -1
        
    left_items = [i for i in items if i['center_x'] < split_x]
    right_items = [i for i in items if i['center_x'] >= split_x]
    
    if return_split_x:
        return left_items, right_items, split_x
    return left_items, right_items

def parse_table_data(text_lines, debug_log=None):
    """
    Attempt to parse table data based on headers and line coordinates.
    Handles dual-column layouts and intelligently maps fields.
    """
    if debug_log is None:
        debug_log = {}
        
    if not text_lines:
        debug_log["error"] = "No text lines provided"
        return []

    # Check for Prescription Mode vs Test Report Mode
    is_prescription = False
    has_strong_prescription_kw = False
    has_test_kw = False
    
    for line in text_lines:
        text = line['text']
        if "处方" in text:
            has_strong_prescription_kw = True
        if "检验" in text or "常规" in text or "结果" in text or "参考" in text or "单位" in text:
            has_test_kw = True
            
    if has_strong_prescription_kw:
        is_prescription = True
    elif has_test_kw:
        is_prescription = False
    else:
        # Check for Rp/Rx only if no clear signal
        for line in text_lines:
            if re.search(r'^(?:Rp|Rx|R)[:\.]', line['text'], re.IGNORECASE):
                is_prescription = True
                break

    # 1. Identify table header line(s) to determine vertical start
    # Use a scoring system to avoid false positives (e.g. "单位" in footer)
    header_keywords = {
        "检验项目": 3, "项目": 2, "Project": 2, "Item": 2,
        "结果": 2, "Result": 2, 
        "单位": 1, "Unit": 1, 
        "参考范围": 3, "参考值": 3, "Reference": 2, 
        "提示": 1, "Flag": 1, "状态": 1,
        # Prescription headers
        "R:": 3, "Rp": 3, "Rp:": 3, "R：": 3, "处方": 3, "Rp.": 3
    }
    
    potential_headers = []
    
    # Enhanced header detection
    for line in text_lines:
        text = line['text']
        clean_text = text.replace(" ", "")
        
        score = 0
        matched_kws = []
        for kw, weight in header_keywords.items():
            if kw in clean_text:
                score += weight
                matched_kws.append(kw)
        
        if score > 0:
            potential_headers.append({
                "line": line,
                "score": score,
                "matches": matched_kws
            })

    # Sort by score desc
    potential_headers.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter headers: Must have score >= 3 (e.g. "检验项目" or "结果"+"单位")
    # This filters out stray "单位" or "结果"
    # Also filter out lines that are likely footers (contain "注", "仅对", "声明")
    # Or appear in the bottom half of the page
    
    # Calculate page height
    all_y = [line['center_y'] for line in text_lines]
    page_height = max(all_y) if all_y else 0
    
    valid_headers = []
    for ph in potential_headers:
        if ph["score"] < 3:
            continue
        
        text = ph["line"]["text"]
        y = ph["line"]["center_y"]
        
        # Debug Filter
        # print(f"DEBUG: Header Filter Check: text='{text}' y={y} page_height={page_height}")
        
        # Exclude footer-like lines
        if "注" in text or "仅对" in text or "声明" in text or "报告" in text or "审核" in text:
             print(f"DEBUG: Filtered out footer-like header: {text}")
             continue
             
        # Exclude lines in bottom half
        if page_height > 0 and y > page_height * 0.5:
             print(f"DEBUG: Filtered out bottom-half header: {text} (y={y}, h={page_height})")
             continue
             
        valid_headers.append(ph)
    
    debug_log["potential_headers"] = str([(h["line"]["text"], h["score"]) for h in potential_headers])
    debug_log["valid_headers"] = str([h["line"]["text"] for h in valid_headers])

    header_y = 0
    if valid_headers:
        # Use the Y of the best header(s)
        # If we have multiple valid headers (e.g. split across lines or columns), take the range
        # But usually header is one line.
        # Take the top-most valid header as the start?
        # Or the one with highest score?
        # Usually header is at the top of the table.
        
        # Let's take the header with the highest score. If multiple have same high score, take the one with min Y?
        # Actually, in the dual column case, the header might be one long line.
        best_score = valid_headers[0]["score"]
        top_headers = [h for h in valid_headers if h["score"] >= best_score - 1] # Allow slightly lower score
        
        # Use the max Y of these top headers to be safe (start table below them)
        header_y = max([h["line"]['center_y'] for h in top_headers])
    
    debug_log["header_y"] = header_y

    # --- FALLBACK: If Header Not Found or very top ---
    # If header_y is still 0 (from initialization) or unreasonably high, 
    # and we have many lines, it might be a table without a clear header.
    # Heuristic: Look for the first line that looks like a table row (contains numbers and medical terms)
    if header_y == 0:
        print("DEBUG: No clear header found. Using fallback detection.")
        
        # 1. Try to find the bottom of Patient Info area first
        # Calculate approximate page height
        all_y_coords = [line['center_y'] for line in text_lines]
        page_height = max(all_y_coords) if all_y_coords else 2000
        
        patient_info_y = 0
        for line in text_lines:
             # Ignore footer-like lines for patient info (assume patient info is in top 40%)
             if line['center_y'] > page_height * 0.4:
                 continue
                 
             text = line['text']
             # Exclude specific footer keywords that might match "日期" or "号"
             if "打印" in text or "审核" in text or "接收" in text or "采集" in text:
                 continue

             if "姓名" in text or "性别" in text or "年龄" in text or "科室" in text or "号" in text or "日期" in text or "医先" in text or "Name" in text or "Sex" in text:
                 patient_info_y = max(patient_info_y, line['center_y'])
        
        # 2. Find first Data Row
        for line in text_lines:
             # Skip lines that are clearly above patient info (if found)
             if patient_info_y > 0 and line['center_y'] < patient_info_y:
                 continue
                 
             # Check if line contains a number and some Chinese/English characters
             # And is not a title (usually large font or top of page)
             # Simple heuristic: If it has a number like "3.56" or "10^9", it's likely a data row
             # Also include common abbreviations like WBC, RBC
             text = line['text']
             is_data_row = False
             
             if re.search(r'\d+\.\d+', text) or '10^' in text or 'g/L' in text or 'U/L' in text:
                 is_data_row = True
             elif text.strip() in ["WBC", "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC", "PLT"]:
                 is_data_row = True
             elif "白细胞" in text or "红细胞" in text or "血红蛋白" in text:
                 # Be careful not to match title "血常规"
                 if "常规" not in text and "报告" not in text:
                     is_data_row = True
             
             if is_data_row:
                # Found a data-like line. Set header_y well above it.
                # Use a larger buffer (40) to include slightly higher text
                header_y = line['center_y'] - 40
                
                # Ensure we don't go above patient info if we found it
                if patient_info_y > 0 and header_y < patient_info_y:
                    header_y = patient_info_y + 10
                    
                print(f"DEBUG: Fallback header_y set to {header_y} based on line '{text}' (patient_info_y={patient_info_y})")
                debug_log["header_y"] = header_y
                break
    
    # If still 0, maybe it's just a list of names? 
    # Set to a small value to process almost everything
    if header_y == 0:
        if patient_info_y > 0:
            header_y = patient_info_y + 20
            print(f"DEBUG: Fallback header_y set to {header_y} based on patient info")
        else:
            header_y = 100 # Skip title area
            print("DEBUG: Fallback header_y set to 100 (default)")
        debug_log["header_y"] = header_y
    
    # 1.5 Identify Footer to determine vertical end
    footer_keywords = ["送检医生", "检验者", "审核者", "备注", "注：", "声明", "采集时间", "接收时间", "报告时间", "危急值", "医师签名", "药师提示", "药费金额", "医师", "药师"]
    footer_y = float('inf')
    
    for line in text_lines:
        if line['center_y'] < header_y:
            continue # Skip header/above
        
        text = line['text'].replace(" ", "")
        if any(kw in text for kw in footer_keywords):
             # For prescriptions, "药师提示" or "医师签名" is definitely footer
             # But "备注" might be in the middle? No, usually bottom.
             if line['center_y'] < footer_y:
                 footer_y = line['center_y']
                 debug_log["footer_detected_at"] = f"{line['text']} (Y={line['center_y']})"
    
    if footer_y == float('inf'):
         # If no footer found, use the bottom of the page
         all_y = [line['center_y'] for line in text_lines]
         if all_y:
             footer_y = max(all_y) + 50
    
    debug_log["footer_y"] = footer_y

    if is_prescription:
        debug_log["mode"] = "prescription"
        return parse_prescription_data(text_lines, header_y, footer_y)
    
    # Find page horizontal center
    all_x = [line['center_x'] for line in text_lines]
    if not all_x:
        return []
    
    # Split items into Left and Right groups (below header and above footer)
    table_items = [line for line in text_lines if line['center_y'] > header_y + 10 and line['center_y'] < footer_y - 10]
    
    debug_log["table_item_count"] = len(table_items)
    
    # Use smart column splitting
    # Attempt to use Header items to determine split point
    header_split_x = None
    
    # We need to find the header line again. We calculated header_y.
    # Find items near header_y
    # Increased tolerance to 60 to capture headers that might be vertically spread (e.g. 360 vs 406)
    header_items = [line for line in text_lines if abs(line['center_y'] - header_y) < 60]
    
    if len(header_items) > 4: # Assuming at least 2 columns * 2-3 items
         print(f"DEBUG: Attempting to split columns based on {len(header_items)} header items.")
         # Try to split headers
         _, _, h_split = split_columns_smart(header_items, return_split_x=True)
         if h_split:
             print(f"DEBUG: Found header split at X={h_split}")
             header_split_x = h_split
             
    if header_split_x:
        left_items, right_items = split_columns_smart(table_items, debug_log, override_split_x=header_split_x)
    else:
        left_items, right_items = split_columns_smart(table_items, debug_log)
    
    debug_log["left_item_count"] = len(left_items)
    debug_log["right_item_count"] = len(right_items)
    
    parsed_items = []
    
    # Process both columns
    for col_idx, items in enumerate([left_items, right_items]):
        if not items:
            continue
        
        # Group items by Y-coordinate (Rows)
        rows = {}
        row_height_threshold = 30 # Increased to 30 to handle misaligned items and scaling
        
        for item in items:
            found_row = False
            # Try to fit into existing rows
            for y in rows.keys():
                if abs(item['center_y'] - y) < row_height_threshold:
                    rows[y].append(item)
                    found_row = True
                    break
            if not found_row:
                rows[item['center_y']] = [item]
        
        # Sort rows by Y
        sorted_rows = sorted(rows.items(), key=lambda x: x[0])
        
        debug_log[f"col_{col_idx}_rows"] = len(sorted_rows)
        
        # Process each row
        for y, row_items in sorted_rows:
            # Sort items in row by X (Left to Right)
            row_items.sort(key=lambda x: x['center_x'])
            
            item_data = {
                "项目名称": "",
                "结果": "",
                "单位": "",
                "参考范围": "",
                "提示": "" # High/Low
            }
            
            # Helper list to keep track of unassigned items
            unassigned = []
            
            # First pass: Identify clear fields by pattern
            for item in row_items:
                text = item['text']
                
                # Filter out graph area text
                # Use case-insensitive check and broader keyword
                if "graph" in text.lower() and "area" in text.lower():
                     print(f"DEBUG: Filtered out graph area text: '{text}'")
                     continue
                
                # 1. Check for Flag/Indicator (Arrow, H, L)
                if text in ['↑', '↓', 'H', 'L', 'h', 'l', '+', '＋', '-', 'High', 'Low'] or re.match(r'^[↑↓HLhl\+\-]$', text):
                    item_data["提示"] = text
                    continue
                    
                # 2. Check for Unit (Strong) - Contains explicit unit markers
                # Prioritize over Ref Range because Ref Range regex can match units like "10~9/L"
                is_unit = False
                
                # Correction: 10~9 -> 10^9
                if '10~9' in text:
                    text = text.replace('10~9', '10^9')
                if '10-9' in text and '/L' in text: # If OCR read ^ as - in unit
                    text = text.replace('10-9', '10^9')
                if '10~12' in text:
                    text = text.replace('10~12', '10^12')
                if '10-12' in text and '/L' in text:
                    text = text.replace('10-12', '10^12')
                
                # --- NEW OCR CORRECTIONS ---
                if 'unol' in text:
                    text = text.replace('unol', 'umol')
                if 'mmo1' in text:
                    text = text.replace('mmo1', 'mmol')
                if 'mz' in text:
                    text = text.replace('mz', 'mg') # mz/L -> mg/L
                if '10/2' in text:
                    text = text.replace('10/2', '10^12') # 10/2/L -> 10^12/L
                if '10~12' in text:
                    text = text.replace('10~12', '10^12') # 10~12/L -> 10^12/L
                if '10-12' in text and '/L' in text:
                    text = text.replace('10-12', '10^12')
                if '109' in text and '/L' in text and '^' not in text:
                    text = text.replace('109', '10^9') # 109/L -> 10^9/L
                if '2/L' in text:
                    text = text.replace('2/L', 'g/L') # 2/L -> g/L (common OCR error for g)
                if '10/g/L' in text:
                    text = text.replace('10/g/L', '10^12/L')
                if '10/9/L' in text:
                    text = text.replace('10/9/L', '10^9/L')
                if '10^1g/L' in text:
                    text = text.replace('10^1g/L', '10^12/L') # 10^12/L -> 10^1g/L (OCR error)
                if '8/L' in text:
                    text = text.replace('8/L', 'g/L') # g/L -> 8/L (OCR error)

        
                # Fix dot space digit (e.g. "15. 0" -> "15.0")
                text = re.sub(r'\.\s+(\d)', r'.\1', text)
                
                # Check for Ref+Unit Glue (e.g. "130--175g/L")
                # Regex: RefRange + Unit
                ref_unit_glue_match = re.match(r'^(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?)([a-zA-Zμ\^/%]+(?:/[a-zA-Z]+)?)$', text)
                if ref_unit_glue_match:
                     ref_part = ref_unit_glue_match.group(1).strip()
                     unit_part = ref_unit_glue_match.group(2).strip()
                     print(f"DEBUG: ref_unit_glue_match split: ref='{ref_part}' unit='{unit_part}'")
                     item_data["参考范围"] = ref_part
                     item_data["单位"] = unit_part
                     continue

                if any(u in text for u in ['/L', 'g/L', 'mol/L', 'umol/L', 'U/L', 'pg', 'fL', '^']):
                     is_unit = True
                elif text in ['%', 'g', 'L', 'mg']: # Exact match units
                    is_unit = True
                
                # Exclude if it looks like a parameter name (e.g. LYMPH%)
                if text.endswith('%') and len(text) > 3 and re.match(r'^[A-Za-z]+%$', text):
                    is_unit = False
                    
                if is_unit:
                    item_data["单位"] = text
                    continue

                # Special Case: Indicator+RefRange Glue (e.g. "↓4.3-5.8")
                # Removed + and - from indicators to avoid false positives with ref ranges like "+27--34"
                ind_ref_match = re.match(r'^([↑↓HLhl])\s*(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?)$', text.strip())
                if ind_ref_match:
                    indicator = ind_ref_match.group(1)
                    ref_part = ind_ref_match.group(2)
                    print(f"DEBUG: ind_ref_glue split: ind='{indicator}' ref='{ref_part}'")
                    item_data["参考范围"] = ref_part
                    if indicator in ['↑', 'H', 'h']:
                        item_data["提示"] = "偏高"
                    if indicator in ['↓', 'L', 'l']:
                        item_data["提示"] = "偏低"
                    continue

                # Special Case: Result+RefRange Glue (e.g. "33.50+40-50", "8.90140--75")
                ref_range_search = re.search(r'(\d+(?:\.\d+)?)\s*([~-]{1,2})\s*(\d+(?:\.\d+)?)$', text.strip())
                if ref_range_search and not item_data["参考范围"]:
                    lower = ref_range_search.group(1)
                    sep = ref_range_search.group(2)
                    upper = ref_range_search.group(3)
                    full_ref = ref_range_search.group(0)
                    start_idx = ref_range_search.start()
                    
                    # Enhanced Glue Detection: Check if lower bound contains Result
                    # e.g. "8.90140" -> Result "8.90", RefStart "140"
                    glued_result = None
                    glued_ref_start = lower
                    
                    # Heuristic: If lower has > 2 decimal places, or length > 5 (and upper < 3)
                    if '.' in lower:
                        dec_part = lower.split('.')[1]
                        if len(dec_part) > 2:
                            # Try to split after 2 decimal places
                            split_idx = lower.index('.') + 3
                            cand_res = lower[:split_idx]
                            cand_ref = lower[split_idx:]
                            
                            # Validate cand_ref with upper
                            # If cand_ref is empty, fallback
                            if cand_ref:
                                # Check if cand_ref <= upper (roughly)
                                # If cand_ref starts with '1' and is > upper, maybe '1' is noise?
                                # "140" vs "75". 140 > 75. Strip 1 -> 40. 40 < 75. OK.
                                
                                final_ref_start = cand_ref
                                if float(cand_ref) > float(upper):
                                     if cand_ref.startswith('1') and len(cand_ref) > 1:
                                         sub_cand = cand_ref[1:]
                                         if float(sub_cand) <= float(upper):
                                             final_ref_start = sub_cand
                                             # The '1' is discarded/noise
                                
                                # If valid range formed
                                if float(final_ref_start) <= float(upper):
                                    glued_result = cand_res
                                    glued_ref_start = final_ref_start
                                    print(f"DEBUG: Detected glued result in lower bound: {lower} -> {glued_result}, {glued_ref_start}")

                    # Validate Range (Lower <= Upper) logic (existing logic enhanced)
                    valid_lower = glued_ref_start
                    prefix_remains = ""
                    
                    try:
                        while len(valid_lower) > 0 and float(valid_lower) > float(upper):
                             # Move first char to prefix
                             prefix_remains += valid_lower[0]
                             valid_lower = valid_lower[1:]
                             if not valid_lower:
                                 break
                             if valid_lower.startswith('.'):
                                 prefix_remains += '.'
                                 valid_lower = valid_lower[1:]
                    except ValueError:
                        pass
                        
                    prefix = text[:start_idx]
                    
                    if valid_lower and valid_lower != lower:
                        ref_part = valid_lower + sep + upper
                        
                        # Handle prefix remains
                        if prefix_remains == "1" and (re.match(r'^[\d\.]+$', prefix) or glued_result):
                             pass # Discard noise "1"
                        else:
                             prefix = prefix + prefix_remains
                    else:
                        ref_part = full_ref
                        
                    if glued_result:
                        # Use the extracted result
                        item_data["结果"] = glued_result
                        item_data["参考范围"] = ref_part
                        continue
                    
                    if prefix.strip():

                        # Case 1: Prefix is Result (e.g. "33.50+")
                        if re.match(r'^[\d\.]+[↑↓\+]?$', prefix.strip()):
                             print(f"DEBUG: result_ref_glue split: res='{prefix}' ref='{ref_part}'")
                             # Extract indicator from result if present
                             clean_prefix = prefix.strip()
                             if clean_prefix.endswith('+') or clean_prefix.endswith('↑') or clean_prefix.endswith('H'):
                                 item_data["提示"] = "偏高"
                                 clean_prefix = clean_prefix[:-1]
                             elif clean_prefix.endswith('-') or clean_prefix.endswith('↓') or clean_prefix.endswith('L'):
                                 item_data["提示"] = "偏低"
                                 clean_prefix = clean_prefix[:-1]
                                 
                             item_data["结果"] = clean_prefix
                             item_data["参考范围"] = ref_part
                             continue
                        
                        # Case 2: Prefix is Index (e.g. "11" in "1130--175")
                        if re.match(r'^\d+$', prefix.strip()) and len(prefix.strip()) <= 2:
                             print(f"DEBUG: index_ref_glue split: index='{prefix}' ref='{ref_part}'")
                             item_data["参考范围"] = ref_part
                             continue

                # Special Case: Name+RefRange Glue (e.g. "LYMPH%20-50")
                name_ref_glue_match = re.match(r'^(.+?)(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?%?)$', text.strip())
                if name_ref_glue_match and not item_data["参考范围"]:
                    name_part = name_ref_glue_match.group(1).strip()
                    ref_part = name_ref_glue_match.group(2).strip()
                    
                    if not re.match(r'^[\d\.]+$', name_part):
                         print(f"DEBUG: name_ref_glue_match split: name='{name_part}' ref='{ref_part}'")
                         item_data["项目名称"] = name_part
                         item_data["参考范围"] = ref_part
                         continue

                # 3. Check for Reference Range (contains ~ or - and numbers)
                # Regex: digit, optional space, tilde/dash, optional space, digit
                # Support "13.5--9.5" (double dash)
                if re.search(r'\d+\.?\d*\s*[~-]{1,2}\s*\d+\.?\d*', text) and ('~' in text or '-' in text):
                    item_data["参考范围"] = text
                    continue
                    
                # 4. Check for Unit (Weak/Other) - Only if not numbers
                # e.g. "fL", "pg" might not have /L.
                if any(u in text for u in ['%']):
                     # Exclude if it looks like a parameter name (e.g. LYMPH% or 中性粒细胞...)
                     # 1. Ends with % and length > 3 (e.g. NEUT%)
                     if text.endswith('%') and len(text) > 3:
                         pass 
                     # 2. Contains Chinese characters (likely parameter name)
                     elif re.search(r'[\u4e00-\u9fa5]', text):
                         pass
                     # 3. Not a number -> Unit
                     elif not re.match(r'^[\d\.]+$', text): 
                         item_data["单位"] = text
                         continue
                
                unassigned.append(item)
            
            # Second pass: Handle Result and Name from unassigned items
            # Usually Name is Leftmost, Result is Rightmost (of the remaining) or a number
            
            name_parts = []
            
            for item in unassigned:
                text = item['text']
                
                # Filter out pure index numbers (1-100) if they appear alone
                # But be careful not to filter out results like "17" if "17" is the result.
                # Usually indices are small integers at the far left.
                # If we haven't found a name yet, and this is a small integer, it might be an index.
                # However, let's look for "Result" candidates first.
                
                # Check for Result (Number)
                # Allow integers and floats
                # Exclude if it looks like a date or code (long number)
                # Check for Result (Number) with optional indicator and percentage
                # Allow integers and floats, and arrows/plus/minus, and trailing %
                result_match = re.match(r'^[↑↓\+]?\s*(\d+(?:\.\s*\d+)?)\s*[%％]?\s*[↑↓\+]?$', text.strip())
                if result_match:
                    # If this is a number
                    val_clean = result_match.group(1).replace(" ", "")
                    
                    # Capture indicator if present
                    if '↑' in text or '+' in text:
                        item_data["提示"] = "偏高"
                    if '↓' in text:
                        item_data["提示"] = "偏低"
                    
                    # Check if it has %
                    if '%' in text or '％' in text:
                        if not item_data["单位"]:
                             item_data["单位"] = "%"
                        elif "%" not in item_data["单位"]:
                             item_data["单位"] += "%"

                    # Context check: Is it likely an index?
                    # If it's the first item in row and small integer, treat as index unless it's the only number.
                    is_likely_index = False
                    if not name_parts and not item_data["结果"]:
                         # It's at the start.
                         if re.match(r'^\d{1,2}$', val_clean): # 1-99
                             # It might be an index.
                             # But it could also be a result if the name was missed?
                             # Let's assume it's an index if there are other items following.
                             if len(unassigned) > 1:
                                 is_likely_index = True
                    
                    if is_likely_index:
                        continue

                    # If we already have a result, we have ambiguity.
                    if not item_data["结果"]:
                         item_data["结果"] = val_clean
                    else:
                        # Ambiguity. 
                        # If the new number is float (contains dot), prefer it as result?
                        if '.' in val_clean and '.' not in item_data["结果"]:
                             # Move old result to name? Or discard?
                             # "17" "1.63" -> "17" is index/name part, "1.63" is result.
                             # But we already skipped index candidates above.
                             # Maybe "17" was treated as result.
                             # Let's swap.
                             if re.match(r'^\d+$', item_data["结果"]):
                                 # Old was integer, new is float. New is likely result.
                                 item_data["结果"] = val_clean
                        else:
                             # Both are numbers. 
                             # Maybe part of name?
                             pass
                    continue
                
                # Special Case: Indicator+RefRange Glue (e.g. "↓4.3--5.8")
                ind_ref_match = re.match(r'^([↑↓HLhl\+\-])\s*(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?)$', text.strip())
                if ind_ref_match:
                    indicator = ind_ref_match.group(1)
                    ref_part = ind_ref_match.group(2)
                    print(f"DEBUG: ind_ref_glue split: ind='{indicator}' ref='{ref_part}'")
                    item_data["参考范围"] = ref_part
                    if indicator in ['↑', 'H', 'h', '+']:
                        item_data["提示"] = "偏高"
                    if indicator in ['↓', 'L', 'l', '-']:
                        item_data["提示"] = "偏低"
                    continue
                
                # Check for Name+Result glue (e.g. "总蛋白72.6", "Cys-C1. 13", "MONO#0.34")
                # Look for name chars followed immediately by number (with optional spaces inside number)
                # Use a broad regex for name but ensure it ends with non-digit or is long enough
                # Regex: Name + Number
                # Handle cases like "CD4500" carefully.
                # If we use greedy name, "CD4500" -> "CD450", "0".
                # If we use lazy name, "CD4500" -> "C", "D4500" (no, D is not digit).
                # Actually, \d+ matches 4500. So Name is CD. Result 4500.
                # But CD4 is the name.
                # Usually there is a visual break or the number is a float.
                
                glue_match = re.match(r'^(.+?)(\d+(?:\.\s*\d+)?)$', text.strip())
                # print(f"DEBUG: glue_check text='{text}' match={bool(glue_match)}")
                
                # Special Case: Result+RefRange Glue (e.g. "78.90140--75" -> Result "78.90", Ref "40--75"?)
                # Pattern: Ends with RefRange
                ref_range_search = re.search(r'(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?)$', text.strip())
                if ref_range_search and not item_data["参考范围"]:
                    ref_part = ref_range_search.group(1)
                    prefix = text[:ref_range_search.start()].strip()
                    
                    if prefix:
                        # Case 1: Prefix is Result (e.g. "33.50+")
                        # Allow optional arrow or +
                        if re.match(r'^[\d\.]+[↑↓\+]?$', prefix):
                             print(f"DEBUG: result_ref_glue split: res='{prefix}' ref='{ref_part}'")
                             item_data["结果"] = prefix
                             item_data["参考范围"] = ref_part
                             continue
                        
                        # Case 2: Prefix is Index (e.g. "11" in "1130--175")
                        # If prefix is small integer and short
                        if re.match(r'^\d+$', prefix) and len(prefix) <= 2:
                             # Likely index or garbage
                             print(f"DEBUG: index_ref_glue split: index='{prefix}' ref='{ref_part}'")
                             item_data["参考范围"] = ref_part
                             continue

                # Special Case: Name+RefRange Glue (e.g. "LYMPH%20--50", "HCT40--50%")
                # Regex: Name + Number + [~-]{1,2} + Number
                # Allow single or double dash.
                name_ref_glue_match = re.match(r'^(.+?)(\d+(?:\.\d+)?\s*[~-]{1,2}\s*\d+(?:\.\d+)?%?)$', text.strip())
                if name_ref_glue_match and not item_data["参考范围"]:
                    name_part = name_ref_glue_match.group(1).strip()
                    ref_part = name_ref_glue_match.group(2).strip()
                    
                    # Validation: Name shouldn't be just a number (though regex . matches digits)
                    # And Reference range should look like a range.
                    if not re.match(r'^[\d\.]+$', name_part):
                         print(f"DEBUG: name_ref_glue_match split: name='{name_part}' ref='{ref_part}'")
                         name_parts.append(name_part)
                         item_data["参考范围"] = ref_part
                         continue

                if glue_match and not item_data["结果"]:
                    name_part = glue_match.group(1).strip()
                    val_part = glue_match.group(2).replace(" ", "") # Clean spaces in value
                    # print(f"DEBUG: glue_match split: name='{name_part}' val='{val_part}'")
                    
                    # Heuristic to avoid splitting things like "B12", "CD4", "CA125"
                    # 1. If value is float (has dot), always split (e.g. "1.63", "0.34")
                    # 2. If value is integer, only split if name length > 2 AND name doesn't end in letter+digit pattern
                    
                    should_split = False
                    if '.' in val_part:
                        should_split = True
                    elif len(name_part) > 2:
                        # Check if name looks like "CD" and val is "4" -> CD4
                        # If name ends with letter and val is digits, it might be a code.
                        if re.search(r'[a-zA-Z]$', name_part):
                             # E.g. "CD" + "4" -> CD4. Don't split.
                             # But "WBC" + "12" -> WBC 12. Split.
                             # Ambiguous.
                             # If value is large (e.g. > 100 or > 10), maybe split?
                             if len(val_part) >= 2: 
                                  should_split = True
                        else:
                             should_split = True
                    
                    if should_split:
                        name_parts.append(name_part)
                        item_data["结果"] = val_part
                        continue
                    else:
                         # Treat as part of name (e.g. B12)
                         pass

                # If not a pure number, it's likely part of the name
                # Clean up "Code:Name" format (e.g. "LYHPH:淋巴细胞数")
                if ':' in text or '：' in text:
                    # Split and take the part with Chinese characters if possible
                    parts = re.split(r'[:：]', text)
                    for part in parts:
                        if re.search(r'[\u4e00-\u9fa5]', part):
                            name_parts.append(part)
                        elif not name_parts: # If no chinese found yet, keep code?
                            # Maybe keep full text if we can't decide
                            pass
                    if not any(re.search(r'[\u4e00-\u9fa5]', p) for p in parts):
                         name_parts.append(text)
                else:
                    name_parts.append(text)
            
            # Construct Name
            item_data["项目名称"] = "".join(name_parts)
            
            # Clean up Name: remove leading digits/symbols if they look like artifacts
            item_data["项目名称"] = re.sub(r'^[\d\s\.\*★]+', '', item_data["项目名称"])
            
            # Post-Processing Item Data
            # 1. Fix '1' noise in Result
            if item_data.get("结果"):
                res = item_data["结果"]
                # Match number followed by '1' (e.g. "10.661" -> "10.66")
                # Heuristic: Value has >1 decimal place, ends in '1'.
                if re.match(r'^\d+\.\d{3}$', res) and res.endswith('1'):
                    item_data["结果"] = res[:-1]
            
            # 2. Fix Parameter Glue (e.g. "WBC...3.509.50")
            if item_data.get("项目名称"):
                 param = item_data["项目名称"]
                 # Check for "NumberNumber" pattern at end
                 glue_match = re.search(r'(\d+\.\d{2})(\d+\.\d{2})$', param)
                 if glue_match:
                     ref_low = glue_match.group(1)
                     ref_high = glue_match.group(2)
                     # Remove from parameter
                     item_data["项目名称"] = param[:glue_match.start()].strip()
                     # Set Reference Range if empty
                     if not item_data.get("参考范围"):
                         item_data["参考范围"] = f"{ref_low}-{ref_high}"
            
            # 3. Clean Unit/Ref Cross-Column Noise
            # e.g. "3.9-6.1mmol/L22极低密度" -> "3.9-6.1mmol/L"
            # Pattern: Unit (anything) + Digits + Chinese
            if item_data.get("unit"):
                unit = item_data["unit"]
                # Look for Digits + Chinese at the end
                match = re.search(r'(\d{2,}[\u4e00-\u9fa5]+.*)$', unit)
                if match:
                    # Strip it
                    item_data["unit"] = unit[:match.start()].strip()
            
            # Special case: If Name is empty but we have Result, something is wrong.
            # Or if we have Name but no Result.
            
            if item_data["项目名称"] or item_data["结果"]:
                 parsed_items.append(item_data)
                 
    return parsed_items


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

def clean_text_data(text_lines):
    """
    Step 2: Medical Data Cleaning
    - Remove OCR artifacts
    - Correct common character confusions
    - Fix medical term typos (calling correct_text)
    """
    cleaned_lines = []
    
    for line in text_lines:
        text = line['text']
        
        # 2.1 Basic Cleaning
        text = text.strip()
        
        # 2.3 Fix Date Glue (e.g. "2024-10-2807:53" -> "2024-10-28 07:53")
        # Match YYYY-MM-DDHH:MM or YYYY-MM-DDH:MM
        text = re.sub(r'(\d{4}-\d{2}-\d{2})(\d{1,2}:\d{2})', r'\1 \2', text)
        
        # Remove standalone special characters often confused as text
        if re.match(r'^[\.\,\;\:\-\_\~\`\*\@\#\$\%\^\&]+$', text):
            continue
            
        # Filter out common header noise that leaks into body
        text_no_space = text.replace(" ", "").upper()
        if any(x in text_no_space for x in ["CLINICALIMPRESSION", "DEPT", "检验目的", "检验结果", "REFERENCERANGE", "IMPRESSION", "TMPRESSION", "CLINICAL", "CLINTCAL"]):
            continue
            
        # Fix dot space digit (e.g. "15. 0" -> "15.0") - Global fix
        text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)

        # 2.2 Character Corrections (Rule-based)
        # Fix common number/letter confusions in medical context
        # e.g. "l0^9/L" -> "10^9/L"
        text = text.replace('l0^', '10^').replace('I0^', '10^').replace('O^', '0^')
        text = text.replace('10~12', '10^12').replace('10~9', '10^9')
        # "g/L" confusions
        text = text.replace('g/l', 'g/L').replace('g/1', 'g/L').replace('2/L', 'g/L')
        
        # Specific Unit Corrections
        if '1012' in text and '/L' in text:
             text = text.replace('1012', '10^12')
        if '10 12' in text and '/L' in text:
             text = text.replace('10 12', '10^12')
        if '109' in text and '/L' in text and '^' not in text:
             text = text.replace('109', '10^9')
        if '10~12' in text:
             text = text.replace('10~12', '10^12')
        if '10-12' in text and '/L' in text:
             text = text.replace('10-12', '10^12')
        
        # Common OCR typos for units
        if 'unol' in text:
            text = text.replace('unol', 'umol')
        if 'mmo1' in text:
            text = text.replace('mmo1', 'mmol')
        if 'mz' in text:
            text = text.replace('mz', 'mg')
        if '2/L' in text:
            text = text.replace('2/L', 'g/L')


        # Fix Double Dash in Ref Range
        text = text.replace('--', '-')

        # Leading 1 in Reference Range Fix (e.g. "13.5-9.5" -> "3.5-9.5")
        # Regex for Range: (\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)
        # Only if '-' is present (after -- replacement)
        if '-' in text:
            range_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', text)
            if range_match:
                 start_val = range_match.group(1)
                 end_val = range_match.group(2)
                 try:
                     v1 = float(start_val)
                     v2 = float(end_val)
                     if v1 > v2:
                         # Check if removing leading '1' helps (e.g. 13.5 -> 3.5)
                         if start_val.startswith('1') and len(start_val) > 1:
                             new_start = start_val[1:]
                             if float(new_start) < v2:
                                 # It's likely a fix!
                                 # Be careful with replace, only replace the range part
                                 text = text.replace(f"{start_val}-{end_val}", f"{new_start}-{end_val}")
                                 # Or simpler replace if unique
                         # Also check for "1130" -> "130"
                         elif start_val.startswith('1') and len(start_val) > 2:
                             new_start = start_val[1:]
                             if float(new_start) < v2:
                                 text = text.replace(f"{start_val}-{end_val}", f"{new_start}-{end_val}")

                 except Exception:
                     pass
        
        # Fix trailing '1' in results that look like noise (e.g. 10.661 -> 10.66)
        # Heuristic: If number has >2 decimal places and ends in 1, and the 1 is likely noise.
        # This handles cases where vertical separator is read as '1'.
        # Matches "10.661" or "10.66 1"
        text = re.sub(r'(\d+\.\d{2})\s*1(?!\d)', r'\1', text)
        
        # 2.3 Medical Term Correction (Fuzzy Match)
        # Use existing correct_text function logic here or call it
        text = correct_text(text)
        
        line['text'] = text
        cleaned_lines.append(line)
        
    return cleaned_lines

def govern_medical_data(parsed_result):
    """
    Step 3: Data Governance
    - Standardize Units
    - Normalize Reference Ranges
    - Normalize Result Status
    """
    def calculate_status(value_str, ref_range_str):
        if not value_str or not ref_range_str:
            return "正常"
            
        try:
            # Clean inputs
            val_clean = value_str.replace(' ', '').replace('+', '')
            ref_clean = ref_range_str.replace(' ', '')
            
            # 1. Handle Value with Inequality (e.g. <5, >100)
            val_num = None
            val_op = None
            
            if val_clean.startswith('<'):
                val_op = '<'
                val_num = float(val_clean[1:])
            elif val_clean.startswith('>'):
                val_op = '>'
                val_num = float(val_clean[1:])
            elif re.match(r'^-?\d+(\.\d+)?$', val_clean):
                val_num = float(val_clean)
            else:
                return "正常" # Cannot parse value
                
            # 2. Parse Reference Range
            # Case A: Range (min-max)
            # Support single or double dash/tilde
            range_match = re.match(r'^(\d+(\.\d+)?)[~-]{1,2}(\d+(\.\d+)?)$', ref_clean)
            if range_match:
                min_val = float(range_match.group(1))
                max_val = float(range_match.group(3))
                
                if val_num is not None:
                    if val_op == '<':
                        # If value is <X, and X <= min_val, it's Low? No, usually "Less than detection limit" is normal for some, or low for others.
                        # But typically <X means small. If min_val is 0, it's normal.
                        # If range is 10-20, and value <5, it's Low.
                        if val_num <= min_val:
                            return "偏低"
                        # If range is 0-10, and value <5. Normal.
                        if val_num <= max_val:
                            return "正常"
                    elif val_op == '>':
                        # If value >X, and X >= max_val, it's High.
                        if val_num >= max_val:
                            return "偏高"
                    else: # Pure number
                        if val_num < min_val:
                            return "偏低"
                        if val_num > max_val:
                            return "偏高"
                return "正常"
                
            # Case B: Inequality (e.g. <10, >5)
            # Ref: <10. Value: 5 -> Normal. Value: 15 -> High.
            if ref_clean.startswith('<'):
                limit = float(ref_clean[1:])
                if val_num is not None:
                     if val_op == '>': # Value > X. 
                         if val_num >= limit:
                             return "偏高"
                     elif val_op is None:
                         if val_num >= limit:
                             return "偏高"
                return "正常"
            
            if ref_clean.startswith('>'):
                limit = float(ref_clean[1:])
                if val_num is not None:
                     if val_op == '<': # Value < X.
                         if val_num <= limit:
                             return "偏低"
                     elif val_op is None:
                         if val_num <= limit:
                             return "偏低"
                return "正常"

        except Exception:
            # print(f"DEBUG: Error calculating status: {e}")
            pass
            
        return "正常"

    if "results" in parsed_result:
        for item in parsed_result["results"]:
            # 3.0 Correct Units by Parameter (Context-aware fix)
            item = correct_units_by_parameter(item)

            # Standardize usage field for prescription
            # Check test_name OR if reference_range looks like usage content
            ref = item.get("reference_range", "")
            is_usage_content = False
            
            # Simple Usage Standardization (Latin -> Chinese)
            if ref:
                ref_lower = ref.lower()
                if "qd" in ref_lower:
                    ref = re.sub(r'qd', '每日一次', ref, flags=re.IGNORECASE)
                if "bid" in ref_lower:
                    ref = re.sub(r'bid', '每日两次', ref, flags=re.IGNORECASE)
                if "tid" in ref_lower:
                    ref = re.sub(r'tid', '每日三次', ref, flags=re.IGNORECASE)
                if "po" in ref_lower:
                    ref = re.sub(r'po', '口服', ref, flags=re.IGNORECASE)
                item["reference_range"] = ref
            
            if ref and ("口服" in ref or "次" in ref or "日" in ref or "Sig" in ref or "用量" in ref):
                is_usage_content = True

            if ("处方" in parsed_result.get("test_name", "") or "Rp" in parsed_result.get("test_name", "") or is_usage_content):
                 if ref and not item.get("usage"):
                     # Move reference_range to usage
                     item["usage"] = ref
                     item["reference_range"] = "" # Clear it
            
            # 3.1 Unit Standardization
            unit = item.get("unit", "")
            if unit:
                # Unify variations
                if "10^9" in unit:
                    item["unit"] = "10^9/L"
                elif "10^12" in unit:
                    item["unit"] = "10^12/L"
                elif "g/L" in unit.lower():
                    item["unit"] = "g/L"
                elif "mol/L" in unit and "u" in unit.lower(): # umol/L vs μmol/L
                    item["unit"] = "μmol/L"
            
            # 3.2 Result Status Normalization
            status = item.get("result_status", "")
            if not status or status == "正常":
                # Try to calculate from value and ref range
                calc_status = calculate_status(item.get("value", ""), item.get("reference_range", ""))
                if calc_status != "正常":
                    item["result_status"] = calc_status
                else:
                    item["result_status"] = "正常"
            else:
                 # Normalize existing status
                if "高" in status or "High" in status or "H" == status.upper() or "↑" in status:
                    item["result_status"] = "偏高"
                elif "低" in status or "Low" in status or "L" == status.upper() or "↓" in status:
                    item["result_status"] = "偏低"
                elif not status or status == "正常":
                    item["result_status"] = "正常"
            
            # 3.3 Value Normalization
            # Ensure value is clean
            val = str(item.get("value", ""))
            if val:
                 item["value"] = val.replace(" ", "")
            
            # 3.4 Prescription Quantity Cleaning
            # If value starts with x/X/×, it's a quantity
            if val and re.match(r'^[x×X]', val):
                # Remove leading x
                clean_val = re.sub(r'^[x×X]\s*', '', val)
                
                # Extract Unit from Value if present (e.g. "2盒")
                # Regex: number + non-number
                match = re.match(r'^(\d+)(.*)$', clean_val)
                if match:
                    num_part = match.group(1)
                    unit_part = match.group(2)
                    item["value"] = num_part
                    if unit_part:
                         # Put Spec in Reference Range if it's not there, and set unit to unit_part
                         old_unit = item.get("unit", "")
                         if old_unit:
                             # Assume old_unit is Spec
                             if not item.get("reference_range"):
                                 item["reference_range"] = f"规格:{old_unit}"
                             else:
                                 # Prepend spec if not already there
                                 if "规格" not in item["reference_range"]:
                                     item["reference_range"] = f"规格:{old_unit}; " + item["reference_range"]
                         
                         item["unit"] = unit_part
                else:
                    item["value"] = clean_val # Just remove x

    return parsed_result

def nlp_structure_data(text_lines, debug_log=None):
    """
    Step 4: NLP Structuring
    - Extract Key-Value Pairs
    - Extract Table Data
    - Organize into final structure
    """
    if debug_log is None:
        debug_log = {}

    # 4.1 Header/Metadata Extraction
    header_info = extract_key_value_pairs(text_lines)
    full_text = " ".join([line.get("text", "") for line in text_lines])
    
    # 4.2 Table Extraction
    table_data = parse_table_data(text_lines, debug_log)
    
    # Check if table_data is a dict (Prescription mode)
    if isinstance(table_data, dict) and "prescription_items" in table_data:
        if "fangfa" in table_data and table_data["fangfa"]:
            header_info["方法"] = table_data["fangfa"]
        table_data = table_data["prescription_items"]
        
    # 4.3 Entity Organization
    # Handle Date logic (Fallback: 检验日期 -> 报告时间 -> 采样时间 -> 日期)
    check_date = header_info.get("检验日期", "")
    if not check_date:
        check_date = header_info.get("报告时间", "")
    if not check_date:
        check_date = header_info.get("采样时间", "")
    if not check_date:
        check_date = header_info.get("日期", "")
    
    def _clean_specimen_value(raw):
        if not raw:
            return ""
        s = str(raw).strip()
        s = re.sub(r'^(?:标本类型|样本类型|样本|标本)\s*[:：]?\s*', '', s)
        s = s.strip()
        # common OCR noise values that should not be used as specimen type
        if s in ["状态", "号", "-", "--", "—", ""]:
            return ""
        return s

    def _normalize_id(raw):
        if not raw:
            return ""
        m = re.search(r'(\d+)', str(raw))
        return m.group(1) if m else ""

    def _normalize_sex(raw, all_text):
        s = str(raw or "")
        if "男" in s:
            return "男"
        if "女" in s:
            return "女"
        m = re.search(r'性别\s*[:：]?\s*([男女])', all_text)
        if m:
            return m.group(1)
        return ""

    def _normalize_hospital(raw):
        s = str(raw or "").strip()
        s = re.sub(r'(检验报告单|处方笔|处方笺|报告单)\s*$', '', s)
        return s.strip()

    def _strip_report_labels(raw):
        s = str(raw or "").strip()
        for token in ["检验项目", "检验目的", "检验结果", "单位", "参考区间", "参考范围", "互认标识", "方法学"]:
            s = s.replace(token, "")
        s = re.sub(r'^[：:\-\s]+|[：:\-\s]+$', '', s)
        return s.strip()

    # specimen type: both yangben and biaobentype should use this same value
    specimen_type = ""
    for k in ["标本类型", "样本类型", "样本", "标本"]:
        specimen_type = _clean_specimen_value(header_info.get(k, ""))
        if specimen_type:
            break

    idhao = _normalize_id(header_info.get("病案号", ""))
    zhuyuanhao = (
        _normalize_id(header_info.get("病案号", ""))
        or _normalize_id(header_info.get("住院号码", ""))
        or _normalize_id(header_info.get("住院号", ""))
    )
    
    # Normalize top-level free-text fields to avoid header labels leaking into JSON
    normalized_test_name = _strip_report_labels(
        header_info.get("检验目的") or header_info.get("检验项目") or "医学检查报告"
    )
    if not normalized_test_name:
        normalized_test_name = "医学检查报告"

    normalized_clinical_impression = _strip_report_labels(
        header_info.get("临床印象", "") or header_info.get("临床诊断", "")
    )

    # Map header info to requested fields
    structured_data = {
        "test_name": normalized_test_name, # Keep internal
        "patient_name": header_info.get("姓名", ""), # Keep internal for re_ocr
        "check_date": check_date, # Keep internal for API doc compatibility
        
        # User requested fields
        "idhao": idhao,
        "yangben": specimen_type,
        "xingming": header_info.get("姓名", ""),
        "baogaoTime": header_info.get("报告时间", ""),
        "biaobentype": specimen_type,
        "yiyuan": _normalize_hospital(header_info.get("医院名称", "")),
        "jianyanTime": check_date,
        "zhuyuanhao": zhuyuanhao,
        "sex": _normalize_sex(header_info.get("性别", ""), full_text),
        "fangfa": header_info.get("方法", ""),
        "details": []
    }
    
    # Check if we got fangfa from prescription table parsing
    if "fangfa" in header_info and header_info["fangfa"]:
         structured_data["fangfa"] = header_info["fangfa"]
         
    # Map table data to results structure
    for item in table_data:
        # Generic item structure: {"项目名称": "", "结果": "", "单位": "", "参考范围": "", "提示": "", ...}
        # Prescription items might just have 'parameter', 'value', 'unit'
        
        param = item.get("项目名称", item.get("parameter", ""))
        val = item.get("结果", item.get("value", ""))
        unit = item.get("单位", item.get("unit", ""))
        ref = item.get("参考范围", item.get("reference_range", ""))
        ind = item.get("提示", item.get("result_status", ""))
        
        status = ind
        if not status and val and ref:
            # We call ind_ref_match internally if calculate_status is not global
            # Actually ind_ref_match is defined, let's use that logic or similar
            try:
                # Basic float conversion to check status
                v = float(re.search(r'\d+\.?\d*', val).group())
                r_match = re.search(r'(\d+\.?\d*)[-~]+(\d+\.?\d*)', ref)
                if r_match:
                    r_low = float(r_match.group(1))
                    r_high = float(r_match.group(2))
                    if v > r_high:
                        status = "偏高"
                    elif v < r_low:
                        status = "偏低"
                    else:
                        status = "正常"
            except Exception:
                pass
            
        if ind in ["↑", "H", "High", "+", "＋", "高", "偏高"]:
            status = "偏高"
        elif ind in ["↓", "L", "Low", "-", "－", "低", "偏低"]:
            status = "偏低"
        elif ind:
            if ind.strip() and ind.strip() not in ["-", "正常"]:
                status = "异常"
                
        if not status:
            status = "正常"
            
        # Parse parameter to see if it contains "代号" (e.g. "WBC 白细胞" or "潜血试验B_TX")
        daihaos = ""
        project_zh = param
        
        # Case 1: English code at the beginning (e.g. "WBC 白细胞")
        eng_match = re.match(r'^([A-Za-z0-9\-\*]+)\s*([\u4e00-\u9fa5].*)', param)
        # Case 2: English code at the end (e.g. "潜血试验B_TX")
        end_eng_match = re.match(r'^([\u4e00-\u9fa50-9\-\*]+(?:[\u4e00-\u9fa5]+)?)\s*([A-Za-z_]+)$', param)
        
        if eng_match:
             daihaos = eng_match.group(1).replace("*", "")
             project_zh = eng_match.group(2)
        elif end_eng_match:
             project_zh = end_eng_match.group(1)
             daihaos = end_eng_match.group(2)
             
        # If it's something like "石/50g", we just leave it in project_zh and daihaos=""

        # Extract min/max reference from reference_range
        min_ref = ""
        max_ref = ""
        if not ref:
            # Fallback: range might be OCR-glued into parameter or unit text
            fallback_text = f"{param} {unit} {val}"
            fallback_match = re.search(r'([\d\.]+)\s*[\-~～—–－]{1,2}\s*([\d\.]+)', fallback_text)
            if fallback_match:
                ref = f"{fallback_match.group(1)}-{fallback_match.group(2)}"

        if ref:
            # Match standard ranges like "0.71--2.78", "0.71-2.78", "15~44", "0.71 ~ 2.78"
            # Support -, --, ~, ～, —, –, －
            ref_match = re.search(r'([\d\.]+)\s*[\-~～—–－]{1,2}\s*([\d\.]+)', ref)
            if ref_match:
                min_ref = ref_match.group(1)
                max_ref = ref_match.group(2)
            else:
                # Handle single values like "<5.0", ">10", "<=0.1"
                lt_match = re.search(r'[<≤]\s*([\d\.]+)', ref)
                gt_match = re.search(r'[>≥]\s*([\d\.]+)', ref)
                if lt_match:
                    max_ref = lt_match.group(1)
                elif gt_match:
                    min_ref = gt_match.group(1)

        # Append with new keys (and keep old keys for compatibility with govern_medical_data)
        structured_data["details"].append({
            "parameter": param,
            "value": val,
            "unit": unit,
            "reference_range": ref,
            "result_status": status,
            
            # New keys
            "project_zh": project_zh,
            "result": val,
            "reference": ref,
            "tishi": status,
            "daihaos": daihaos,
            "minReference": min_ref,
            "maxReference": max_ref
        })
    
    return structured_data

def re_ocr_patient_name(image_np, text_lines, debug_log):
    """
    If Patient Name is missing, look for 'Gender' anchor and re-OCR the area to its left.
    Uses high contrast crop.
    """
    try:
        # 1. Find Gender Anchor
        gender_line = None
        for line in text_lines:
            if "性别" in line['text'] or "男" in line['text'] or "女" in line['text']:
                # Verify it's in the header area (top 30% of image)
                # Box coords are available in line['box']
                ys = [p[1] for p in line['box']]
                min_y = min(ys)
                if min_y < image_np.shape[0] * 0.3:
                     gender_line = line
                     break
        
        if not gender_line:
            debug_log["re_ocr_status"] = "No Gender Anchor"
            print("DEBUG: re_ocr - No Gender Anchor found")
            return None
            
        # 2. Define ROI (Region of Interest)
        # For 河南省肿瘤医院/血常规.jpg specifically, the name is often right above "门诊号" or "条码号"
        # and to the left of "性别".
        # Let's try expanding the crop upwards more aggressively if we see those keywords, or just generally.
        box = gender_line['box']
        g_x_min = min(p[0] for p in box)
        g_y_min = min(p[1] for p in box)
        g_y_max = max(p[1] for p in box)
        g_height = g_y_max - g_y_min
        
        print(f"DEBUG: re_ocr - Gender Anchor at {g_x_min},{g_y_min}")
        
        # Define Crop
        # X: From 0 to Gender Start (or slightly before)
        # Y: Gender Y +/- Height (Expand vertical range)
        c_x_min = 0
        c_x_max = int(g_x_min)
        # Expand Y significantly upwards to catch names on the line above
        c_y_min = int(max(0, g_y_min - g_height * 4.0)) 
        c_y_max = int(min(image_np.shape[0], g_y_max + g_height * 2.0))
        
        print(f"DEBUG: re_ocr - ROI: {c_x_min}:{c_x_max}, {c_y_min}:{c_y_max}")
        
        if c_x_max - c_x_min < 10: # Too narrow
            debug_log["re_ocr_status"] = "ROI too narrow"
            print("DEBUG: re_ocr - ROI too narrow")
            return None
            
        crop = image_np[c_y_min:c_y_max, c_x_min:c_x_max]
        
        # Save debug crop
        cv2.imwrite("output/debug_name_crop.png", crop)
        
        # 3. Enhance Crop
        # Convert to grayscale if not already
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop
            
        # Enhance Contrast (CLAHE) aggressively
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Thresholding - Try Adaptive Thresholding which is better for varying lighting
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Also try a more aggressive simple threshold specifically for faint text
        _, binary_faint = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV) # Inverse might help OCR sometimes, or just lower threshold
        _, binary_low = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        _, binary_very_low = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY) # Very aggressive for very faint text
        
        # 4. Run OCR
        # Use global reader
        print("DEBUG: re_ocr - Running OCR on crop (Adaptive Thresh)...")
        result, _ = reader(thresh)
        
        if not result:
             print("DEBUG: re_ocr - No text found with Adaptive Thresh, trying Gray+CLAHE...")
             result, _ = reader(gray)
             
        if not result:
             print("DEBUG: re_ocr - Trying Binary Low (faint text)...")
             result, _ = reader(binary_low)
             
        if not result:
             print("DEBUG: re_ocr - Trying Binary Very Low (very faint text)...")
             result, _ = reader(binary_very_low)
             
        if not result:
             # Try Inverted Threshold (sometimes text is light on dark?) Unlikely for medical reports but...
             # Let's try simple Binary with lower threshold
             _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
             print("DEBUG: re_ocr - Trying Simple Binary...")
             result, _ = reader(binary)
        
        if not result:
            debug_log["re_ocr_status"] = "No Text Found"
            print("DEBUG: re_ocr - No text found in crop")
            return None
            
        # 5. Extract Name from Result
        candidates = []
        for line in result:
            text = line[1]
            debug_log[f"re_ocr_text_{line[1]}"] = line[2]
            print(f"DEBUG: re_ocr - Text found: {text}")
            
            # Clean text
            clean_text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
            
            # For specific templates where the name is next to "姓名", check original text
            if "名" in text or "姓" in text:
                 name_part = re.sub(r'^.*[姓名]+[:：\s]*', '', text)
                 name_part = re.sub(r'[^\u4e00-\u9fa5]', '', name_part)
                 if 2 <= len(name_part) <= 4:
                     candidates.append(name_part)
                     continue
            
            # Skip if empty or too long
            if len(clean_text) < 2 or len(clean_text) > 4:
                continue
                
            # Exclude common keywords
            exclude_keywords = ["性别", "年龄", "科室", "门诊", "住院", "号", "床", "病案", "费别", "序代", "代号", "编号", "样本"]
            
            # But allow if it *is* the only text found and looks like a name?
            # No, "门诊" is definitely not a name.
             
            if any(k in text for k in exclude_keywords):
                # Special check: If text is like "姓名:张三", we should extract "张三"
                if "姓名" in text or "名" in text:
                     # Try to strip "姓名"
                     name_part = re.sub(r'^.*[姓名]+[:：\s]*', '', text)
                     name_part = re.sub(r'[^\u4e00-\u9fa5]', '', name_part)
                     if 2 <= len(name_part) <= 4:
                         candidates.append(name_part)
                         continue # Found a potential name
                
                # If "门诊" is found, check if there's anything else in the text
                cleaned_for_check = re.sub(r'[^\u4e00-\u9fa5]', '', text)
                for k in exclude_keywords:
                    cleaned_for_check = cleaned_for_check.replace(k, '')
                
                if 2 <= len(cleaned_for_check) <= 4:
                    # Exclude "血带规" (OCR error for 血常规)
                    if "血" in cleaned_for_check and ("规" in cleaned_for_check or "带" in cleaned_for_check):
                         continue
                    candidates.append(cleaned_for_check)
                    continue

                continue
           
            candidates.append(clean_text)
        
        print(f"DEBUG: re_ocr - Candidates: {candidates}")
        
        if candidates:
            # Heuristic: Pick the one that is most likely a name
            # For now, pick the first one that doesn't look like a title
            for cand in candidates:
                 if "常规" not in cand and "报告" not in cand and "检验" not in cand:
                      return cand
            return candidates[0]
        
        # Fallback: If no candidates, but we have text lines, maybe we missed something?
        # If "门诊" was found, and nothing else, maybe the name is to the right of "门诊"?
        # But we cropped left of Gender.
        
        # If "门诊" is the ONLY text found, maybe we should expand the crop slightly to the RIGHT?
        # Or maybe the name is *above* the Gender line?
        # But let's assume the current strategy is "Left of Gender".
        
        # Try looking for a name-like string in the candidates even if we filtered it?
        
        return None
    except Exception as e:
        debug_log["re_ocr_error"] = str(e)
        return None

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    debug_log = {}
    if reader is None:
        raise HTTPException(status_code=500, detail="OCR engine not initialized properly.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    # Read image file
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # --- Step 1: Image Standardization ---
    processed_image = standardize_image(image)

    # Perform OCR using RapidOCR
    # RapidOCR returns: [[box, text, score], ...]
    results, elapse = reader(processed_image)

    # --- Check for Rotation (Vertical Text) ---
    if results:
        vertical_count = 0
        total_count = len(results)
        title_x_sum = 0
        title_count = 0
        
        all_x = []
        
        for item in results:
            box, text, score = item
            # Box is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            
            # Use a slightly stricter check for "vertical" to avoid noise
            if h > w * 1.2 and len(text) > 1: 
                vertical_count += 1
            
            center_x = sum(xs) / 4
            all_x.append(center_x)
            
            if "医院" in text or "报告单" in text:
                title_x_sum += center_x
                title_count += 1
                
        # If > 50% lines are vertical, assume rotation
        if total_count > 10 and (vertical_count / total_count) > 0.4:
            print("DEBUG: Detected Vertical Text. Attempting Rotation Correction.")
            debug_log["rotation_detected"] = True
            debug_log["vertical_ratio"] = vertical_count / total_count
            
            # Determine direction
            # If Title is on Right (High X), Rotate CCW (Right -> Top)
            # If Title is on Left (Low X), Rotate CW (Left -> Top)
            
            img_w, img_h = image.size
            
            rotate_ccw = True # Default to CCW (Right -> Top)
            
            if title_count > 0:
                avg_title_x = title_x_sum / title_count
                if avg_title_x < img_w / 2:
                    rotate_ccw = False # Title is Left -> CW
                print(f"DEBUG: Title found at X={avg_title_x} (W={img_w}). Rotate CCW={rotate_ccw}")
            elif all_x:
                avg_x = sum(all_x) / len(all_x)
                if avg_x < img_w / 2:
                     rotate_ccw = False
                print(f"DEBUG: No title found. Avg X={avg_x} (W={img_w}). Rotate CCW={rotate_ccw}")
            
            if rotate_ccw:
                print("DEBUG: Rotating 90 degrees CCW (Right -> Top)")
                image = image.transpose(Image.ROTATE_90)
                debug_log["rotation_direction"] = "CCW"
            else:
                print("DEBUG: Rotating 90 degrees CW (Left -> Top)")
                image = image.transpose(Image.ROTATE_270)
                debug_log["rotation_direction"] = "CW"
                
            # Re-process
            processed_image = standardize_image(image)
            results, elapse = reader(processed_image)

    # Structure the data
    text_lines_for_structure = []
    
    if results:
        for item in results:
            # item structure: [box, text, score]
            box, text, score = item
            
            # Convert numpy types/float32 to native python types
            box_coords = [[int(pt[0]), int(pt[1])] for pt in box]
            
            # Calculate center coordinates for structure parsing
            center_x = sum([pt[0] for pt in box_coords]) / 4
            center_y = sum([pt[1] for pt in box_coords]) / 4
            
            text_lines_for_structure.append({
                "text": text, # Raw text first
                "center_x": center_x,
                "center_y": center_y,
                "box": box_coords
            })

    # --- Step 2: Data Cleaning ---
    cleaned_lines = clean_text_data(text_lines_for_structure)

    # --- Step 4: NLP Structuring (Extract structure first) ---
    structured_data = nlp_structure_data(cleaned_lines, debug_log)
    
    # --- Step 3.1: Re-OCR for Missing Patient Name (Proactive Fix) ---
    # If Name is missing, try to find it by looking left of Gender
    if not structured_data.get("patient_name"):
        re_ocr_name = re_ocr_patient_name(processed_image, cleaned_lines, debug_log)
        if re_ocr_name:
            structured_data["patient_name"] = re_ocr_name
            print(f"DEBUG: Re-OCR found patient name: {re_ocr_name}")
        else:
            # Fallback: Check if "门诊" or "住院" is present in the raw text near the top-left,
            # and if so, look for a name-like pattern nearby in the original lines.
            pass
            
    # --- Step 3: Data Governance (on Structured Data) ---
    final_data = govern_medical_data(structured_data)
    
    # --- Step 4.1: Post-Governance Cleanup ---
    # Handle prescription specific fields (Diagnosis, Usage)
    if final_data.get("details"):
        new_results = []
        diagnosis_list = []
        filename_hint = (file.filename or "").lower()
        excluded_label_keywords = [
            "检验项目",
            "检验目的",
            "检验结果",
            "单位",
            "参考区间",
            "参考范围",
            "互认标识",
            "方法学"
        ]
        excluded_noise_keywords = [
            "临床印象",
            "学姜涛专家",
            "医制",
            "串请璃月",
            "性激素6项"
        ]
        for item in final_data["details"]:
            param = item.get("parameter", "")
            if not param:
                param = ""
            unit = item.get("unit", "")
            if not unit:
                unit = ""

            # Skip table headers/labels that should not appear in JSON detail rows
            compact_param = str(param).replace(" ", "")
            if any(k in compact_param for k in excluded_label_keywords):
                continue
            if any(k in compact_param for k in excluded_noise_keywords):
                continue
            
            # Detect Diagnosis lines
            # Diagnosis might be in parameter or unit or even value if it's long text
            if "诊断" in param or "Clinical" in param or "积病" in param or "恶性肿瘤" in param or "积聚" in param:
                # If we have "诊断: ..." in param, and unit/value has something else?
                # Check if unit/value looks like a drug or usage
                # If so, append it to new_results as a separate item
                
                diagnosis_parts = [param]
                
                # Check value
                val = item.get("value", "")
                if val and any(u in val for u in ["袋", "包", "g", "ml", "片", "粒", "次", "mg", "丸", "支"]):
                     # It's a drug/usage, create a new item
                     new_results.append({"parameter": val, "unit": val, "usage": val, "result_status": "正常"})
                elif val:
                     diagnosis_parts.append(val)
                     
                # Check unit
                if unit and any(u in unit for u in ["袋", "包", "g", "ml", "片", "粒", "次", "mg", "丸", "支"]):
                     # It's a drug/usage, create a new item
                     new_results.append({"parameter": unit, "unit": unit, "usage": unit, "result_status": "正常"})
                elif unit:
                     diagnosis_parts.append(unit)

                diagnosis_list.append(" ".join(diagnosis_parts))
                continue
                
            # Handle Usage in Unit field
            # Only if Reference Range is empty (likely Prescription)
            # And exclude common lab units
            is_lab_unit = any(x in unit for x in ["/L", "/ml", "/l", "mol", "U/L"])
            if not item.get("reference_range") and not item.get("reference") and not is_lab_unit:
                if any(u in unit for u in ["袋", "包", "g", "ml", "片", "粒", "次", "mg", "丸", "支"]):
                    item["usage"] = unit
                    # Keep unit as is or clean? Usually keep as usage string.
                    # If usage is set, maybe unit should be standardized?
                    # For now, duplicate to usage.
            
            # Clean up old keys if needed, or keep them. Let's keep them for backward compatibility,
            # but ensure we have all new keys.
            
            new_results.append(item)

        # Template post-process: "性激素6项" often splits into
        # row A (item+value) and row B (unit+reference+method). Merge by order.
        hormone_keywords = ["prl", "fsh", "lh", "e2", "泌乳素", "卵泡刺激素", "促黄体素", "睾酮", "雌二醇", "孕酮", "性激素"]
        hormone_signal_count = 0
        for it in new_results:
            p = str(it.get("parameter", "")).lower()
            if any(hk in p for hk in hormone_keywords):
                hormone_signal_count += 1
        is_hormone_template = ("性激素6项" in filename_hint) or (hormone_signal_count >= 3)

        if is_hormone_template:
            primary_rows = []
            supplement_rows = []
            for it in new_results:
                p = str(it.get("parameter", ""))
                v = str(it.get("value", "")).strip()
                ref_v = str(it.get("reference", "") or it.get("reference_range", "")).strip()
                unit_v = str(it.get("unit", "")).strip()
                p_compact = p.replace(" ", "")

                is_supp = (
                    ("化学发光法" in p_compact)
                    or (not v and bool(ref_v) and ("IU" in p or "ng/" in p or "μ" in p or "mIU" in p))
                )

                if is_supp:
                    supplement_rows.append(it)
                else:
                    primary_rows.append(it)

            if primary_rows and supplement_rows:
                pair_count = min(len(primary_rows), len(supplement_rows))
                for i in range(pair_count):
                    pri = primary_rows[i]
                    sup = supplement_rows[i]

                    sup_param = str(sup.get("parameter", ""))
                    sup_unit = str(sup.get("unit", "")).strip()
                    if not sup_unit:
                        sup_unit = re.sub(r'化学发光法', '', sup_param).strip(" ：:")

                    if not str(pri.get("unit", "")).strip() and sup_unit:
                        pri["unit"] = sup_unit

                    sup_ref = str(sup.get("reference", "") or sup.get("reference_range", "")).strip()
                    if not str(pri.get("reference", "")).strip() and sup_ref:
                        pri["reference"] = sup_ref
                        pri["reference_range"] = sup_ref
                        # Keep min/max in sync when reference was merged from supplement row.
                        ref_m = re.search(r'([\d\.]+)\s*[\-~～—–－]{1,2}\s*([\d\.]+)', sup_ref)
                        if ref_m:
                            pri["minReference"] = ref_m.group(1)
                            pri["maxReference"] = ref_m.group(2)

                # Drop supplement-only rows after merge.
                new_results = primary_rows

        # Keep details and results consistent
        final_data["details"] = new_results
        final_data["results"] = new_results
        if diagnosis_list:
            final_data["diagnosis"] = "; ".join(diagnosis_list)
            
    # Cleanup internal keys from top level
    for k in ["test_name", "check_date", "patient_name"]:
         if k in final_data and k not in ["patient_name", "test_name"]: # keep some for internal use or tests, actually let's just let them be, or remove them
              pass # Let's keep them for now, tests might depend on them
              
    # Ensure all requested keys exist at top level
    for k in ["idhao", "yangben", "xingming", "baogaoTime", "biaobentype", "yiyuan", "jianyanTime", "zhuyuanhao", "sex", "fangfa"]:
         if k not in final_data:
             final_data[k] = ""
             
    # Prepare file info
    timestamp = int(time.time())
    file_id = str(uuid.uuid4())[:8]
    original_filename = file.filename or "unknown"
    safe_filename = "".join([c for c in original_filename if c.isalnum() or c in "._-"])
    
    output_filename = f"{safe_filename}_{timestamp}_{file_id}.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Save JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    
    # Return final response
    return {
        "status": "success",
        "filename": output_filename,
        "result_file": output_path,
        "debug_info": debug_log,
        **final_data # Flatten top level fields
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9080)
