import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path so we can import modules
sys.path.append(os.getcwd())

# Load .env
load_dotenv()

from pubmed_interface.pubmed_client import PubMedClient

def test_pubmed():
    print("Testing PubMed Client...")
    try:
        client = PubMedClient()
        query = "lung cancer"
        print(f"Searching for: {query}")
        
        results = client.search(query, max_results=5)
        
        print(f"Found {len(results)} results.")
        if results:
            print("First result:")
            print(results[0])
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pubmed()
