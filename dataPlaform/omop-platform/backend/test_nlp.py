import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.staging_transformer import StagingTransformer
from app.services.nlp_mapper import NLPMapper
from app.models.raw import SourceBatch, RawRecord

def test():
    db = SessionLocal()
    batch = db.query(SourceBatch).first()
    if not batch:
        print("No batch")
        return
        
    raw = db.query(RawRecord).filter(RawRecord.batch_id == batch.id).limit(10).all()
    headers = list(raw[0].row_data.keys()) if raw else []
    
    auto_mapping = NLPMapper.generate_mapping(headers)
    
    transformer = StagingTransformer(db)
    try:
        row = raw[0].row_data
        nlp_keys = ["chief_complaint", "history_of_present_illness", "imaging_reports", "admission_record", "daily_course_record", "discharge_summary", "treatment_plan"]
        
        print("--- NLP 批量性能测试开始 ---")
        start = time.time()
        count = 0
        
        # Collect texts
        texts_to_process = []
        for k in nlp_keys:
            val = row.get(k)
            if val:
                texts_to_process.append(val)
                
        # Batch extract
        if texts_to_process:
            results = transformer.ner_mapper.extract_entities_batch(texts_to_process, batch_size=16)
            count = len(results)
            
        end = time.time()
        
        print(f"提取了 {count} 个字段的文本实体。")
        print(f"单条患者记录（包含多个长文本字段）的 NLP 提取总耗时: {end - start:.3f} 秒")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

test()
