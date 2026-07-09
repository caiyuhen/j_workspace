
import config
from pymilvus import connections, Collection, utility
from collections import Counter
import json

def visualize_kg():
    print("Connecting to Milvus...", flush=True)
    connections.connect("default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    print("Connected.", flush=True)
    
    if not utility.has_collection(config.COLLECTION_NAME):
        print(f"Collection {config.COLLECTION_NAME} does not exist.", flush=True)
        return

    collection = Collection(config.COLLECTION_NAME)
    print("Loading collection...", flush=True)
    collection.load()
    
    print(f"Collection: {config.COLLECTION_NAME}", flush=True)
    print(f"Total entities: {collection.num_entities}", flush=True)
    
    # Fields to analyze
    kg_fields = [
        "stages", "syndromes", "principles",
        "western_medicines", "tcm_medicines", "diagnoses",
        "pathology_types", "diagnostic_features", "gene_mutations",
        "cytology_checks", "surgeries", "radiotherapies",
        "initial_treatments", "adjuvant_treatments"
    ]
    
    print("\n=== Knowledge Graph Statistics ===", flush=True)
    
    # Query all data (limit to 1000 for speed)
    results = collection.query(
        expr="id >= 0",
        output_fields=kg_fields,
        limit=1000
    )
    
    stats = {field: Counter() for field in kg_fields}
    
    for res in results:
        for field in kg_fields:
            val = res.get(field)
            if val:
                # Assuming val is a comma-separated string or list
                if isinstance(val, str):
                    items = [item.strip() for item in val.split(",") if item.strip()]
                elif isinstance(val, list):
                    items = val
                else:
                    items = []
                
                stats[field].update(items)
    
    for field, counter in stats.items():
        print(f"\n[{field.upper()}] - Found in {sum(counter.values())} instances")
        if counter:
            print("  Top 5 entities:")
            for item, count in counter.most_common(5):
                print(f"    - {item}: {count}")
        else:
            print("  (No data found)")

if __name__ == "__main__":
    visualize_kg()
