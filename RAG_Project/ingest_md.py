import os
import sys
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vector_store import MilvusStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_md_files(source_dir):
    source_path = Path(source_dir)
    
    vector_store = MilvusStore()
    if not vector_store.connected:
        vector_store.connect()
    vector_store.init_collection()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
<<<<<<< HEAD
    # Recursively find all markdown files
    for file_path in source_path.rglob("*.md"):
=======
    for file_path in source_path.glob("*.md"):
        if '乳腺' not in file_path.name:
            continue
            
>>>>>>> origin/main
        logging.info(f"Processing: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        chunks = text_splitter.split_text(content)
        
        chunks_to_insert = []
        for chunk in chunks:
            chunks_to_insert.append({
                "text": chunk,
                "source": file_path.name,
                "stages": [],
                "syndromes": [],
                "western_medicines": [],
                "tcm_medicines": [],
                "diagnoses": [],
                "pathology_types": [],
                "diagnostic_features": [],
                "gene_mutations": [],
                "cytology_checks": [],
                "surgeries": [],
                "radiotherapies": [],
                "initial_treatments": [],
                "adjuvant_treatments": []
            })
            
        if chunks_to_insert:
            logging.info(f"Inserting {len(chunks_to_insert)} chunks from {file_path.name}...")
            vector_store.insert_chunks(chunks_to_insert)

if __name__ == "__main__":
<<<<<<< HEAD
    # Point to the root data directory to capture all subdirectories
    ingest_md_files("/app/data")
=======
    ingest_md_files("/mnt/disk3/home/pg/RAG_Project/data/ragv6")
>>>>>>> origin/main
