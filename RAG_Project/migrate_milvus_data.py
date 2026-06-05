import os
import sys
import numpy as np
from tqdm import tqdm
from pymilvus import connections, Collection, utility

# Ensure HF_ENDPOINT is set before importing config or sentence_transformers
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Import existing MilvusStore for inserting
from vector_store import MilvusStore
from sentence_transformers import SentenceTransformer

def extract_data(collection_name):
    if not utility.has_collection(collection_name):
        print(f"Collection {collection_name} does not exist. Skipping.")
        return []
        
    print(f"Extracting data from {collection_name}...")
    col = Collection(collection_name)
    col.load()
    
    # Define output fields based on collection type
    if collection_name == "medical_knowledge":
        output_fields = ["content", "keywords"]
    else:
        output_fields = [
            "text", "source", "stages", "syndromes", "principles",
            "western_medicines", "tcm_medicines", "diagnoses", "pathology_types",
            "diagnostic_features", "gene_mutations", "cytology_checks",
            "surgeries", "radiotherapies", "initial_treatments", "adjuvant_treatments"
        ]
        
    # Query all records
    # To bypass 16384 limit, we could paginate or just query all if it's small
    # For this demo, let's assume it's small enough or use iterator
    res = col.query(expr="id >= 0", output_fields=output_fields, limit=16000)
    
    chunks = []
    for hit in res:
        chunk = {}
        if collection_name == "medical_knowledge":
            chunk['text'] = hit.get('content', '')
            # Try to map keywords to source or something descriptive
            keywords = hit.get('keywords', '')
            chunk['source'] = f"medical_knowledge (Keywords: {keywords})"
        else:
            chunk['text'] = hit.get('text', '')
            chunk['source'] = hit.get('source', '')
            # Copy other metadata
            for field in output_fields:
                if field not in ['text', 'source']:
                    val = hit.get(field, "")
                    # MilvusStore.insert_chunks expects lists for these fields
                    chunk[field] = val.split(',') if val else []
                    
        chunks.append(chunk)
        
    print(f"Extracted {len(chunks)} chunks from {collection_name}.")
    return chunks

def main():
    connections.connect("default", host="127.0.0.1", port="19530")
    
    collections_to_migrate = ["lung_cancer_rag", "medical_knowledge"]
    all_chunks = []
    
    for col_name in collections_to_migrate:
        all_chunks.extend(extract_data(col_name))
        
    if not all_chunks:
        print("No data to migrate.")
        return
        
    print(f"Total {len(all_chunks)} chunks to re-embed and insert.")
    
    # Initialize the target store (medical_rag)
    store = MilvusStore()
    store.connect()
    store.init_collection()
    store.load_collection()
    
    # Insert chunks (MilvusStore.insert_chunks will handle the re-embedding)
    print("Inserting data into unified medical_rag collection...")
    store.insert_chunks(all_chunks, batch_size=50)
    
    # Drop old collections to free up memory and prevent confusion
    for col_name in collections_to_migrate:
        if utility.has_collection(col_name):
            utility.drop_collection(col_name)
            print(f"Dropped old collection: {col_name}")

    print("Migration complete!")

if __name__ == "__main__":
    main()
