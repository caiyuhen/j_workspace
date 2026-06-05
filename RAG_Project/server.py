
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Import local modules
# Assuming server.py is in the root of RAG_Project
from rag_engine import RAGEngine
from pubmed_interface.pubmed_client import PubMedClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Service")

app = FastAPI(title="RAG Retrieval Service", description="Dedicated service for Medical RAG and PubMed retrieval")

# Global instances
rag_engine = None
pubmed_client = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    use_pubmed: bool = False
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup_event():
    global rag_engine, pubmed_client
    logger.info("Initializing RAG Engine (Milvus)...")
    try:
        rag_engine = RAGEngine()
        rag_engine.initialize()
        logger.info("RAG Engine initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Engine: {e}")
        # We might continue if PubMed is still usable, or fail hard.
        # For now, let's log and continue, but RAG calls will fail.

    logger.info("Initializing PubMed Client...")
    try:
        pubmed_client = PubMedClient()
        logger.info("PubMed Client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize PubMed Client: {e}")

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    all_results = []
    analysis_result = None

    # 1. Milvus Retrieval (RAG Engine)
    if rag_engine:
        try:
            # RAGEngine.answer() does analysis + search. 
            # We might want to separate them if we want pure search, but answer() returns 'retrieved_docs'.
            # Let's use answer() for now as it handles the logic.
            # Or better, let's use the store directly if we want raw results, but RAGEngine adds logic.
            # The user said "Encapsulate RAG_Project logic", so using RAGEngine is correct.
            
            # However, RAGEngine.answer returns a dict with 'answer_prompt', 'retrieved_docs', 'analysis'.
            # We just want retrieved docs and analysis.
            rag_response = rag_engine.answer(request.query, top_k=request.top_k)
            if "retrieved_docs" in rag_response:
                for doc in rag_response["retrieved_docs"]:
                    if "source_type" not in doc:
                        doc["source_type"] = "Milvus"
                    all_results.append(doc)
            if "analysis" in rag_response:
                analysis_result = rag_response["analysis"]
        except Exception as e:
            logger.error(f"RAG Engine search failed: {e}")

    # 2. PubMed Retrieval
    if request.use_pubmed and pubmed_client:
        try:
            pubmed_docs = pubmed_client.search(request.query, max_results=request.top_k)
            # Convert to unified format
            for pd in pubmed_docs:
                all_results.append({
                    "text": f"Title: {pd.get('Title')}\nAbstract: {pd.get('Abstract')}",
                    "source": f"PubMed (PMID: {pd.get('PMID')})",
                    "score": 0.0, # PubMed doesn't return score in this client
                    "source_type": "PubMed",
                    "metadata": pd
                })
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")

    return {
        "results": all_results,
        "analysis": analysis_result
    }

@app.get("/health")
async def health():
    return {"status": "ok", "rag_engine": rag_engine is not None, "pubmed_client": pubmed_client is not None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
