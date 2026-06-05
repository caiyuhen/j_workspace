from pymilvus import Collection, connections

conn = connections.connect("default", host="127.0.0.1", port="19530")
col = Collection("medical_knowledge")
print(col.schema)
