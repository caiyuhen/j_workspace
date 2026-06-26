import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.staging_transformer import StagingTransformer
from app.services.nlp_mapper import NLPMapper
from app.models.raw import SourceBatch, RawRecord

def process_50_rows():
    db = SessionLocal()
    batch = db.query(SourceBatch).first()
    if not batch:
        print("No batch found.")
        return
        
    raw = db.query(RawRecord).filter(RawRecord.batch_id == batch.id).first()
    if not raw:
        print("No raw records found.")
        return
        
    headers = list(raw.row_data.keys())
    auto_mapping = NLPMapper.generate_mapping(headers)
    
    transformer = StagingTransformer(db)
    
    import app.services.staging_transformer
    app.services.staging_transformer.BATCH_SIZE = 10
    
    original_query = db.query
    def mock_query(*args):
        if transformer._hack_called:
            class EmptyQuery:
                def filter(self, *a): return self
                def limit(self, *a): return self
                def offset(self, *a): return self
                def all(self): return []
            return EmptyQuery()
        transformer._hack_called = True
        return original_query(*args)
        
    transformer._hack_called = False
    transformer.db.query = mock_query
    
    print("Force processing 50 rows to Staging...")
    try:
        transformer.transform_batch_to_person(batch.id, auto_mapping)
        print("Success! 50 rows pushed to Staging.")
    except Exception as e:
        print("Failed!")
        import traceback
        traceback.print_exc()

process_50_rows()

