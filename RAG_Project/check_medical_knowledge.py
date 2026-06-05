from vector_store import MilvusStore
from pymilvus import Collection, utility

store = MilvusStore()
store.connect()

for col_name in ["medical_knowledge", "lung_cancer_rag", "medical_rag"]:
    if utility.has_collection(col_name):
        col = Collection(col_name)
        col.load()
        results = col.query(expr="source like '%乳腺%' or text like '%乳腺%'", output_fields=["source"], limit=100)
        sources = set([r['source'] for r in results])
        print(f"Sources in {col_name}:", sources)
        
