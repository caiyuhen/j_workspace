
from rapidocr_onnxruntime import RapidOCR
import cv2
import numpy as np
from PIL import Image
import os
import re
from main import standardize_image, split_columns_smart

# Initialize
reader = RapidOCR()

# Test file
test_files = [
    # r"d:\workspace\OCR_Project\input\河南省肿瘤医院\血常规.jpg",
    r"d:\workspace\OCR_Project\output\debug_preprocessed.png"
]

def analyze_image(image_path):
    print(f"\nAnalyzing: {image_path}")
    if not os.path.exists(image_path):
        print("File not found.")
        return

    # 1. Standardize
    pil_img = Image.open(image_path)
    img = standardize_image(pil_img)
    
    # 2. OCR
    results, elapse = reader(img)
    if not results:
        print("No OCR results.")
        return

    # Convert to list of dicts
    text_lines = []
    for item in results:
        box, text, score = item
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        center_x = sum(xs) / 4
        center_y = sum(ys) / 4
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        
        text_lines.append({
            "text": text,
            "center_x": center_x,
            "center_y": center_y,
            "width": w,
            "height": h,
            "box": box
        })

    print(f"Total lines: {len(text_lines)}")

    # 3. Analyze Patient Info Area (Top 500px)
    print("\n--- Patient Info Area (Y < 500) ---")
    for line in text_lines:
        if line['center_y'] < 500:
            print(f"'{line['text']}' (X={line['center_x']:.1f}, Y={line['center_y']:.1f})")

    # 4. Analyze Table Area
    # Find Header
    header_y = 0
    for line in text_lines:
        if "检验项目" in line['text'] or "参考范围" in line['text']:
            header_y = max(header_y, line['center_y'])
    
    if header_y == 0:
        header_y = 400 # Fallback
        
    print(f"\nHeader Y: {header_y}")
    
    # Filter table items
    table_items = [line for line in text_lines if line['center_y'] > header_y + 10]
    
    # Split Columns
    debug_log = {}
    left_items, right_items = split_columns_smart(table_items, debug_log)
    print(f"\nSplit X: {debug_log.get('split_x')}")
    print(f"Left Items: {len(left_items)}, Right Items: {len(right_items)}")
    
    # Analyze WBC/RBC Rows (Left Column)
    print("\n--- Left Column Rows (First 10) ---")
    rows = {}
    row_height_threshold = 30
    for item in left_items:
        found = False
        for y in rows:
            if abs(item['center_y'] - y) < row_height_threshold:
                rows[y].append(item)
                found = True
                break
        if not found:
            rows[item['center_y']] = [item]
            
    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    
    for y, items in sorted_rows[:10]:
        items.sort(key=lambda x: x['center_x'])
        row_text = " | ".join([i['text'] for i in items])
        print(f"Y={y:.1f}: {row_text}")

    # Analyze Right Column Rows
    print("\n--- Right Column Rows (First 10) ---")
    rows_r = {}
    for item in right_items:
        found = False
        for y in rows_r:
            if abs(item['center_y'] - y) < row_height_threshold:
                rows_r[y].append(item)
                found = True
                break
        if not found:
            rows_r[item['center_y']] = [item]
            
    sorted_rows_r = sorted(rows_r.items(), key=lambda x: x[0])
    
    for y, items in sorted_rows_r[:10]:
        items.sort(key=lambda x: x['center_x'])
        row_text = " | ".join([i['text'] for i in items])
        print(f"Y={y:.1f}: {row_text}")

if __name__ == "__main__":
    for f in test_files:
        analyze_image(f)
