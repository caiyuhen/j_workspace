import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from pubmed_interface.pubmed_client import PubMedClient

def test_pubmed_chinese():
    print("Testing PubMed Client with Chinese query...")
    try:
        client = PubMedClient()
        query = "肺癌"
        print(f"Searching for: {query}")
        
        results = client.search(query, max_results=5)
        
        print(f"Found {len(results)} results.")
        if results:
            print("First result:")
            print(results[0])
        else:
            print("No results found. PubMed requires English queries or MeSH terms.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pubmed_chinese()
