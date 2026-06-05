
import os
import time
import json
import logging
import requests
import threading
import ssl
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from langchain_community.document_loaders import PubMedLoader
import xmltodict

# Disable SSL verification for urllib (used by PubMedLoader)
ssl._create_default_https_context = ssl._create_unverified_context

# Configure logging
os.makedirs("pubmed_interface/logs", exist_ok=True)
logger = logging.getLogger("pubmed_client")
logger.setLevel(logging.ERROR)
fh = logging.FileHandler("pubmed_interface/logs/pubmed_error.log")
formatter = logging.Formatter("%(asctime)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)

# Load env
load_dotenv()

class PubMedClient:
    def __init__(self):
        self.api_key = os.getenv("PUBMED_API_KEY")
        self.base_url = os.getenv("PUBMED_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/")
        
        if not self.api_key:
            raise ValueError("PUBMED_API_KEY not found in .env")

        self.session = requests.Session()
        
        # Retry strategy
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        
        # Rate limiting state
        self.last_request_time = 0
        self.min_interval = 0.11  # slightly more than 0.1s to be safe (10 req/s = 0.1s/req)
        self.lock = threading.Lock()

    def _rate_limit(self):
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()

    def search(self, query: str, max_results: int = 100, sort: str = 'relevance') -> List[Dict]:
        """
        Use LangChain PubMedLoader to search and retrieve basic info.
        """
        self._rate_limit()
        
        # Retry loop for PubMedLoader (which uses urllib and might fail with 429)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loader = PubMedLoader(query=query, load_max_docs=max_results)
                # Inject API Key into the underlying client if available
                if self.api_key:
                    loader._client.api_key = self.api_key
                    loader._client.email = os.getenv("PUBMED_USER", "user@example.com")

                # Note: load() fetches max_docs. We can't easily control it here without hacking,
                # but we filter later.
                docs = loader.load() 
                
                # Limit to max_results
                docs = docs[:max_results]
                
                results = []
                for doc in docs:
                    # Extract fields from Document
                    meta = doc.metadata
                    # Structure: PMID, Title, Abstract, Author, Date, DOI
                    item = {
                        "PMID": meta.get("uid", ""),
                        "Title": meta.get("Title", ""),
                        "Abstract": doc.page_content,
                        "Author": meta.get("Authors", ""), 
                        "Date": meta.get("Published", ""),
                        "DOI": meta.get("DOI", "") 
                    }
                    results.append(item)
                
                return results

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Search attempt {attempt+1} failed for '{query}': {e}. Retrying...")
                    time.sleep(2 * (attempt + 1)) # Backoff
                else:
                    logger.error(f"Search failed for query '{query}': {str(e)}", exc_info=True)
                    return []
        return []

    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """
        Batch call EFetch to get MeSH, Journal, PMC ID.
        """
        if not pmids:
            return []

        results = []
        batch_size = 200 # EFetch limit advice
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]
            ids_str = ",".join(batch)
            
            params = {
                "db": "pubmed",
                "id": ids_str,
                "retmode": "xml",
                "api_key": self.api_key
            }
            
            self._rate_limit()
            try:
                url = f"{self.base_url}efetch.fcgi"
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = xmltodict.parse(response.content)
                
                # Parse XML
                articles = data.get("PubmedArticleSet", {}).get("PubmedArticle", [])
                if isinstance(articles, dict):
                    articles = [articles]
                
                for article in articles:
                    medline = article.get("MedlineCitation", {})
                    
                    # Safe get for PMID
                    pmid_elem = medline.get("PMID")
                    if isinstance(pmid_elem, dict):
                        pmid = pmid_elem.get("#text", "")
                    else:
                        pmid = str(pmid_elem) if pmid_elem else ""
                    
                    # MeSH
                    mesh_list = []
                    mesh_heading_list = medline.get("MeshHeadingList", {}).get("MeshHeading", [])
                    if isinstance(mesh_heading_list, dict):
                        mesh_heading_list = [mesh_heading_list]
                    for mesh in mesh_heading_list:
                        descriptor_elem = mesh.get("DescriptorName")
                        if isinstance(descriptor_elem, dict):
                            descriptor = descriptor_elem.get("#text", "")
                        else:
                            descriptor = str(descriptor_elem) if descriptor_elem else ""
                            
                        if descriptor:
                            mesh_list.append(descriptor)
                    
                    # Journal
                    journal_elem = medline.get("Article", {}).get("Journal", {}).get("Title")
                    if isinstance(journal_elem, dict):
                        journal = journal_elem.get("#text", "")
                    else:
                        journal = str(journal_elem) if journal_elem else ""
                    
                    # PMC ID
                    pmc_id = ""
                    article_id_list = article.get("PubmedData", {}).get("ArticleIdList", {}).get("ArticleId", [])
                    if isinstance(article_id_list, dict):
                        article_id_list = [article_id_list]
                    for aid in article_id_list:
                        if isinstance(aid, dict):
                            if aid.get("@IdType") == "pmc":
                                pmc_id = aid.get("#text")
                                break
                        # If aid is not dict, it's just text, likely no attributes so no IdType check possible
                            
                    results.append({
                        "PMID": pmid,
                        "MeSH": mesh_list,
                        "Journal": journal,
                        "PMC_ID": pmc_id
                    })

            except Exception as e:
                logger.error(f"Fetch details failed for batch {batch}: {str(e)}", exc_info=True)
        
        return results

    def save_to_jsonl(self, data: List[Dict], path: str):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for entry in data:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Save to JSONL failed for {path}: {str(e)}", exc_info=True)
