import requests
import re
from typing import Dict, Any, List, Optional

class ClinicalTrialsClient:
    """
    Client for interacting with the ClinicalTrials.gov API v2.
    """
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    
    # Common drug name translations (Chinese -> English)
    # Reusing the same translation logic as FDA client for consistency
    DRUG_TRANSLATIONS = {
        "阿司匹林": "ASPIRIN",
        "布洛芬": "IBUPROFEN",
        "对乙酰氨基酚": "ACETAMINOPHEN",
        "扑热息痛": "ACETAMINOPHEN",
        "二甲双胍": "METFORMIN",
        "阿莫西林": "AMOXICILLIN",
        "青霉素": "PENICILLIN",
        "头孢": "CEPHALOSPORIN",
        "多西环素": "DOXYCYCLINE",
        "异维A酸": "ISOTRETINOIN"
    }

    def __init__(self):
        pass

    def search_studies(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for clinical trials using a text query.
        """
        if not query:
            return []

        search_term = query
        
        # Check for translation (simple substring matching)
        translation_found = False
        for cn, en in self.DRUG_TRANSLATIONS.items():
            if cn in query:
                search_term = en
                translation_found = True
                break
        
        # If no translation found, and query has Chinese, try to extract English parts (e.g. "GLP-1")
        if not translation_found and re.search(r'[\u4e00-\u9fa5]', query):
             english_parts = re.findall(r'[a-zA-Z0-9\-\.]+', query)
             if english_parts:
                 search_term = " ".join(english_parts)

        params = {
            "query.term": search_term,
            "pageSize": limit,
            "format": "json"
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("studies", [])
            else:
                print(f"ClinicalTrials API Error {response.status_code}: {response.text}")
                return []
        except Exception as e:
            print(f"ClinicalTrials Request Failed: {e}")
            return []

    def format_study_info(self, study: Dict[str, Any]) -> str:
        """
        Formats a single study record into a readable string.
        """
        if not study:
            return ""

        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        description_module = protocol.get("descriptionModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        
        nct_id = id_module.get("nctId", "N/A")
        title = id_module.get("officialTitle") or id_module.get("briefTitle", "No Title")
        status = status_module.get("overallStatus", "Unknown")
        conditions = conditions_module.get("conditions", [])
        
        lines = []
        lines.append(f"NCT ID: {nct_id}")
        lines.append(f"Title: {title}")
        lines.append(f"Status: {status}")
        
        if conditions:
            lines.append(f"Conditions: {', '.join(conditions[:5])}")
            
        summary = description_module.get("briefSummary", "")
        if summary:
            # Truncate summary if too long
            summary_text = summary[:200] + "..." if len(summary) > 200 else summary
            lines.append(f"Summary: {summary_text}")
            
        return "\n".join(lines)
