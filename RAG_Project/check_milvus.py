import os
import sys
import logging
from pymilvus import connections, Collection, utility

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_milvus():
    print("Connecting to Milvus...")
    connections.connect("default", host="127.0.0.1", port=19530)
    
    collection_name = "medical_rag"
    
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' exists.")
        col = Collection(collection_name)
        col.load()
        
        num_entities = col.num_entities
        print(f"Total entities in collection: {num_entities}")
        
        print("\nSchema details:")
        for field in col.schema.fields:
            print(f" - Field: {field.name}, Type: {field.dtype}, Max Length/Dim: {getattr(field, 'max_length', getattr(field, 'dim', 'N/A'))}")
            
        print("\nQuerying 2 sample records from Milvus...")
        # Search using a dummy vector just to fetch some records if direct query is restricted,
        # or use query with an expression
        results = col.query(expr="id > 0", output_fields=["id", "text", "source", "stages"], limit=2)
        
        for res in results:
            print(f"\n--- Record ID: {res['id']} ---")
            print(f"Source: {res['source']}")
            print(f"Stages: {res['stages']}")
            print(f"Text Chunk: {res['text'][:200]}...") # Truncate for display
            
    else:
        print(f"Collection '{collection_name}' does not exist.")

if __name__ == "__main__":
    check_milvus()
