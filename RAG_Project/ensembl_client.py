import requests
import re
from typing import Dict, Any, Optional, List

class EnsemblClient:
    """
    Client for interacting with the Ensembl REST API to retrieve gene and protein information.
    """
    BASE_URL = "https://rest.ensembl.org"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def get_gene_info(self, gene_symbol: str, species: str = "homo_sapiens") -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a specific gene symbol.
        """
        endpoint = f"/lookup/symbol/{species}/{gene_symbol}"
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            params = {"content-type": "application/json"}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                print(f"Ensembl API Error 400: Bad Request for {gene_symbol}")
                return None
            else:
                print(f"Ensembl API Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Ensembl Request Failed: {e}")
            return None

    def extract_gene_symbols(self, text: str) -> List[str]:
        """
        Extracts potential gene symbols from text.
        Simple heuristic: Uppercase alphanumeric strings of length 3-10.
        """
        pattern = r'(?:^|[^A-Za-z0-9])([A-Z][A-Z0-9-]{2,9})(?:$|[^A-Za-z0-9])'
        matches = re.findall(pattern, text)
        
        common_acronyms = {"DNA", "RNA", "MRI", "CT", "PET", "WHO", "USA", "UK", "HIV", "AIDS", "PCR", "RAG", "LLM", "API", "REST"}
        filtered = [m for m in matches if m not in common_acronyms]
        
        return list(set(filtered))

    def format_gene_info(self, gene_info: Dict[str, Any]) -> str:
        """
        Formats the raw JSON response into a readable string.
        """
        if not gene_info:
            return ""
            
        lines = []
        lines.append(f"Gene Symbol: {gene_info.get('display_name')}")
        lines.append(f"ID: {gene_info.get('id')}")
        lines.append(f"Description: {gene_info.get('description', 'N/A')}")
        lines.append(f"Biotype: {gene_info.get('biotype')}")
        lines.append(f"Assembly: {gene_info.get('assembly_name')}")
        lines.append(f"Location: {gene_info.get('seq_region_name')}:{gene_info.get('start')}-{gene_info.get('end')} ({gene_info.get('strand')})")
        
        return "\n".join(lines)
