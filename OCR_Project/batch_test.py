import os
import requests
import json
import glob
import time

URL = "http://localhost:9080/ocr"
INPUT_DIR = r"d:\workspace\OCR_Project\input"
OUTPUT_DIR = r"d:\workspace\OCR_Project\output"

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_directory(directory):
    # Get all image files in the directory and its subdirectories
    image_files = glob.glob(os.path.join(directory, "**", "*.jpg"), recursive=True)
    image_files.extend(glob.glob(os.path.join(directory, "**", "*.png"), recursive=True))
    
    print(f"Found {len(image_files)} images to process in {directory}")
    
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(image_files):
        print(f"\n[{i+1}/{len(image_files)}] Processing: {file_path}")
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
                response = requests.post(URL, files=files)
                
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(f"  Success! Result saved to: {result.get('result_file')}")
                    success_count += 1
                else:
                    print(f"  API Error: {result}")
                    fail_count += 1
            else:
                print(f"  HTTP Error: {response.status_code}")
                print(response.text)
                fail_count += 1
        except Exception as e:
            print(f"  Exception occurred: {e}")
            fail_count += 1
            
        # Small delay to not overwhelm the server
        time.sleep(1)
            
    print(f"\n=== Batch Processing Complete ===")
    print(f"Total processed: {len(image_files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Results are saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get("http://localhost:9080/", timeout=2)
        print("OCR Server is running. Starting batch process...")
        process_directory(INPUT_DIR)
    except requests.ConnectionError:
        print("Error: Could not connect to OCR Server at http://localhost:9080/")
        print("Please ensure the server is running (python main.py)")
