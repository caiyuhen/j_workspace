import sqlite3
import os
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from parser import PatientParser
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PatientService")

app = FastAPI(title="Patient Data Service", version="1.0.0")
parser = PatientParser()

# 数据库配置
DB_PATH = os.getenv("DB_PATH", "patients.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            cobb_angle REAL,
            data JSON
        )
    ''')
    conn.commit()
    conn.close()

# 用于演示的内存存储
PATIENT_DB = {} # 保留用于兼容，但在启动时同步

# 用于本地执行的项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 旧版单个 JSON 文件
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH", os.path.join(PROJECT_ROOT, "extracted_data.json"))

# OCR 提取的 JSON 文件目录
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH", os.path.join(PROJECT_ROOT, "extracted_data"))

# --- Pydantic 模型 ---
class PatientRecord(BaseModel):
    id: str
    name: str
    metrics: Dict[str, float]
    curve_data: Dict[str, List[float]]

# --- 端点 ---

@app.on_event("startup")
async def load_data():
    """在启动时从 JSON 文件和目录加载数据并同步到 SQLite"""
    global PATIENT_DB
    PATIENT_DB = {}
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    
    # 2. 从 extracted_data 目录加载 (OCR 输出)
    if os.path.exists(DATA_DIR_PATH) and os.path.isdir(DATA_DIR_PATH):
        try:
            for filename in os.listdir(DATA_DIR_PATH):
                if filename.endswith(".json") and not filename.startswith("sample"):
                    file_path = os.path.join(DATA_DIR_PATH, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data_content = json.load(f)
                            
                            # 处理嵌套
                            entry = data_content.get('extracted_data', data_content)
                            
                            # 解析
                            patient_name = filename.replace('_extracted.json', '').replace('.json', '')
                            record = parser.parse(entry, patient_name)
                            
                            # 存入 DB (Upsert)
                            cursor.execute('''
                                INSERT OR REPLACE INTO patients (id, name, cobb_angle, data)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                record['id'], 
                                record['name'], 
                                record.get('cobb_angle', 0.0),
                                json.dumps(record, ensure_ascii=False)
                            ))
                            
                            # 同步到内存缓存
                            PATIENT_DB[record['name']] = record
                            count += 1
                    except Exception as fe:
                        logger.warning(f"跳过 {filename}: {fe}")
            conn.commit()
            logger.info(f"已同步 {count} 条患者记录到数据库")
        except Exception as e:
            logger.error(f"加载目录数据失败: {e}")
    
    # 从数据库加载所有数据到内存 (作为缓存)
    cursor.execute("SELECT name, data FROM patients")
    rows = cursor.fetchall()
    for row in rows:
        name, data_json = row
        PATIENT_DB[name] = json.loads(data_json)
        
    conn.close()
    logger.info(f"服务就绪，当前缓存患者数: {len(PATIENT_DB)}")

@app.post("/reload")
async def reload_data():
    """手动重新加载数据源"""
    await load_data()
    return {"status": "reloaded", "patient_count": len(PATIENT_DB)}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "patient-service"}

@app.get("/patients", response_model=List[str])
def list_patients():
    return list(PATIENT_DB.keys())

@app.get("/patients/{patient_name}")
def get_patient(patient_name: str):
    """
    获取指定患者的详细信息。
    优先从内存数据库查找，如果未找到则尝试从文件加载。
    """
    logger.info(f"正在获取患者: {patient_name}")
    
    # 1. 尝试从内存数据库获取
    if patient_name in PATIENT_DB:
        return PATIENT_DB[patient_name]
        
    # 2. 如果内存中没有，尝试查找文件 (后备机制)
    try:
        # 查找此患者的 JSON 文件
        # 我们假设文件名为 "{patient_name}_extracted.json"
        # 还需要处理中文文件名编码
        json_filename = f"{patient_name}_extracted.json"
        json_path = os.path.join(DATA_DIR_PATH, json_filename)
        
        if not os.path.exists(json_path):
            # 尝试查找包含名称的文件（模糊匹配）
            files = os.listdir(DATA_DIR_PATH)
            found = False
            for f in files:
                if patient_name in f and f.endswith("_extracted.json"):
                    json_path = os.path.join(DATA_DIR_PATH, f)
                    found = True
                    break
            
            if not found:
                logger.warning(f"未找到患者 {patient_name} 的文件")
                raise HTTPException(status_code=404, detail=f"未找到患者 {patient_name} 的数据")

        logger.info(f"找到患者数据文件: {json_path}")

        # 2. 加载 JSON 数据
        with open(json_path, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)
            # Handle possible 'extracted_data' wrapper as seen in load_data
            if 'extracted_data' in ocr_data:
                ocr_data = ocr_data['extracted_data']

        # 3. 解析 OCR 数据为结构化患者模型
        patient_name_from_file = ocr_data.get('filename', patient_name)
        patient_data = parser.parse(ocr_data, patient_name_from_file)
        
        return patient_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检索患者 {patient_name} 时发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
