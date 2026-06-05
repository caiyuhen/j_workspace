from vector_store import MilvusStore
from pymilvus import Collection

store = MilvusStore()
store.connect()
col = Collection("medical_rag")
col.load()
results = col.query(expr="source like '%乳腺%' or text like '%乳腺%'", output_fields=["source", "text"], limit=10)
print(f"Found {len(results)} Breast Cancer knowledge documents in medical_rag")
for r in results[:3]:
    print(r['source'], r['text'][:100])
    
col2 = Collection("lung_cancer_rag")
col2.load()
results2 = col2.query(expr="source like '%乳腺%' or text like '%乳腺%'", output_fields=["source", "text"], limit=10)
print(f"Found {len(results2)} Breast Cancer knowledge documents in lung_cancer_rag")
for r in results2[:3]:
    print(r['source'], r['text'][:100])
