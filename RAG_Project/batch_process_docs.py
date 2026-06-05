import os
import sys
import shutil
import logging
from pathlib import Path

# Try to download NLTK data to the local directory silently if missing
import nltk
nltk.data.path.append('/home/lfang/nltk_data')
try:
    nltk.download('punkt_tab', download_dir='/home/lfang/nltk_data', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', download_dir='/home/lfang/nltk_data', quiet=True)
except Exception:
    pass

# Add the project directory to sys.path so 'vector_store' and 'config' can be found
sys.path.append("/mnt/disk3/home/pg/RAG_Project")

# Try to import necessary Langchain document loaders
try:
    from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from vector_store import MilvusStore
except ImportError as e:
    logging.error(f"Missing required libraries. Please ensure langchain, unstructured, and pymilvus are installed. Error: {e}")
    sys.exit(1)
    # Continue anyway so we can write the file, but execution might fail if dependencies are missing.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_documents(source_dir, dest_dir, milvus_collection="medical_rag"):
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    # Ensure destination directory exists
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize MilvusStore
    try:
        logging.info("Initializing MilvusStore...")
        # Make sure your MilvusStore is configured properly in src/core/vector_store.py
        vector_store = MilvusStore()
        # Ensure we are connected and collection is initialized
        if not vector_store.connected:
            vector_store.connect()
        vector_store.init_collection()
    except Exception as e:
        logging.error(f"Failed to initialize MilvusStore: {e}")
        return
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    # Process all files in source directory
    for file_path in source_path.iterdir():
        if file_path.is_file() and file_path.name != ".DS_Store":
            logging.info(f"Processing file: {file_path.name}")
            
            try:
                # 1. Load Document based on extension
                docs = []
                if file_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                    docs = loader.load()
                elif file_path.suffix.lower() in ['.docx', '.doc']:
                    loader = UnstructuredWordDocumentLoader(str(file_path))
                    docs = loader.load()
                else:
                    logging.warning(f"Unsupported file type: {file_path.name}. Skipping.")
                    continue
                
                if not docs:
                    logging.warning(f"No content extracted from {file_path.name}.")
                    continue
                
                # Convert to "Markdown/Text" implicitly through Langchain's load() which extracts text
                # 2. Chunking
                logging.info(f"Splitting {file_path.name} into chunks...")
                langchain_chunks = text_splitter.split_documents(docs)
                
                # Convert Langchain Document objects to MilvusStore expected dictionary format
                chunks_to_insert = []
                for chunk in langchain_chunks:
                    chunks_to_insert.append({
                        "text": chunk.page_content,
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
                
                # 3. Vectorize and insert into Milvus
                if chunks_to_insert:
                    logging.info(f"Inserting {len(chunks_to_insert)} chunks from {file_path.name} into Milvus...")
                    vector_store.insert_chunks(chunks_to_insert)
                    logging.info(f"Successfully vectorized {file_path.name}.")
                
                # 4. Move original file to oldf directory
                target_path = dest_path / file_path.name
                shutil.move(str(file_path), str(target_path))
                logging.info(f"Moved {file_path.name} to {dest_dir}")
                
            except Exception as e:
                logging.error(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    SOURCE_DIR = "/mnt/disk3/home/pg/RAG_Project/data/sf/"
    DEST_DIR = "/mnt/disk3/home/pg/RAG_Project/data/oldf/"
    
    process_documents(SOURCE_DIR, DEST_DIR)
    logging.info("Batch processing complete.")
