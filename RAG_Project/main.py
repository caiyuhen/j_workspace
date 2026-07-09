import argparse
import sys
import os
import threading
import queue
import time
import pickle
from data_processor import process_data_stream
from vector_store import MilvusStore
from rag_engine import RAGEngine

def ingest_data():
    print("Starting data ingestion pipeline...", flush=True)
    
    total_chunks = 0

    # Init Vector Store
    store = MilvusStore()
    store.connect()
    if not store.connected:
        print("FATAL: Could not connect to Milvus. Exiting.")
        return
        
    store.init_collection()
    
    # Process and insert in stream
    print("Step 1: Processing data and inserting into Milvus...", flush=True)
    
    # Increased batch size for efficiency
    BATCH_SIZE = 256 # Reduced from 1024 to prevent SegFaults
    
    for batch_chunks in process_data_stream(batch_size=BATCH_SIZE):
        if not batch_chunks:
            continue
            
        # 1. Insert into Vector Store (Milvus) - Fast
        try:
            store.insert_chunks(batch_chunks)
        except Exception as e:
            print(f"Error inserting to Milvus: {e}")
            continue
        
        total_chunks += len(batch_chunks)
        print(f"Processed {total_chunks} chunks so far.", end='\r')
        
    store.flush()
    print(f"\nStep 1 Complete. Total chunks in Milvus: {total_chunks}")


def start_chat():
    print("Initializing RAG System...")
    engine = RAGEngine()
    
    # Try to connect
    engine.store.connect()
    if engine.store.connected:
        engine.store.load_collection()
        if engine.store.collection is None:
            print(f"\nWarning: Collection '{engine.store.collection_name}' not found.")
            print("Please run 'python3 main.py --ingest' first to create and populate the database.")
    else:
        print("Warning: Milvus not connected. Running in simulation mode (no retrieval).")
    
    print("\n" + "="*50)
    print("通用医学智能诊疗RAG系统 (输入 'quit' 退出)")
    print("="*50)
    
    while True:
        query = input("\n请输入临床问题: ").strip()
        if query.lower() in ['quit', 'exit']:
            break
        if not query:
            continue
            
        print(f"\n[系统分析中...] 正在处理: {query}")
        
        try:
            result = engine.answer(query)
            
            print("\n--- 检索到的参考段落 (Top 3) ---")
            for i, doc in enumerate(result['retrieved_docs'][:3]):
                print(f"[{i+1}] {doc['source']} (相关性: {doc['score']:.4f})")
                print(f"    Tags: {doc['metadata']}")
                print(f"    Content: {doc['text'][:100]}...")
            
            print("\n--- 生成的回答 Prompt ---")
            # In a real app, we would print the LLM response here
            # response = llm.generate(result['answer_prompt'])
            print("(Prompt已生成，准备发送给真实LLM接口)")
            print(result['answer_prompt'])
            
        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Medical RAG System")
    parser.add_argument('--ingest', action='store_true', help='Process data and ingest into Milvus')
    parser.add_argument('--chat', action='store_true', help='Start chat interface')
    
    args = parser.parse_args()
    
    if args.ingest:
        ingest_data()
    elif args.chat:
        start_chat()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
