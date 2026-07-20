import config # Import config first to ensure HF_ENDPOINT is set
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
from sentence_transformers import SentenceTransformer
import numpy as np

class MilvusStore:
    def __init__(self, host=config.MILVUS_HOST, port=config.MILVUS_PORT):
        self.host = host
        self.port = port
        self.collection_name = config.COLLECTION_NAME
        self.embedding_model = None
        self.connected = False
        self.collection = None

    def connect(self):
        try:
            print(f"Connecting to Milvus at {self.host}:{self.port}...")
            connections.connect("default", host=self.host, port=self.port, timeout=5)
            
            # Check connection
            try:
                if utility.get_server_version():
                    self.connected = True
                    print("Connected to Milvus Server.")
                    return
            except Exception:
                pass # Fallthrough to Lite check if version check fails (though connect succeeded?)
                
        except Exception as e:
            print(f"Failed to connect to Milvus Server: {e}")
        
        print("Falling back to Milvus Lite (local file)...")
        try:
            import os
<<<<<<< HEAD
            db_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "milvus_medical.db")
=======
            db_name = "milvus_medical.db"
>>>>>>> origin/main
            if os.path.exists(db_name):
                    print(f"Found existing Lite DB: {db_name}")
            connections.connect("default", uri=db_name)
            self.connected = True
            print(f"Connected to Milvus Lite ({db_name}).")
            return
        except Exception as e_lite:
            print(f"Failed to connect to Milvus Lite: {e_lite}")
            self.connected = False

    def _ensure_index(self):
        try:
            print("Ensuring vector index...")
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params, index_name="vector_idx")
            print("Index created.")
        except Exception as e:
            print(f"Index creation skipped/failed (might already exist): {e}")

    def init_collection(self):
        if not self.connected:
            return

        if utility.has_collection(self.collection_name):
            print(f"Collection {self.collection_name} exists.")
            self.collection = Collection(self.collection_name)
        else:
            print(f"Creating collection {self.collection_name}...")
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=config.VECTOR_DIM),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
                # Metadata fields for Knowledge Graph/Structured Retrieval
                FieldSchema(name="stages", dtype=DataType.VARCHAR, max_length=512), # Stored as comma-separated string
                FieldSchema(name="syndromes", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="principles", dtype=DataType.VARCHAR, max_length=512),
                # New Expert Rule Entities
                FieldSchema(name="western_medicines", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="tcm_medicines", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="diagnoses", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="pathology_types", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="diagnostic_features", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="gene_mutations", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="cytology_checks", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="surgeries", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="radiotherapies", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="initial_treatments", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="adjuvant_treatments", dtype=DataType.VARCHAR, max_length=512)
            ]
            schema = CollectionSchema(fields, "Medical RAG Knowledge Base")
            self.collection = Collection(self.collection_name, schema)
            
        self._ensure_index()

    def load_collection(self):
        if not self.connected:
            return
        # We handle multi-collection logic in the search function now,
        # but let's load the main one by default.
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self._ensure_index()
            self.collection.load()
            print(f"Collection {self.collection_name} loaded.")
        else:
            print(f"Collection {self.collection_name} does not exist. Please init first.")
            
        # Also load lung_cancer_rag and medical_knowledge if they exist
        for extra_col in ["lung_cancer_rag", "medical_knowledge"]:
            if utility.has_collection(extra_col):
                col = Collection(extra_col)
                col.load()
                print(f"Extra collection {extra_col} loaded.")

    def load_model(self):
        print(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}...")
        try:
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        except Exception as e:
            # Choose fallback model based on configured dimension
            fallback_model = 'BAAI/bge-small-zh-v1.5' if config.VECTOR_DIM == 512 else 'all-MiniLM-L6-v2'
            print(f"Could not load specific model {config.EMBEDDING_MODEL_NAME}, falling back to '{fallback_model}' for demo.")
            try:
                self.embedding_model = SentenceTransformer(fallback_model)
            except Exception as e2:
                print(f"Could not load fallback model '{fallback_model}': {e2}")
                print("Failed to load any embedding model. Please check your model paths and environment.")
                raise RuntimeError("Failed to load embedding model.")

    def insert_chunks(self, chunks, batch_size=50):
        if not self.connected or not self.collection:
            print("Milvus connection lost. Reconnecting...")
            self.connect()
            self.init_collection()
            if not self.connected:
                print("Milvus not connected after retry.")
                return

        if self.embedding_model is None:
            self.load_model()
            
        # Ensure model is on the correct device
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Move model to device ONCE, not in loop
        if hasattr(self.embedding_model, 'to') and next(self.embedding_model.parameters()).device.type != device:
             print(f"Moving model to {device}...")
             self.embedding_model.to(device)

        total_chunks = len(chunks)
        print(f"Total chunks to process: {total_chunks}")
        
        from tqdm import tqdm
        import gc
        
        # Determine device
        print(f"Using device: {device} for embedding.")
        
        # If model not on correct device, move it
        # Moved outside loop
            
        for i in tqdm(range(0, total_chunks, batch_size), desc="Embedding & Inserting"):
            batch_chunks = chunks[i:i + batch_size]
            batch_texts = [chunk['text'] for chunk in batch_chunks]
            
            try:
                # Encode batch
                embeddings = self.embedding_model.encode(
                    batch_texts, 
                    normalize_embeddings=True,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    device=device
                )
                
                # Ensure float32
                if hasattr(embeddings, 'astype'):
                    embeddings = embeddings.astype(np.float32)
                
                # Prepare data for insertion
                data = [
                    embeddings,
                    batch_texts,
                    [chunk['source'] for chunk in batch_chunks],
                    [",".join(chunk.get('stages', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('syndromes', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('principles', [])) for chunk in batch_chunks],
                    # New Entities
                    [",".join(chunk.get('western_medicines', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('tcm_medicines', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('diagnoses', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('pathology_types', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('diagnostic_features', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('gene_mutations', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('cytology_checks', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('surgeries', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('radiotherapies', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('initial_treatments', [])) for chunk in batch_chunks],
                    [",".join(chunk.get('adjuvant_treatments', [])) for chunk in batch_chunks]
                ]
                
                # Insert batch
                self.collection.insert(data)
                
                # Explicit cleanup
                del embeddings
                del data
                gc.collect()
                
            except Exception as e:
                print(f"Error inserting batch {i}: {e}")
        
        # print("Flushing collection...")
        # self.collection.flush()
        print(f"Inserted {total_chunks} chunks.")

    def flush(self):
        if self.connected and self.collection:
            print("Flushing collection...")
            self.collection.flush()
            print("Collection flushed.")

    def search(self, query, top_k=5, filters=None):
        if not self.connected or not self.collection:
            return []
            
        if self.embedding_model is None:
            self.load_model()

        # Disable progress bar for search queries to reduce log noise
        query_embedding_512 = self.embedding_model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        if hasattr(query_embedding_512, 'astype'):
            query_embedding_512 = query_embedding_512.astype(np.float32)
        emb_list_512 = query_embedding_512.tolist()
        q_emb = [emb_list_512[0]] if isinstance(emb_list_512[0], list) else [emb_list_512]
        
        out_fields = [
            "text", "source", 
            "stages", "syndromes", "principles",
            "western_medicines", "tcm_medicines", "diagnoses", "pathology_types",
            "diagnostic_features", "gene_mutations", "cytology_checks",
            "surgeries", "radiotherapies", "initial_treatments", "adjuvant_treatments"
        ]
        
        try:
            results = self.collection.search(
                data=q_emb, 
                anns_field="embedding", 
                param=search_params, 
                limit=top_k * 2,
                expr=None,
                output_fields=out_fields
            )
            
            all_retrieved = []
            for hits in results:
                for hit in hits:
                    item = {
                        "id": hit.id,
                        "score": hit.distance,
                        "text": hit.entity.get("text"),
                        "source": hit.entity.get("source"),
                        "metadata": {
                            "stages": hit.entity.get("stages"),
                            "syndromes": hit.entity.get("syndromes"),
                            "principles": hit.entity.get("principles"),
                            "western_medicines": hit.entity.get("western_medicines"),
                            "tcm_medicines": hit.entity.get("tcm_medicines"),
                            "diagnoses": hit.entity.get("diagnoses"),
                            "pathology_types": hit.entity.get("pathology_types"),
                            "diagnostic_features": hit.entity.get("diagnostic_features"),
                            "gene_mutations": hit.entity.get("gene_mutations"),
                            "cytology_checks": hit.entity.get("cytology_checks"),
                            "surgeries": hit.entity.get("surgeries"),
                            "radiotherapies": hit.entity.get("radiotherapies"),
                            "initial_treatments": hit.entity.get("initial_treatments"),
                            "adjuvant_treatments": hit.entity.get("adjuvant_treatments")
                        }
                    }
                    all_retrieved.append(item)
                    
        except Exception as e:
            print(f"Error searching in {self.collection_name}: {e}")
            return []
            
        # Apply manual post-filtering
        filtered_retrieved = []
        for item in all_retrieved:
            if filters:
                match = True
                for key, value in filters.items():
                    if value and value not in (item["metadata"].get(key) or ""):
                        match = False
                        break
                if not match:
                    continue
            
            filtered_retrieved.append(item)
            if len(filtered_retrieved) >= top_k:
                break
                
        return filtered_retrieved

if __name__ == "__main__":
    # Test connection
    store = MilvusStore()
    store.connect()
