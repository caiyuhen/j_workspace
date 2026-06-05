import sys
import os

# 将项目根目录加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import random
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, MetaData, Table

# 数据库连接：PostgreSQL 15 (用户名postgres 密码root@123 数据库名postgres)
# 密码中包含 '@' 符号，需要进行 URL 编码 (%40)
PG_URL = "postgresql://postgres:root%40123@localhost:5432/postgres"

engine = create_engine(PG_URL)
metadata = MetaData()

# 创建患者表和诊疗记录表
patients = Table(
    'patients', metadata,
    Column('id', String(50), primary_key=True),
    Column('name', String(50)),
    Column('age', Integer),
    Column('gender', String(10)),
    Column('base_risk_level', String(20))
)

records = Table(
    'clinical_records', metadata,
    Column('record_id', Integer, primary_key=True, autoincrement=True),
    Column('patient_id', String(50), ForeignKey('patients.id')),
    Column('fbg', Float),
    Column('sbp', Float),
    Column('dbp', Float),
    Column('heart_rate', Integer),
    Column('diagnosis', String(255)),
    Column('timestamp', DateTime)
)

def init_pg_data():
    metadata.drop_all(engine)
    metadata.create_all(engine)
    
    print("PostgreSQL 数据库表已创建。正在生成 150 名患者测试数据...")
    start_time = time.time()
    
    conn = engine.connect()
    trans = conn.begin()
    try:
        patient_data = []
        record_data = []
        for i in range(1, 151):
            p_id = f"PAT-{1000+i}"
            gender = random.choice(["男", "女"])
            patient_data.append({
                "id": p_id,
                "name": f"患者_{i}号",
                "age": random.randint(40, 85),
                "gender": gender,
                "base_risk_level": random.choice(["低危", "中危", "高危", "极高危"])
            })
            
            # 为每位患者生成 3 条模拟诊疗记录
            for j in range(3):
                record_data.append({
                    "patient_id": p_id,
                    "fbg": round(random.uniform(5.0, 11.0), 1),
                    "sbp": round(random.uniform(110, 180), 1),
                    "dbp": round(random.uniform(70, 110), 1),
                    "heart_rate": random.randint(60, 100),
                    "diagnosis": random.choice(["2型糖尿病控制良好", "高血压合并心肌缺血", "代谢综合征", "心律不齐"]),
                    "timestamp": "2024-01-01 10:00:00" # 简化时间
                })
        
        conn.execute(patients.insert(), patient_data)
        conn.execute(records.insert(), record_data)
        trans.commit()
        print(f"数据初始化完成！耗时: {time.time() - start_time:.3f} 秒")
    except Exception as e:
        trans.rollback()
        print(f"初始化失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_pg_data()
