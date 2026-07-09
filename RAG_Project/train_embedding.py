import os
import sys

# Prevent segmentation faults by limiting threads and parallelism
# Must be set BEFORE importing torch
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1" 
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import config # Import config first to set HF_ENDPOINT environment variable
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses, models, datasets
from torch.utils.data import DataLoader
# The `datasets` module in sentence_transformers is actually using the `datasets` library under the hood or expects it.
import nltk
import zipfile
import shutil

def ensure_nltk_resource(resource_path, download_id):
    try:
        nltk.data.find(resource_path)
    except (LookupError, zipfile.BadZipFile, OSError):
        print(f"Resource {download_id} missing or corrupted. Downloading...")
        try:
            nltk.download(download_id, quiet=True)
        except Exception as e:
            print(f"Failed to download {download_id}: {e}")
            # Try to force download/cleanup if possible, but usually standard download works.

ensure_nltk_resource('tokenizers/punkt_tab', 'punkt_tab')
ensure_nltk_resource('tokenizers/punkt', 'punkt')

from data_processor import DataProcessor, TextChunker

import random

def train_embedding(epochs=1, batch_size=16, model_name=None, max_seq_length=256, max_samples=None, output_path="output/trained_model_384", gpu_memory_fraction=None, num_workers=0, use_amp=True, checkpoint_steps=500):
    """
    Train/Fine-tune an embedding model using TSDAE (Transformer-based Denoising AutoEncoder)
    on the private corpus (Markdown files in data directory).
    This is an unsupervised method effective for domain adaptation.
    """
    # 0. Optimization & Configuration
    if torch.cuda.is_available():
        print(f"CUDA is available. Device: {torch.cuda.get_device_name(0)}")
        if gpu_memory_fraction:
            try:
                torch.cuda.set_per_process_memory_fraction(gpu_memory_fraction)
                print(f"GPU memory fraction limited to {gpu_memory_fraction:.2f}")
            except Exception as e:
                print(f"Warning: Could not set GPU memory fraction: {e}")
        
        # Enable CuDNN benchmark for speed
        torch.backends.cudnn.benchmark = True
    else:
        print("CUDA not available. Training on CPU (will be slow).")
        use_amp = False # Force disable AMP on CPU

    # 1. Check Permissions
    try:
        # Try to create the output directory or check writability
        os.makedirs(output_path, exist_ok=True)
        test_file = os.path.join(output_path, ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"Output directory verified: {output_path}")
    except PermissionError:
        print(f"ERROR: No write permission for directory '{output_path}'.")
        print("Please check file permissions or specify a different output path using --output_path")
        return
    except Exception as e:
        print(f"ERROR: Could not access output directory '{output_path}': {e}")
        return

    if model_name is None:
        # Check if config points to the output directory (circular dependency check)
        if "trained_model" in config.EMBEDDING_MODEL_NAME:
            print(f"Config points to output model '{config.EMBEDDING_MODEL_NAME}'. Using default base model 'BAAI/bge-small-zh-v1.5' for training.")
            model_name = "BAAI/bge-small-zh-v1.5"
        else:
            model_name = config.EMBEDDING_MODEL_NAME
    
    print(f"Starting training pipeline with base model: {model_name}")
    print(f"Data directory: {config.DATA_DIR}")
    print(f"Max Sequence Length: {max_seq_length}")
    print(f"Output Path: {output_path}")
    print(f"Batch Size: {batch_size}")
    print(f"Num Workers: {num_workers}")
    print(f"Mixed Precision (AMP): {use_amp}")
    print(f"Checkpoint Steps: {checkpoint_steps}")
    
    # 2. Load Data
    processor = DataProcessor(config.DATA_DIR)
    chunker = TextChunker(chunk_size=max_seq_length, chunk_overlap=0) # Use smaller chunks for training speed
    
    train_sentences = []
    print("Loading and chunking documents...")
    
    count = 0
    for doc in processor.iter_documents():
        doc['content'] = processor.clean_text(doc['content'])
        chunks = chunker.chunk_document(doc)
        for chunk in chunks:
            text = chunk['text']
            if len(text) > 50: # Filter short noise
                train_sentences.append(text)
                count += 1
                if count % 1000 == 0:
                    print(f"Loaded {count} sentences...", end='\r')
    
    print(f"\nTotal training sentences available: {len(train_sentences)}")
    
    if not train_sentences:
        print("No data found to train on.")
        return

    # Data Sampling Optimization
    if max_samples and len(train_sentences) > max_samples:
        print(f"Downsampling data to {max_samples} random samples for efficiency...")
        random.shuffle(train_sentences)
        train_sentences = train_sentences[:max_samples]
    
    print(f"Final training set size: {len(train_sentences)}")

    # 3. Prepare Model
    try:
        word_embedding_model = models.Transformer(model_name, max_seq_length=max_seq_length)
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
        model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
    except Exception as e:
        print(f"Could not load base model {model_name}: {e}")
        print("Falling back to 'sentence-transformers/all-MiniLM-L6-v2'")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        word_embedding_model = models.Transformer(model_name, max_seq_length=max_seq_length)
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
        model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

    # 4. Prepare Dataset for TSDAE
    train_dataset = datasets.DenoisingAutoEncoderDataset(train_sentences)
    # num_workers > 0 works on Windows if wrapped in main, which we are.
    # It speeds up data loading significantly.
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    
    # 5. Define Loss
    train_loss = losses.DenoisingAutoEncoderLoss(model, decoder_name_or_path=model_name, tie_encoder_decoder=True)
    
    # 6. Train
    print(f"Training for {epochs} epochs on {model.device}...")
    
    # Setup checkpoint path
    checkpoint_path = os.path.join(output_path, "checkpoints")
    os.makedirs(checkpoint_path, exist_ok=True)
        
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        weight_decay=0,
        scheduler='constantlr',
        optimizer_params={'lr': 3e-5},
        show_progress_bar=True,
        output_path=output_path,
        use_amp=use_amp, # Enable mixed precision if CUDA available and requested
        checkpoint_path=checkpoint_path,
        checkpoint_save_steps=checkpoint_steps,
        checkpoint_save_total_limit=3 # Keep only last 3 checkpoints
    )
    
    print(f"Training complete. Model saved to {output_path}")
    print(f"You can now update config.py to set EMBEDDING_MODEL_NAME = '{output_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train embedding model on private corpus")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--max_seq_length", type=int, default=256, help="Max sequence length (lower is faster)")
    parser.add_argument("--max_samples", type=int, default=None, help="Max number of training samples (None for all)")
    parser.add_argument("--output_path", type=str, default="output/trained_model_384", help="Path to save the trained model")
    parser.add_argument("--model_name", type=str, default=None, help="Base model name or path to checkpoint to resume from")
    parser.add_argument("--gpu_memory_fraction", type=float, default=None, help="Fraction of GPU memory to allocate (0.0-1.0)")
    parser.add_argument("--num_workers", type=int, default=0, help="Number of data loading workers (default 0, try 2 or 4 for speed)")
    parser.add_argument("--no_amp", action="store_true", help="Disable Mixed Precision (AMP) training")
    parser.add_argument("--checkpoint_steps", type=int, default=500, help="Save checkpoint every N steps")
    args = parser.parse_args()
    
    # Enable multiprocessing support for Windows
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    train_embedding(
        epochs=args.epochs, 
        batch_size=args.batch_size, 
        model_name=args.model_name,
        max_seq_length=args.max_seq_length, 
        max_samples=args.max_samples, 
        output_path=args.output_path,
        gpu_memory_fraction=args.gpu_memory_fraction,
        num_workers=args.num_workers,
        use_amp=not args.no_amp,
        checkpoint_steps=args.checkpoint_steps
    )
