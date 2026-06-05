from vector_store import MilvusStore
from ensembl_client import EnsemblClient
from chembl_client import ChEMBLClient
from fda_client import FDAClient
from clinical_trials_client import ClinicalTrialsClient
from typing import Dict, Any, List

class RAGEngine:
    """
    Core RAG Engine that coordinates retrieval from multiple sources (Milvus, Ensembl, ChEMBL, FDA, ClinicalTrials).
    """
    def __init__(self):
        self.store = MilvusStore()
        self.ensembl = EnsemblClient()
        self.chembl = ChEMBLClient()
        self.fda = FDAClient()
        self.trials = ClinicalTrialsClient()
        
    def initialize(self):
        """
        Initialize connections (Milvus, etc.)
        """
        print("Initializing RAG Engine components...")
        self.store.connect()
        if self.store.connected:
            self.store.load_collection()
        print(f"Milvus connected: {self.store.connected}")
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Simple query analysis.
        """
        return {
            "original_query": query,
            "intent": "general",
            "filters": {}
        }
        
    def answer(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Main entry point for answering a query.
        """
        analysis = self.analyze_query(query)
        
        # 1. Retrieve from Milvus (if connected)
        results = []
        if self.store.connected:
             results = self.store.search(query, top_k=top_k)
             for res in results:
                 res['source_type'] = 'Milvus'

        # 2. Retrieve from Ensembl (Gene info)
        gene_symbols = self.ensembl.extract_gene_symbols(query)
        if gene_symbols:
            print(f"Detected Gene Symbols: {gene_symbols}")
            for gene in gene_symbols:
                info = self.ensembl.get_gene_info(gene)
                if info:
                    formatted_info = self.ensembl.format_gene_info(info)
                    results.insert(0, {
                        "source": f"Ensembl Knowledge Base ({gene})",
                        "text": formatted_info,
                        "score": 1.0,
                        "source_type": "Ensembl",
                        "metadata": {"type": "external_api", "id": info.get("id"), "source_type": "Ensembl"}
                    })

        # 3. Retrieve from ChEMBL (Molecule info)
        # Removed length check to allow searching for longer queries (e.g. translated ones)
        try:
             molecules = self.chembl.search_molecule(query)
             for mol in molecules:
                formatted_mol = self.chembl.format_molecule_info(mol)
                mol_name = mol.get('pref_name') or mol.get('molecule_chembl_id')
                results.insert(0, {
                    "source": f"ChEMBL Knowledge Base ({mol_name})",
                    "text": formatted_mol,
                    "score": 0.9,
                    "source_type": "ChEMBL",
                    "metadata": {"type": "external_api", "id": mol.get("molecule_chembl_id"), "source_type": "ChEMBL"}
                })
        except Exception as e:
            print(f"ChEMBL search error: {e}")
             
        # 4. Retrieve from FDA (Adverse Events)
        try:
             fda_events = self.fda.search_events(query, limit=1)
             for event in fda_events:
                 formatted_event = self.fda.format_event_info(event)
                 report_id = event.get('safetyreportid')
                 results.insert(0, {
                     "source": f"FDA Adverse Event ({report_id})",
                     "text": formatted_event,
                     "score": 0.85,
                     "source_type": "FDA",
                     "metadata": {"type": "external_api", "id": report_id, "source_type": "FDA", "details": event}
                 })
        except Exception as e:
            print(f"FDA search error: {e}")
             
        # 5. Retrieve from ClinicalTrials.gov (Studies)
        try:
             studies = self.trials.search_studies(query, limit=1)
             for study in studies:
                 formatted_study = self.trials.format_study_info(study)
                 protocol = study.get("protocolSection", {})
                 id_module = protocol.get("identificationModule", {})
                 nct_id = id_module.get("nctId", "N/A")
                 
                 results.insert(0, {
                     "source": f"ClinicalTrials.gov ({nct_id})",
                     "text": formatted_study,
                     "score": 0.8,
                     "source_type": "ClinicalTrials",
                     "metadata": {"type": "external_api", "id": nct_id, "source_type": "ClinicalTrials", "details": study}
                 })
        except Exception as e:
            print(f"ClinicalTrials search error: {e}")
        
        # Construct Answer Prompt
        context = "\n\n".join([r['text'] for r in results[:5]])
        prompt = f"""基于以下参考资料回答问题。如果参考资料不足，请说明。

参考资料:
{context}

用户问题: {query}
"""
        return {
            "answer_prompt": prompt,
            "retrieved_docs": results,
            "analysis": analysis
        }
