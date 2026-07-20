
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
<<<<<<< HEAD
import time
import uuid
=======
>>>>>>> origin/main

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

<<<<<<< HEAD
import requests

=======
>>>>>>> origin/main
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    use_pubmed: bool = False
    filters: Optional[Dict[str, Any]] = None
<<<<<<< HEAD
    file_paths: Optional[List[str]] = None
    summarize: bool = True
    return_citations: bool = True
    return_debug: bool = False
    score_threshold: Optional[float] = None
    source_filter: Optional[List[str]] = None
=======
>>>>>>> origin/main

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]] = None
<<<<<<< HEAD
    summary: Optional[str] = None
    retrieval_meta: Optional[Dict[str, Any]] = None

def _normalize_source(source_name: Optional[str]) -> str:
    return (source_name or "").strip().lower()

def _source_matches(source_name: Optional[str], source_filter: Optional[set]) -> bool:
    if not source_filter:
        return True
    normalized = _normalize_source(source_name)
    if normalized in source_filter:
        return True
    alias_map = {
        "milvus": {"local", "vector"},
        "pubmed": {"ncbi"},
        "clinicaltrials": {"clinicaltrials.gov", "trials"}
    }
    for canonical, aliases in alias_map.items():
        if normalized == canonical and source_filter.intersection(aliases):
            return True
    return False

def _score_matches(source_name: Optional[str], score: Any, threshold: Optional[float]) -> bool:
    if threshold is None or score is None:
        return True
    try:
        score_value = float(score)
    except (TypeError, ValueError):
        return True
    if _normalize_source(source_name) == "milvus":
        return score_value <= threshold
    return score_value >= threshold

def _collect_citations(results: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    citations = []
    for item in results[:limit]:
        citations.append({
            "source": item.get("source"),
            "source_type": item.get("source_type"),
            "score": item.get("score"),
            "snippet": (item.get("text") or "")[:300]
        })
    return citations
=======
>>>>>>> origin/main

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
<<<<<<< HEAD
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    request_id = str(uuid.uuid4())
    start_time = time.time()
    all_results = []
    analysis_result = None
    source_filter = {_normalize_source(source) for source in (request.source_filter or []) if source}
    local_hits = 0
    pubmed_hits = 0
    external_hits = 0
    warning_messages = []
=======
    all_results = []
    analysis_result = None
>>>>>>> origin/main

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
<<<<<<< HEAD
                    if _source_matches(doc.get("source_type"), source_filter) and _score_matches(doc.get("source_type"), doc.get("score"), request.score_threshold):
                        all_results.append(doc)
                        if _normalize_source(doc.get("source_type")) == "milvus":
                            local_hits += 1
                        else:
                            external_hits += 1
            if "analysis" in rag_response:
                analysis_result = rag_response["analysis"]
        except Exception as e:
            warning_messages.append("milvus_search_failed")
            logger.error("RAG Engine search failed request_id=%s error=%s", request_id, e)
    else:
        warning_messages.append("rag_engine_unavailable")
=======
                    all_results.append(doc)
            if "analysis" in rag_response:
                analysis_result = rag_response["analysis"]
        except Exception as e:
            logger.error(f"RAG Engine search failed: {e}")
>>>>>>> origin/main

    # 2. PubMed Retrieval
    if request.use_pubmed and pubmed_client:
        try:
            pubmed_docs = pubmed_client.search(request.query, max_results=request.top_k)
            # Convert to unified format
            for pd in pubmed_docs:
<<<<<<< HEAD
                doc = {
=======
                all_results.append({
>>>>>>> origin/main
                    "text": f"Title: {pd.get('Title')}\nAbstract: {pd.get('Abstract')}",
                    "source": f"PubMed (PMID: {pd.get('PMID')})",
                    "score": 0.0, # PubMed doesn't return score in this client
                    "source_type": "PubMed",
                    "metadata": pd
<<<<<<< HEAD
                }
                if _source_matches(doc.get("source_type"), source_filter) and _score_matches(doc.get("source_type"), doc.get("score"), request.score_threshold):
                    all_results.append(doc)
                    pubmed_hits += 1
        except Exception as e:
            warning_messages.append("pubmed_search_failed")
            logger.error("PubMed search failed request_id=%s error=%s", request_id, e)
    elif request.use_pubmed:
        warning_messages.append("pubmed_client_unavailable")

    summary = None
    if request.summarize and all_results:
        try:
            context = "\n\n".join([r.get('text', '') for r in all_results[:5]])
            prompt = f"请基于以下参考资料，对用户的问题进行准确的总结提炼。\n\n参考资料:\n{context}\n\n用户问题: {request.query}"
            llm_payload = {
                "messages": [
                    {"role": "system", "content": [{"type": "text", "text": "你是一个专业的医疗信息总结助手。"}]},
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
                "max_new_tokens": 512,
                "temperature": 0.3
            }
            llm_res = requests.post("http://llm_service:9013/generate", json=llm_payload, timeout=60)
            if llm_res.status_code == 200:
                summary = llm_res.json().get("response", "")
            else:
                warning_messages.append("llm_summary_failed")
        except Exception as e:
            warning_messages.append("llm_summary_failed")
            logger.error("LLM summarization failed request_id=%s error=%s", request_id, e)

    elapsed_ms = int((time.time() - start_time) * 1000)
    retrieval_meta = {
        "request_id": request_id,
        "query": request.query,
        "top_k": request.top_k,
        "use_pubmed": request.use_pubmed,
        "summarize": request.summarize,
        "source_filter": request.source_filter or [],
        "score_threshold": request.score_threshold,
        "local_hits": local_hits,
        "pubmed_hits": pubmed_hits,
        "external_hits": external_hits,
        "total_hits": len(all_results),
        "elapsed_ms": elapsed_ms,
        "warnings": warning_messages
    }
    if request.return_citations:
        retrieval_meta["citations"] = _collect_citations(all_results)
    if request.return_debug:
        retrieval_meta["analysis_snapshot"] = analysis_result

    logger.info(
        "Search completed request_id=%s query=%s top_k=%s local_hits=%s pubmed_hits=%s external_hits=%s elapsed_ms=%s warnings=%s",
        request_id,
        request.query,
        request.top_k,
        local_hits,
        pubmed_hits,
        external_hits,
        elapsed_ms,
        warning_messages
    )
    return {
        "results": all_results,
        "analysis": analysis_result,
        "summary": summary,
        "retrieval_meta": retrieval_meta
    }

@app.get("/")
async def root():
    return {"message": "RAG Service is running. Access /docs for API documentation."}

=======
                })
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")

    return {
        "results": all_results,
        "analysis": analysis_result
    }

>>>>>>> origin/main
@app.get("/health")
async def health():
    return {"status": "ok", "rag_engine": rag_engine is not None, "pubmed_client": pubmed_client is not None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
