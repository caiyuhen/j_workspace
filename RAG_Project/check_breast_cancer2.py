from vector_store import MilvusStore
from pymilvus import Collection

store = MilvusStore()
store.connect()
col = Collection("medical_rag")
col.load()
results = col.query(expr="source like '中国肿瘤%'", output_fields=["source"], limit=100)
sources = set([r['source'] for r in results])
print("Sources in medical_rag:", sources)

if store.has_collection("lung_cancer_rag"):
    col2 = Collection("lung_cancer_rag")
    col2.load()
    results2 = col2.query(expr="source like '中国肿瘤%'", output_fields=["source"], limit=100)
    sources2 = set([r['source'] for r in results2])
    print("Sources in lung_cancer_rag:", sources2)

if store.has_collection("medical_knowledge"):
    col3 = Collection("medical_knowledge")
    col3.load()
    results3 = col3.query(expr="source like '中国肿瘤%'", output_fields=["source"], limit=100)
    sources3 = set([r['source'] for r in results3])
    print("Sources in medical_knowledge:", sources3)
