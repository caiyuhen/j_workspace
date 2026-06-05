import os
import re
from typing import List, Dict, Any
import glob
from tqdm import tqdm
import config

class DataProcessor:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        
    def iter_documents(self):
        """
        Generator to yield documents one by one to save memory.
        """
        print("Scanning files...")
        file_list = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith('.md'):
                    file_list.append(os.path.join(root, file))
        
        print(f"Found {len(file_list)} files. Starting stream processing...")
        
        for file_path in tqdm(file_list, desc="Processing Files"):
            doc = self._read_markdown(file_path)
            if doc:
                yield doc

    def _read_markdown(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "content": content,
                "type": "markdown"
            }
        except Exception as e:
            # print(f"Error reading {file_path}: {e}") # Reduce noise
            return None

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove null bytes which can cause issues in C extensions
        text = text.replace('\x00', '')
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()

class TextChunker:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc['content']
        chunks = []
        if not text:
            return chunks
            
        # Simple sliding window
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            if len(chunk_text) < 10: # Skip very small chunks
                continue
            chunks.append({
                "text": chunk_text,
                "source": doc['filename'],
                "file_path": doc['file_path'],
                "doc_type": doc['type']
            })
        return chunks

class KnowledgeExtractor:
    def __init__(self):
        pass
        
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        metadata = {
            "stages": [],
            "syndromes": [],
            "principles": [],
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
        }
        
        # Helper to extract based on list
        def extract_tags(source_list, target_key):
            for item in source_list:
                if item in text:
                    metadata[target_key].append(item)

        # Original
        extract_tags(config.STAGES, "stages")
        extract_tags(config.SYNDROMES, "syndromes")
        extract_tags(config.TREATMENT_PRINCIPLES, "principles")
        
        # New Entities
        extract_tags(config.WESTERN_MEDICINES, "western_medicines")
        extract_tags(config.TCM_MEDICINES, "tcm_medicines")
        extract_tags(config.DIAGNOSES, "diagnoses")
        extract_tags(config.PATHOLOGY_TYPES, "pathology_types")
        extract_tags(config.DIAGNOSTIC_FEATURES, "diagnostic_features")
        extract_tags(config.GENE_MUTATIONS, "gene_mutations")
        extract_tags(config.CYTOLOGY_CHECKS, "cytology_checks")
        extract_tags(config.SURGERIES, "surgeries")
        extract_tags(config.RADIOTHERAPIES, "radiotherapies")
        extract_tags(config.INITIAL_TREATMENTS, "initial_treatments")
        extract_tags(config.ADJUVANT_TREATMENTS, "adjuvant_treatments")

        return metadata

def process_data_stream(batch_size=100):
    """
    Yields batches of processed chunks.
    """
    processor = DataProcessor(config.DATA_DIR)
    chunker = TextChunker()
    extractor = KnowledgeExtractor()
    
    current_batch = []
    
    for doc in processor.iter_documents():
        # Clean text
        doc['content'] = processor.clean_text(doc['content'])
        
        # Create chunks
        chunks = chunker.chunk_document(doc)
        
        # Extract metadata
        for chunk in chunks:
            metadata = extractor.extract_metadata(chunk['text'])
            chunk.update(metadata)
            current_batch.append(chunk)
            
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
    
    # Yield remaining
    if current_batch:
        yield current_batch


if __name__ == "__main__":
    process_data_pipeline()
