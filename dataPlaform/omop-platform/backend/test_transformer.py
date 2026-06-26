import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.staging_transformer import StagingTransformer
from app.services.nlp_mapper import NLPMapper
from app.models.raw import SourceBatch, RawRecord

def test():
    db = SessionLocal()
    batch = db.query(SourceBatch).first()
    print("Batch:", batch.id)
    
    # Check one raw record
    raw = db.query(RawRecord).filter(RawRecord.batch_id == batch.id).first()
    print("Sample Raw:", raw.row_data if raw else None)
    
    headers = list(raw.row_data.keys()) if raw else []
    print("Headers:", headers)
    
    auto_mapping = NLPMapper.generate_mapping(headers)
    print("Auto Mapping:", auto_mapping)
    
    transformer = StagingTransformer(db)
    print("Running transformer...")
    try:
        transformer.transform_batch_to_person(batch.id, auto_mapping)
        print("Transformer done.")
    except Exception as e:
        print("Transformer failed:", e)
        import traceback
        traceback.print_exc()
        
test()
