from vector_store import MilvusStore
from pymilvus import Collection, connections

conn = connections.connect("default", host="127.0.0.1", port="19530")
col = Collection("medical_rag")
col.load()
results = col.query(expr="source == '乳腺癌疾病管理路径.md'", output_fields=["source"], limit=10)
print("Found chunks for 乳腺癌疾病管理路径.md:", len(results))
