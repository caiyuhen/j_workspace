
import os
import re
import json
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pubmed_interface.pubmed_client import PubMedClient

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/retrieval.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mapping for Chinese prompts to English MeSH terms
PROMPT_MAPPING = {
    "肺癌的最新治疗方案": "Lung Neoplasms[MeSH Terms] AND therapy[Subheading]",
    "非小细胞肺癌的靶向药物": "Carcinoma, Non-Small-Cell Lung[MeSH Terms] AND Molecular Targeted Therapy[MeSH Terms]",
    "免疫治疗的副作用": "Immunotherapy/adverse effects[MeSH Terms]",
    "肺癌早期筛查指南": "Lung Neoplasms/diagnosis[MeSH Terms] AND Mass Screening[MeSH Terms] AND Practice Guidelines as Topic[MeSH Terms]",
    "PD-1抑制剂在肺癌中的应用": "Lung Neoplasms[MeSH Terms] AND Programmed Cell Death 1 Receptor/antagonists and inhibitors[MeSH Terms]"
}

def sanitize_filename(name: str) -> str:
    # Keep only alphanumeric, spaces, hyphens, underscores
    s = re.sub(r'[^\w\s-]', '', name)
    return s.strip().replace(' ', '_')[:50] # Limit length

def process_prompt(client: PubMedClient, prompt_entry: dict, output_dir: str, max_results: int, since: str):
    prompt = prompt_entry.get("prompt")
    if not prompt:
        return
    
    # Construct query with date filter if provided
    # Translate query if in mapping
    query_text = PROMPT_MAPPING.get(prompt, prompt)
    
    if since:
        # PubMed date format: YYYY/MM/DD
        # We append to query: AND ("YYYY/MM/DD"[Date - Publication] : "3000"[Date - Publication])
        date_query = f' AND ("{since}"[Date - Publication] : "3000"[Date - Publication])'
        query = query_text + date_query
    else:
        query = query_text
    
    try:
        logging.info(f"Searching for: {prompt}")
        results = client.search(query, max_results=max_results)
        
        if not results:
            logging.info(f"No results for: {prompt}")
            return

        # Fetch details (abstracts, etc.)
        # The search results might already contain some info, but we need full details
        # The client.search returns basic info. We might need to fetch details if not complete.
        # Assuming client.search returns full dicts as per implementation.
        # But wait, search() in PubMedClient calls PubMedLoader.load() which returns Documents.
        # We need to convert to dicts.
        # Actually, let's look at PubMedClient.search implementation.
        # It returns List[Dict].
        
        # Deduplicate by PMID
        unique_results = []
        seen_pmids = set()
        for r in results:
            pmid = r.get('PMID')
            if pmid and pmid not in seen_pmids:
                seen_pmids.add(pmid)
                unique_results.append(r)
        
        filename = sanitize_filename(prompt) + ".jsonl"
        output_path = os.path.join(output_dir, filename)
        
        client.save_to_jsonl(unique_results, output_path)
        logging.info(f"Saved {len(unique_results)} results to {output_path}")
        
    except Exception as e:
        error_msg = f"Error processing prompt '{prompt}': {e}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)

def main():
    parser = argparse.ArgumentParser(description="PubMed Retrieval CLI")
    parser.add_argument("--prompt-file", required=True, help="Path to prompts.jsonl")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--max", type=int, default=100, help="Max results per prompt")
    parser.add_argument("--since", help="Start date (YYYY/MM/DD)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.prompt_file):
        print(f"Error: Prompt file {args.prompt_file} not found.")
        return

    os.makedirs(args.output, exist_ok=True)
    
    # Read prompts
    prompts = []
    with open(args.prompt_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
    
    client = PubMedClient()
    
    # Parallel execution
    max_workers = 3
    print(f"Processing {len(prompts)} prompts with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_prompt, client, p, args.output, args.max, args.since)
            for p in prompts
        ]
        
        for _ in tqdm(as_completed(futures), total=len(prompts)):
            pass

    # Sequential for stability
    # print(f"Processing {len(prompts)} prompts sequentially...")
    # for p in prompts:
    #     process_prompt(client, p, args.output, args.max, args.since)
            
    print("Done.")

if __name__ == "__main__":
    main()
