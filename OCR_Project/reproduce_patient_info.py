
import re

def extract_key_value_pairs(text_lines):
    extracted_data = {}
    
    # Sort lines by Y then X to ensure consistent order
    text_lines.sort(key=lambda x: (x['center_y'], x['center_x']))
    
    # Define regex patterns for common fields
    patterns = {
        "姓名": r"(?:姓名|Name|姓\s*名|名|医先|:姓名)[:：]?\s*([\u4e00-\u9fa5]{2,4})",
        "性别": r"(?:性\s*别|s别|Sex|别|:别)[:：]?\s*([男女])",
        "年龄": r"(?:年\s*龄|Age|龄|:龄)[:：]?\s*(\d+.*?)",
        "科室": r"(?:科\s*室|Dept|室|:科室)[:：]?\s*([\u4e00-\u9fa5]+)",
        "床号": r"(?:床\s*号|Bed|:床号)[:：]?\s*([A-Za-z0-9]+)",
    }
    
    full_text = " ".join([line['text'] for line in text_lines])
    print(f"Full Text: {full_text}")
    
    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, full_text)
            if match:
                value = match.group(1).strip()
                extracted_data[key] = value
        except Exception as e:
            print(f"Error extracting {key}: {e}")

    # Fallback logic from main.py
    if "性别" not in extracted_data:
        m = re.search(r"别[:：]\s*([男女])", full_text)
        if m: extracted_data["性别"] = m.group(1)
             
    if "年龄" not in extracted_data:
        m = re.search(r"龄[:：]\s*(\d+[^\s]*)", full_text)
        if m: extracted_data["年龄"] = m.group(1).strip()

    # --- NEW LOGIC START ---
    if "姓名" not in extracted_data:
        print("Attempting to find Name via spatial logic...")
        # Find Gender block
        gender_block = None
        for line in text_lines:
            if "性别" in line['text'] or "别" in line['text']: # Simple check
                 # Verify it's the gender block
                 if re.search(r"[男女]", line['text']):
                     gender_block = line
                     break
        
        if gender_block:
            print(f"Found Gender block: {gender_block['text']}")
            # Look left
            candidates = []
            for line in text_lines:
                if line == gender_block: continue
                
                # Same row (approx)
                if abs(line['center_y'] - gender_block['center_y']) < 20:
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
                    if text not in ["科室", "床号", "姓名", "性别", "年龄"]:
                        extracted_data["姓名"] = text
                        print(f"Found Name candidate: {text}")
                        break
    # --- NEW LOGIC END ---
        
    return extracted_data

# Simulation of 河南省肿瘤医院/血常规.jpg text lines
test_lines = [
    {'text': '河南省肿瘤医院', 'center_x': 500, 'center_y': 50},
    {'text': '血常规检验报告单', 'center_x': 500, 'center_y': 100},
    {'text': '张三', 'center_x': 200.0, 'center_y': 285.0}, # Name (no label)
    {'text': '别：男', 'center_x': 491.0, 'center_y': 285.0}, # Gender (partial label)
    {'text': '龄：68岁', 'center_x': 1130.5, 'center_y': 302.5}, # Age (partial label)
    {'text': '科室：内科', 'center_x': 200.0, 'center_y': 320.0}
]

print("--- Test 2: Spatial Name Extraction ---")
result = extract_key_value_pairs(test_lines)
print("Result:", result)

if "姓名" in result and result["姓名"] == "张三":
    print("SUCCESS: Name extracted via spatial logic")
else:
    print("FAILED: Name not extracted")
