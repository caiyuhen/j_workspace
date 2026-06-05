from vector_store import MilvusStore
from pymilvus import Collection

store = MilvusStore()
store.connect()
col = Collection("medical_rag")
col.load()
results = col.query(expr="source like 'Breast_Cancer_Rule_%'", output_fields=["source", "text"], limit=10)
print(f"Found {len(results)} Breast_Cancer_Rule documents")
for r in results[:3]:
    print(r['source'], r['text'][:100])
