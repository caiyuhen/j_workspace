from pymilvus import Collection, connections

conn = connections.connect("default", host="127.0.0.1", port="19530")

col = Collection("medical_rag")
col.load()

# Let's get a few sources
results = col.query(expr="source != ''", output_fields=["source"], limit=1000)
sources = set([r['source'] for r in results])
print("Sample sources in medical_rag:")
for i, s in enumerate(list(sources)[:20]):
    print(i, s)
