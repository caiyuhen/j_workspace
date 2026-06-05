
import os
from pymilvus import connections, Collection, utility

# Setup connection
try:
    print("Connecting to Milvus Lite (milvus_medical.db)...")
    connections.connect("default", uri="milvus_medical.db")
    
    collection_name = "medical_rag"
    
    if not utility.has_collection(collection_name):
        print(f"Collection {collection_name} does not exist.")
        exit(0)
        
    collection = Collection(collection_name)
    collection.load()
    
    num_entities = collection.num_entities
    print(f"Total Vectors: {num_entities}")
    
    # Define fields to analyze
    scalar_fields = [
        "western_medicines", "tcm_medicines", "diagnoses", 
        "pathology_types", "diagnostic_features", "gene_mutations",
        "cytology_checks", "surgeries", "radiotherapies", 
        "initial_treatments", "adjuvant_treatments",
        "stages", "syndromes", "principles"
    ]
    
    # Query data
    # Note: Querying all might be heavy if millions, but for <100k it's fine. 
    # Let's try 10000 limit first to be safe, if num_entities > 10000 we extrapolate or page.
    limit = 10000
    if num_entities > 10000:
        print(f"Warning: Only analyzing first {limit} entities for node/edge stats.")
    
    res = collection.query(
        expr="", 
        output_fields=scalar_fields,
        limit=limit
    )
    
    total_nodes = set()
    total_edges = 0
    
    field_counts = {f: 0 for f in scalar_fields}
    
    for hit in res:
        for field in scalar_fields:
            val = hit.get(field)
            if val:
                # Assuming comma-separated values
                items = [item.strip() for item in val.split(",") if item.strip()]
                if items:
                    field_counts[field] += len(items)
                    # Add to nodes
                    for item in items:
                        total_nodes.add(f"{field}:{item}") # Unique node by type:value
                    
                    # Edges: implicitly, each item is connected to the chunk (vector)
                    # And items within the same chunk are connected to each other (clique)
                    # For "extracted relations", usually implies (Entity) -> (Chunk) or (Entity) -> (Entity)
                    # Let's count (Entity) -> (Chunk) edges as simple relations
                    total_edges += len(items)

    print(f"Total Extracted Entities (Nodes): {len(total_nodes)}")
    print(f"Total Extracted Relations (Edges): {total_edges}")
    
    print("\nBreakdown by Field (Relations/Mentions):")
    for f, count in field_counts.items():
        print(f"  {f}: {count}")
        
except Exception as e:
    print(f"Error: {e}")
