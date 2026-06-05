
import os
import re
import json
import sys
from collections import Counter

# Use sys.stdout.flush() to ensure output is visible
def log(msg):
    print(msg)
    sys.stdout.flush()

try:
    import pandas as pd
except ImportError:
    log("Pandas not found. Please install pandas.")
    sys.exit(1)

SOURCE_DIR = "/mnt/disk3/home/pg/large _model"
OUTPUT_JSONL = "/mnt/disk3/home/pg/RAG_Project/prompts.jsonl"
OUTPUT_STATS = "/mnt/disk3/home/pg/RAG_Project/prompt_stats.csv"

def extract_prompts():
    log(f"Scanning {SOURCE_DIR}...")
    if not os.path.exists(SOURCE_DIR):
        log(f"Directory {SOURCE_DIR} does not exist!")
        return

    prompts_data = []
    
    # Regex pattern
    pattern = re.compile(r'提示词[:：]\s*(.+)')
    
    file_count = 0
    match_count = 0

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(('.txt', '.md', '.json')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # log(f"Content of {file_path}: {content[:50]}...") # Debug
                        matches = pattern.findall(content)
                        if matches:
                            rel_path = os.path.relpath(file_path, SOURCE_DIR)
                            for match in matches:
                                prompt = match.strip()
                                if prompt:
                                    prompts_data.append({
                                        "file": rel_path,
                                        "prompt": prompt
                                    })
                                    match_count += 1
                        else:
                             # Try to debug why it didn't match if it looks like it should
                             if "提示词" in content:
                                 log(f"Found '提示词' in {file_path} but regex failed.")
                except Exception as e:
                    log(f"Error reading {file_path}: {e}")
                file_count += 1

    log(f"Scanned {file_count} files. Found {match_count} prompts.")

    if not prompts_data:
        log("No prompts found.")
        return

    # Save raw JSONL
    try:
        with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
            for entry in prompts_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        log(f"Saved raw prompts to {OUTPUT_JSONL}")
    except Exception as e:
        log(f"Error saving JSONL: {e}")

    # Deduplicate and stats
    all_prompts = [p['prompt'] for p in prompts_data]
    
    # Count frequencies
    counter = Counter(all_prompts)
    
    # Convert to DataFrame
    df = pd.DataFrame(counter.items(), columns=['prompt', 'count'])
    df = df.sort_values(by='count', ascending=False)
    
    # Save stats
    try:
        df.to_csv(OUTPUT_STATS, index=False, encoding='utf-8')
        log(f"Saved stats to {OUTPUT_STATS}")
    except Exception as e:
        log(f"Error saving stats: {e}")

if __name__ == "__main__":
    extract_prompts()
