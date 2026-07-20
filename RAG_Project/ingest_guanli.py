import os
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
<<<<<<< HEAD
import config # Ensure HF_ENDPOINT is set
=======
>>>>>>> origin/main
from vector_store import MilvusStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_file(file_path):
    vector_store = MilvusStore()
    if not vector_store.connected:
        vector_store.connect()
    vector_store.init_collection()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    path = Path(file_path)
    if not path.exists():
        logging.error(f"File {file_path} does not exist.")
        return
        
    logging.info(f"Processing: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    chunks = text_splitter.split_text(content)
    
    chunks_to_insert = []
    for chunk in chunks:
        chunks_to_insert.append({
            "text": chunk,
            "source": path.name,
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
        logging.info(f"Inserting {len(chunks_to_insert)} chunks from {path.name}...")
        vector_store.insert_chunks(chunks_to_insert)

if __name__ == "__main__":
<<<<<<< HEAD
    ingest_file("/home/user/RAG_Project/data/guanli/乳腺癌疾病管理路径.md")
=======
    ingest_file("/mnt/disk3/home/pg/RAG_Project/data/guanli/乳腺癌疾病管理路径.md")
>>>>>>> origin/main
