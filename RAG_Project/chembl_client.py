import requests
from typing import Dict, Any, Optional, List

class ChEMBLClient:
    """
    Client for interacting with the ChEMBL REST API to retrieve molecule and target information.
    """
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def search_molecule(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for molecules using a text query.
        """
        url = f"{self.BASE_URL}/molecule/search"
        
        try:
            params = {
                "q": query,
                "format": "json",
                "limit": 3
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                molecules = data.get('molecules', [])
                return molecules[:3]
            else:
                print(f"ChEMBL API Error {response.status_code}")
                return []
        except Exception as e:
            print(f"ChEMBL Request Failed: {e}")
            return []

    def format_molecule_info(self, molecule_info: Dict[str, Any]) -> str:
        """
        Formats the raw JSON response into a readable string.
        """
        if not molecule_info:
            return ""
            
        lines = []
        pref_name = molecule_info.get('pref_name')
        chembl_id = molecule_info.get('molecule_chembl_id')
        
        lines.append(f"Molecule Name: {pref_name if pref_name else 'Unknown'}")
        lines.append(f"ChEMBL ID: {chembl_id}")
        
        props = molecule_info.get('molecule_properties') or {}
        if props:
            lines.append(f"Formula: {props.get('full_molformula', 'N/A')}")
            lines.append(f"Molecular Weight: {props.get('full_mwt', 'N/A')}")
            
        atc = molecule_info.get('atc_classifications', [])
        if atc:
            lines.append(f"ATC Codes: {', '.join(atc[:3])}")
            
        black_box = molecule_info.get('black_box_warning')
        if black_box:
             lines.append(f"Black Box Warning: Yes")
             
        return "\n".join(lines)
