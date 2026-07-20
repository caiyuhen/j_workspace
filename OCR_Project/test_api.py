<<<<<<< HEAD
import requests
import json
import os

url = "http://localhost:9080/ocr"
blood_routine_file = "test_blood_routine.png"
prescription_file = "test_prescription.png"

# Real-world test images
real_world_images = [
    r"d:\workspace\OCR_Project\input\河南省肿瘤医院\血常规.jpg",
    r"d:\workspace\OCR_Project\input\北中医三元\7736c010e0a41742b83431d4a98adefe.jpg",
    r"d:\workspace\OCR_Project\input\北中医三元\处方3.jpg.png",
    r"d:\workspace\OCR_Project\input\北中医三元\95527c0d20ae2ba93dc4bbb6336b4dbc.jpg",
    r"d:\workspace\OCR_Project\input\大连\血常规(1).jpg",
    r"d:\workspace\OCR_Project\input\广安门\血常规.jpg",
    r"d:\workspace\OCR_Project\input\广安门\生化全项.jpg",
    r"d:\workspace\OCR_Project\input\广安门\药方图片(1).jpg"
]

def test_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    try:
        print(f"\nSending {os.path.basename(file_path)} to {url}...")
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "image/png")} # Keeping mime type simple
            response = requests.post(url, files=files)

        if response.status_code == 200:
            print("Success!")
            result = response.json()
            
            # Pretty print specific parts of the response
            print(f"Status: {result.get('status')}")
            
            # Print Debug Info
            debug_info = result.get("debug_info", {})
            print(f"Debug: header_y={debug_info.get('header_y')}, footer_y={debug_info.get('footer_y')}")
            print(f"Debug: table_items={debug_info.get('table_item_count')}, left={debug_info.get('left_item_count')}, right={debug_info.get('right_item_count')}")
            print(f"Filename: {result.get('filename')}")
            print(f"Result File: {result.get('result_file')}")
            
            # Direct access to flattened fields
            print("\n--- Structured Result Summary ---")
            print(f"Patient Name: {result.get('xingming')}")
            print(f"Check Date: {result.get('jianyanTime')}")
            if result.get('diagnosis'):
                print(f"Diagnosis: {result.get('diagnosis')}")
            if "results" in result:
                print(f"Item Count: {len(result['results'])}")
                print("First 3 items:")
                for i, item in enumerate(result["results"]):
                    item_info = {
                        "project_zh": item.get("project_zh"),
                        "daihaos": item.get("daihaos"),
                        "result": item.get("result"),
                        "unit": item.get("unit"),
                        "reference": item.get("reference"),
                        "minReference": item.get("minReference"),
                        "maxReference": item.get("maxReference"),
                        "tishi": item.get("tishi")
                    }
                    if item.get("usage"):
                        item_info["usage"] = item.get("usage")
                    print(json.dumps(item_info, ensure_ascii=False, indent=4))
                    if i >= 2: break
            else:
                print("No results found.")
            
        else:
            print(f"Failed with status code: {response.status_code}")
            # print(f"Response: {response.text}") # Reduce noise if failing

    except Exception as e:
        print(f"An error occurred: {e}")

# Run tests
# test_file(blood_routine_file)
# test_file(prescription_file)

print("\n=== Testing Real World Images ===")
for img_path in real_world_images:
    test_file(img_path)
=======
import requests
import json
import os

url = "http://localhost:9080/ocr"
blood_routine_file = "test_blood_routine.png"
prescription_file = "test_prescription.png"

# Real-world test images
real_world_images = [
    r"d:\workspace\OCR_Project\input\河南省肿瘤医院\血常规.jpg",
    r"d:\workspace\OCR_Project\input\北中医三元\7736c010e0a41742b83431d4a98adefe.jpg",
    r"d:\workspace\OCR_Project\input\北中医三元\处方3.jpg.png",
    r"d:\workspace\OCR_Project\input\北中医三元\95527c0d20ae2ba93dc4bbb6336b4dbc.jpg",
    r"d:\workspace\OCR_Project\input\大连\血常规(1).jpg",
    r"d:\workspace\OCR_Project\input\广安门\血常规.jpg",
    r"d:\workspace\OCR_Project\input\广安门\生化全项.jpg",
    r"d:\workspace\OCR_Project\input\广安门\药方图片(1).jpg"
]

def test_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    try:
        print(f"\nSending {os.path.basename(file_path)} to {url}...")
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "image/png")} # Keeping mime type simple
            response = requests.post(url, files=files)

        if response.status_code == 200:
            print("Success!")
            result = response.json()
            
            # Pretty print specific parts of the response
            print(f"Status: {result.get('status')}")
            
            # Print Debug Info
            debug_info = result.get("debug_info", {})
            print(f"Debug: header_y={debug_info.get('header_y')}, footer_y={debug_info.get('footer_y')}")
            print(f"Debug: table_items={debug_info.get('table_item_count')}, left={debug_info.get('left_item_count')}, right={debug_info.get('right_item_count')}")
            print(f"Filename: {result.get('filename')}")
            print(f"Result File: {result.get('result_file')}")
            
            # Direct access to flattened fields
            print("\n--- Structured Result Summary ---")
            print(f"Patient Name: {result.get('xingming')}")
            print(f"Check Date: {result.get('jianyanTime')}")
            if result.get('diagnosis'):
                print(f"Diagnosis: {result.get('diagnosis')}")
            if "results" in result:
                print(f"Item Count: {len(result['results'])}")
                print("First 3 items:")
                for i, item in enumerate(result["results"]):
                    item_info = {
                        "project_zh": item.get("project_zh"),
                        "daihaos": item.get("daihaos"),
                        "result": item.get("result"),
                        "unit": item.get("unit"),
                        "reference": item.get("reference"),
                        "minReference": item.get("minReference"),
                        "maxReference": item.get("maxReference"),
                        "tishi": item.get("tishi")
                    }
                    if item.get("usage"):
                        item_info["usage"] = item.get("usage")
                    print(json.dumps(item_info, ensure_ascii=False, indent=4))
                    if i >= 2: break
            else:
                print("No results found.")
            
        else:
            print(f"Failed with status code: {response.status_code}")
            # print(f"Response: {response.text}") # Reduce noise if failing

    except Exception as e:
        print(f"An error occurred: {e}")

# Run tests
# test_file(blood_routine_file)
# test_file(prescription_file)

print("\n=== Testing Real World Images ===")
for img_path in real_world_images:
    test_file(img_path)
>>>>>>> origin/main
