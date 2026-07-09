import requests
import re
from typing import Dict, Any, List, Optional

class FDAClient:
    """
    Client for interacting with the openFDA Drug Adverse Event API.
    """
    BASE_URL = "https://api.fda.gov/drug/event.json"
    API_KEY = "gKwp4EY75rEkZEr0Ft13f8WzWoUKxzlU3bByIXmc"
    
    # Common drug name translations (Chinese -> English)
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

    def search_events(self, drug_name: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Searches for adverse events associated with a drug name.
        """
        if not drug_name:
            return []

        search_term = drug_name
        
        # Check for translation (simple substring matching)
        translation_found = False
        for cn, en in self.DRUG_TRANSLATIONS.items():
            if cn in drug_name:
                search_term = en
                translation_found = True
                break
        
        # If no translation found, and query has Chinese, try to extract English parts
        if not translation_found and re.search(r'[\u4e00-\u9fa5]', drug_name):
             english_parts = re.findall(r'[a-zA-Z0-9\-\.]+', drug_name)
             if english_parts:
                 search_term = " ".join(english_parts)

        # Construct the search query
        # We search in patient.drug.medicinalproduct
        # Using exact match for the drug name if possible, or simple search
        search_query = f'patient.drug.medicinalproduct:"{search_term}"'
        
        params = {
            "api_key": self.API_KEY,
            "search": search_query,
            "limit": limit
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                print(f"FDA API Error {response.status_code}: {response.text}")
                return []
        except Exception as e:
            print(f"FDA Request Failed: {e}")
            return []

    def format_event_info(self, event: Dict[str, Any]) -> str:
        """
        Formats a single adverse event record into a readable string.
        """
        if not event:
            return ""

        lines = []
        report_id = event.get("safetyreportid", "N/A")
        lines.append(f"Report ID: {report_id}")
        
        # Patient Info
        patient = event.get("patient", {})
        reaction_list = patient.get("reaction", [])
        reactions = [r.get("reactionmeddrapt", "") for r in reaction_list if r.get("reactionmeddrapt")]
        if reactions:
            lines.append(f"Reactions: {', '.join(reactions[:5])}")

        # Drugs
        drugs = patient.get("drug", [])
        drug_names = [d.get("medicinalproduct", "") for d in drugs if d.get("medicinalproduct")]
        if drug_names:
            lines.append(f"Concomitant Drugs: {', '.join(drug_names[:5])}")
            
        serious = event.get("serious")
        if serious == "1":
            lines.append("Serious: Yes")
            
        return "\n".join(lines)
