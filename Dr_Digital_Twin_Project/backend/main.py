<<<<<<< HEAD
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time
import logging
import uuid
import base64
import os

import sys
import os
import httpx
import asyncio
from gradio_client import Client

# 设定 HuggingFace 镜像源以加速国内访问
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 将项目根目录加入 sys.path，解决模块导入找不到 'backend' 的问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.llm_service import get_clinical_diagnosis, generate_clinical_suggestion
from backend.services.tts_service import generate_doctor_speech
from backend.services.avatar_service import generate_avatar_video
from neo4j import GraphDatabase

# 假定有 mock twin service 或直接模拟数据
def update_digital_twin(patient_id, text):
    kg_reasoning = []
    try:
        # 连接图谱数据库
        URI = "neo4j://192.168.0.214:7687"
        AUTH = ("neo4j", "tes12345")
        driver = GraphDatabase.driver(URI, auth=AUTH)
        with driver.session(database="neo4j") as session:
            # 1. 动态响应患者主诉症状
            if "头痛" in text or "头通" in text:
                kg_reasoning.append({
                    "type": "chronic_alert",
                    "data": ["主诉症状: 头痛", "图谱关联推演", "警惕：原发性高血压导致血压波动"]
                })
            elif "胸闷" in text:
                kg_reasoning.append({
                    "type": "chronic_alert",
                    "data": ["主诉症状: 胸闷", "图谱关联推演", "警惕：冠心病引发心肌缺血"]
                })

            # 2. 查询真实的并发症关联
            comp_query = """
            MATCH (d1:Disease)-[r:CAUSES]->(d2:Disease)
            RETURN d1.name AS source, r.risk_factor AS relation, d2.name AS target
            LIMIT 2
            """
            for record in session.run(comp_query):
                kg_reasoning.append({
                    "type": "chronic_alert", 
                    "data": [record["source"], record["relation"] or "导致并发", record["target"]]
                })
                
            # 3. 查询真实的治疗关联
            med_query = """
            MATCH (m:Medication)-[r:TREATS]->(d:Disease)
            RETURN d.name AS disease, r.evidence_level AS evidence, m.name AS med
            LIMIT 2
            """
            for record in session.run(med_query):
                kg_reasoning.append({
                    "type": "medication_alert", 
                    "data": [f"针对 {record['disease']}", f"证据等级 {record['evidence']} 推荐", record["med"]]
                })
    except Exception as e:
        print(f"Neo4j 图谱查询失败: {e}")
        # 如果 Neo4j 连接失败，则降级返回兜底数据
        kg_reasoning = [
            {"type": "chronic_alert", "data": ["2型糖尿病", "高血糖加速动脉硬化", "冠心病风险提升"]},
            {"type": "medication_alert", "data": ["二甲双胍控制不佳", "推荐 SGLT-2抑制剂", "降低心衰风险"]}
        ]

    return {
        "name": "老王",
        "risk_level": "高危",
        "fbg": 8.5,
        "sbp": 145,
        "kg_reasoning": kg_reasoning
    }

from logging.handlers import RotatingFileHandler

# 创建日志目录
os.makedirs("logs", exist_ok=True)

# 配置根日志记录器
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# 后端日志文件 (包含错误日志)
file_handler = RotatingFileHandler("logs/backend.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
file_handler.setFormatter(log_formatter)

# 设置基础 logging
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
logger = logging.getLogger(__name__)

# 为前端创建专门的日志记录器
frontend_logger = logging.getLogger("frontend")
frontend_handler = RotatingFileHandler("logs/frontend.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
frontend_handler.setFormatter(logging.Formatter('%(asctime)s - FRONTEND - %(levelname)s - %(message)s'))
frontend_logger.addHandler(frontend_handler)
frontend_logger.setLevel(logging.INFO)
frontend_logger.propagate = False

app = FastAPI(title="Digital Twin Doctor API", version="1.0.0")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon", status_code=204)

@app.get("/static/undefined", include_in_schema=False)
async def static_undefined():
    from fastapi.responses import Response
    return Response(content="", status_code=204)


# =======================
# 0. 前端日志接收接口
# =======================
class FrontendLog(BaseModel):
    level: str
    message: str
    url: str = ""
    line: int = 0
    col: int = 0
    error: str = ""

@app.post("/api/v1/log")
async def receive_frontend_log(log_data: FrontendLog):
    log_msg = f"URL: {log_data.url} | Line: {log_data.line}:{log_data.col} | Msg: {log_data.message} | Err: {log_data.error}"
    if log_data.level.lower() == "error":
        frontend_logger.error(log_msg)
    elif log_data.level.lower() == "warn":
        frontend_logger.warning(log_msg)
    else:
        frontend_logger.info(log_msg)
    return {"status": "logged"}

def verify_sadtalker_api(url: str):
    logger.info(f"✅ SadTalker API verification skipped to avoid heartbeat spam.")
    return True

@app.on_event("startup")
async def startup_event():
    logger.info("Verifying connections to external services...")
    sadtalker_url = "http://192.168.0.214:7860"
    
    # 检查 SadTalker 接口
    logger.info(f"Checking SadTalker API at {sadtalker_url} ...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(sadtalker_url)
            if response.status_code == 200:
                logger.info(f"✅ SadTalker API is reachable and healthy (200 OK).")
            else:
                logger.warning(f"⚠️ SadTalker API at {sadtalker_url} returned status code {response.status_code}.")
    except Exception as e:
        logger.error(f"❌ Failed to connect to SadTalker API at {sadtalker_url}. Error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
# 静态资源挂载用于访问图片和生成的视频
app.mount("/docs_images", StaticFiles(directory="docs"), name="docs_images")

# =======================
# 1. 核心对话流 (包含头像视频流)
# =======================
class InteractRequest(BaseModel):
    patient_id: str
    text: str
    doctor_gender: str = "male"  # 'male' 或 'female'
    use_rag: bool = True

@app.post("/api/v1/chat/interact")
async def chat_interaction(req: InteractRequest):
    trace_id = str(uuid.uuid4())
    
    # 1. 数字孪生状态计算
    twin_data = update_digital_twin(req.patient_id, req.text)
    
    # 2. 意图理解与医学知识检索 (LLM)
    llm_response = get_clinical_diagnosis(req.patient_id, req.text, twin_data)
    doctor_reply = llm_response.get("reply", "")
    
    # 3. 语音合成 (TTS) - 转换医疗文本的逻辑已内置于 generate_doctor_speech
    audio_path = generate_doctor_speech(doctor_reply, req.doctor_gender)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 拷贝音频文件到指定目录
    chatter_box_out_dir = os.path.join(base_dir, "output", "chatter-box")
    os.makedirs(chatter_box_out_dir, exist_ok=True)
    if audio_path and os.path.exists(audio_path):
        import shutil
        shutil.copy(audio_path, os.path.join(chatter_box_out_dir, f"audio_{trace_id}.wav"))
    
    # 4. 生成唇形同步视频 (SadTalker)
    image_file = "3f38645a-9a34-4539-835e-a0138327f26d.jpg" if req.doctor_gender == "male" else "d970347c-8030-4035-ab24-f8c63e4a6e84.jpg"
    image_path = os.path.join(base_dir, "docs", image_file)
    
    video_path = await generate_avatar_video(image_path, audio_path)
    
    # 拷贝视频文件到指定目录
    sadtalker_out_dir = os.path.join(base_dir, "output", "SadTalker")
    os.makedirs(sadtalker_out_dir, exist_ok=True)
    if video_path and os.path.exists(video_path):
        import shutil
        shutil.copy(video_path, os.path.join(sadtalker_out_dir, f"video_{trace_id}.mp4"))
    
    # 如果视频生成成功，读取转为 Base64（实际生产中应返回视频 URL 或流地址以避免 Base64 过大，这里为了演示）
    video_base64 = ""
    if video_path and os.path.exists(video_path):
        with open(video_path, "rb") as vf:
            video_base64 = base64.b64encode(vf.read()).decode("utf-8")
            
    # 兜底：如果视频生成失败（比如 SadTalker 报错 ValueError(None)），返回纯音频 Base64 供前端播放
    audio_base64 = ""
    if not video_base64 and audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as af:
            audio_base64 = base64.b64encode(af.read()).decode("utf-8")
    
    return {
        "status": "success",
        "trace_id": trace_id,
        "doctor_reply": doctor_reply,
        "video_base64": video_base64,
        "audio_base64": audio_base64,
        "mime_type": "video/mp4",
        "twin_data": twin_data
    }

# =======================
# 1.5 纯语音+数字人视频生成接口 (绕过 LLM 和知识图谱)
# =======================
class GenerateVideoRequest(BaseModel):
    text: str = Field(..., description="要合成的文本")
    doctor_gender: str = Field("male", description="医生性别 ('male' 或 'female')")

@app.post("/api/v1/generate_video")
async def generate_video_only(req: GenerateVideoRequest):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received request to generate video for text: {req.text[:20]}...")
    
    # 1. 语音合成 (TTS)
    audio_path = generate_doctor_speech(req.text, req.doctor_gender)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 拷贝音频文件到指定目录
    chatter_box_out_dir = os.path.join(base_dir, "output", "chatter-box")
    os.makedirs(chatter_box_out_dir, exist_ok=True)
    if audio_path and os.path.exists(audio_path):
        import shutil
        shutil.copy(audio_path, os.path.join(chatter_box_out_dir, f"audio_{trace_id}.wav"))
    
    # 2. 生成唇形同步视频 (SadTalker)
    image_file = "3f38645a-9a34-4539-835e-a0138327f26d.jpg" if req.doctor_gender == "male" else "d970347c-8030-4035-ab24-f8c63e4a6e84.jpg"
    image_path = os.path.join(base_dir, "docs", image_file)
    
    video_path = await generate_avatar_video(image_path, audio_path)
    
    # 拷贝视频文件到指定目录
    sadtalker_out_dir = os.path.join(base_dir, "output", "SadTalker")
    os.makedirs(sadtalker_out_dir, exist_ok=True)
    if video_path and os.path.exists(video_path):
        import shutil
        shutil.copy(video_path, os.path.join(sadtalker_out_dir, f"video_{trace_id}.mp4"))
    
    video_base64 = ""
    if video_path and os.path.exists(video_path):
        with open(video_path, "rb") as vf:
            video_base64 = base64.b64encode(vf.read()).decode("utf-8")
            
    audio_base64 = ""
    if not video_base64 and audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as af:
            audio_base64 = base64.b64encode(af.read()).decode("utf-8")
            
    return {
        "status": "success",
        "trace_id": trace_id,
        "video_base64": video_base64,
        "audio_base64": audio_base64,
        "mime_type": "video/mp4"
    }

# =======================
# 2. 临床建议接口 (Clinical Suggestion)
# =======================
class ClinicalSuggestionRequest(BaseModel):
    prompt: str = Field(..., description="临床问题的详细描述", json_schema_extra={"example": "2型糖尿病，二甲双胍控制不佳，HbA1c 8.5%，下一步治疗方案推荐？"})
    use_rag: bool = Field(True, description="是否使用 RAG 增强检索指南")

class ClinicalSuggestionResponse(BaseModel):
    response: str = Field(..., description="大模型生成的临床建议")
    retrieved_knowledge: list = Field(default_factory=list, description="通过 RAG 检索到的参考指南/知识库")

@app.post("/clinical", response_model=ClinicalSuggestionResponse)
async def get_clinical_suggestion(req: ClinicalSuggestionRequest):
    result = generate_clinical_suggestion(req.prompt, req.use_rag)
    return ClinicalSuggestionResponse(
        response=result.get("response", ""),
        retrieved_knowledge=result.get("retrieved_knowledge", [])
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    # 确保当前目录在 sys.path 中，以便 worker 进程能找到 backend
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 支持 100 并发，单实例性能压测 (生产建议 Gunicorn 管理 workers)
    # 将 workers 改为 1，避免 Windows 下多进程导致的模块导入或 PyTorch 初始化问题
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8123, workers=1)
=======
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time
import logging
import uuid
import base64
import os

import sys
import os
import httpx
import asyncio
from gradio_client import Client

# 设定 HuggingFace 镜像源以加速国内访问
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 将项目根目录加入 sys.path，解决模块导入找不到 'backend' 的问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.llm_service import get_clinical_diagnosis, generate_clinical_suggestion
from backend.services.tts_service import generate_doctor_speech
from backend.services.avatar_service import generate_avatar_video
from neo4j import GraphDatabase

# 假定有 mock twin service 或直接模拟数据
def update_digital_twin(patient_id, text):
    kg_reasoning = []
    try:
        # 连接图谱数据库
        URI = "neo4j://192.168.0.214:7687"
        AUTH = ("neo4j", "tes12345")
        driver = GraphDatabase.driver(URI, auth=AUTH)
        with driver.session(database="neo4j") as session:
            # 1. 动态响应患者主诉症状
            if "头痛" in text or "头通" in text:
                kg_reasoning.append({
                    "type": "chronic_alert",
                    "data": ["主诉症状: 头痛", "图谱关联推演", "警惕：原发性高血压导致血压波动"]
                })
            elif "胸闷" in text:
                kg_reasoning.append({
                    "type": "chronic_alert",
                    "data": ["主诉症状: 胸闷", "图谱关联推演", "警惕：冠心病引发心肌缺血"]
                })

            # 2. 查询真实的并发症关联
            comp_query = """
            MATCH (d1:Disease)-[r:CAUSES]->(d2:Disease)
            RETURN d1.name AS source, r.risk_factor AS relation, d2.name AS target
            LIMIT 2
            """
            for record in session.run(comp_query):
                kg_reasoning.append({
                    "type": "chronic_alert", 
                    "data": [record["source"], record["relation"] or "导致并发", record["target"]]
                })
                
            # 3. 查询真实的治疗关联
            med_query = """
            MATCH (m:Medication)-[r:TREATS]->(d:Disease)
            RETURN d.name AS disease, r.evidence_level AS evidence, m.name AS med
            LIMIT 2
            """
            for record in session.run(med_query):
                kg_reasoning.append({
                    "type": "medication_alert", 
                    "data": [f"针对 {record['disease']}", f"证据等级 {record['evidence']} 推荐", record["med"]]
                })
    except Exception as e:
        print(f"Neo4j 图谱查询失败: {e}")
        # 如果 Neo4j 连接失败，则降级返回兜底数据
        kg_reasoning = [
            {"type": "chronic_alert", "data": ["2型糖尿病", "高血糖加速动脉硬化", "冠心病风险提升"]},
            {"type": "medication_alert", "data": ["二甲双胍控制不佳", "推荐 SGLT-2抑制剂", "降低心衰风险"]}
        ]

    return {
        "name": "老王",
        "risk_level": "高危",
        "fbg": 8.5,
        "sbp": 145,
        "kg_reasoning": kg_reasoning
    }

from logging.handlers import RotatingFileHandler

# 创建日志目录
os.makedirs("logs", exist_ok=True)

# 配置根日志记录器
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# 后端日志文件 (包含错误日志)
file_handler = RotatingFileHandler("logs/backend.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
file_handler.setFormatter(log_formatter)

# 设置基础 logging
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
logger = logging.getLogger(__name__)

# 为前端创建专门的日志记录器
frontend_logger = logging.getLogger("frontend")
frontend_handler = RotatingFileHandler("logs/frontend.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
frontend_handler.setFormatter(logging.Formatter('%(asctime)s - FRONTEND - %(levelname)s - %(message)s'))
frontend_logger.addHandler(frontend_handler)
frontend_logger.setLevel(logging.INFO)
frontend_logger.propagate = False

app = FastAPI(title="Digital Twin Doctor API", version="1.0.0")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon", status_code=204)

@app.get("/static/undefined", include_in_schema=False)
async def static_undefined():
    from fastapi.responses import Response
    return Response(content="", status_code=204)


# =======================
# 0. 前端日志接收接口
# =======================
class FrontendLog(BaseModel):
    level: str
    message: str
    url: str = ""
    line: int = 0
    col: int = 0
    error: str = ""

@app.post("/api/v1/log")
async def receive_frontend_log(log_data: FrontendLog):
    log_msg = f"URL: {log_data.url} | Line: {log_data.line}:{log_data.col} | Msg: {log_data.message} | Err: {log_data.error}"
    if log_data.level.lower() == "error":
        frontend_logger.error(log_msg)
    elif log_data.level.lower() == "warn":
        frontend_logger.warning(log_msg)
    else:
        frontend_logger.info(log_msg)
    return {"status": "logged"}

def verify_sadtalker_api(url: str):
    logger.info(f"✅ SadTalker API verification skipped to avoid heartbeat spam.")
    return True

@app.on_event("startup")
async def startup_event():
    logger.info("Verifying connections to external services...")
    sadtalker_url = "http://192.168.0.214:7860"
    
    # 检查 SadTalker 接口
    logger.info(f"Checking SadTalker API at {sadtalker_url} ...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(sadtalker_url)
            if response.status_code == 200:
                logger.info(f"✅ SadTalker API is reachable and healthy (200 OK).")
            else:
                logger.warning(f"⚠️ SadTalker API at {sadtalker_url} returned status code {response.status_code}.")
    except Exception as e:
        logger.error(f"❌ Failed to connect to SadTalker API at {sadtalker_url}. Error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
# 静态资源挂载用于访问图片和生成的视频
app.mount("/docs_images", StaticFiles(directory="docs"), name="docs_images")

# =======================
# 1. 核心对话流 (包含头像视频流)
# =======================
class InteractRequest(BaseModel):
    patient_id: str
    text: str
    doctor_gender: str = "male"  # 'male' 或 'female'
    use_rag: bool = True

@app.post("/api/v1/chat/interact")
async def chat_interaction(req: InteractRequest):
    trace_id = str(uuid.uuid4())
    
    # 1. 数字孪生状态计算
    twin_data = update_digital_twin(req.patient_id, req.text)
    
    # 2. 意图理解与医学知识检索 (LLM)
    llm_response = get_clinical_diagnosis(req.patient_id, req.text, twin_data)
    doctor_reply = llm_response.get("reply", "")
    
    # 3. 语音合成 (TTS) - 转换医疗文本的逻辑已内置于 generate_doctor_speech
    audio_path = generate_doctor_speech(doctor_reply, req.doctor_gender)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 拷贝音频文件到指定目录
    chatter_box_out_dir = os.path.join(base_dir, "output", "chatter-box")
    os.makedirs(chatter_box_out_dir, exist_ok=True)
    if audio_path and os.path.exists(audio_path):
        import shutil
        shutil.copy(audio_path, os.path.join(chatter_box_out_dir, f"audio_{trace_id}.wav"))
    
    # 4. 生成唇形同步视频 (SadTalker)
    image_file = "3f38645a-9a34-4539-835e-a0138327f26d.jpg" if req.doctor_gender == "male" else "d970347c-8030-4035-ab24-f8c63e4a6e84.jpg"
    image_path = os.path.join(base_dir, "docs", image_file)
    
    video_path = await generate_avatar_video(image_path, audio_path)
    
    # 拷贝视频文件到指定目录
    sadtalker_out_dir = os.path.join(base_dir, "output", "SadTalker")
    os.makedirs(sadtalker_out_dir, exist_ok=True)
    if video_path and os.path.exists(video_path):
        import shutil
        shutil.copy(video_path, os.path.join(sadtalker_out_dir, f"video_{trace_id}.mp4"))
    
    # 如果视频生成成功，读取转为 Base64（实际生产中应返回视频 URL 或流地址以避免 Base64 过大，这里为了演示）
    video_base64 = ""
    if video_path and os.path.exists(video_path):
        with open(video_path, "rb") as vf:
            video_base64 = base64.b64encode(vf.read()).decode("utf-8")
            
    # 兜底：如果视频生成失败（比如 SadTalker 报错 ValueError(None)），返回纯音频 Base64 供前端播放
    audio_base64 = ""
    if not video_base64 and audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as af:
            audio_base64 = base64.b64encode(af.read()).decode("utf-8")
    
    return {
        "status": "success",
        "trace_id": trace_id,
        "doctor_reply": doctor_reply,
        "video_base64": video_base64,
        "audio_base64": audio_base64,
        "mime_type": "video/mp4",
        "twin_data": twin_data
    }

# =======================
# 2. 临床建议接口 (Clinical Suggestion)
# =======================
class ClinicalSuggestionRequest(BaseModel):
    prompt: str = Field(..., description="临床问题的详细描述", json_schema_extra={"example": "2型糖尿病，二甲双胍控制不佳，HbA1c 8.5%，下一步治疗方案推荐？"})
    use_rag: bool = Field(True, description="是否使用 RAG 增强检索指南")

class ClinicalSuggestionResponse(BaseModel):
    response: str = Field(..., description="大模型生成的临床建议")
    retrieved_knowledge: list = Field(default_factory=list, description="通过 RAG 检索到的参考指南/知识库")

@app.post("/clinical", response_model=ClinicalSuggestionResponse)
async def get_clinical_suggestion(req: ClinicalSuggestionRequest):
    result = generate_clinical_suggestion(req.prompt, req.use_rag)
    return ClinicalSuggestionResponse(
        response=result.get("response", ""),
        retrieved_knowledge=result.get("retrieved_knowledge", [])
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    # 确保当前目录在 sys.path 中，以便 worker 进程能找到 backend
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 支持 100 并发，单实例性能压测 (生产建议 Gunicorn 管理 workers)
    # 将 workers 改为 1，避免 Windows 下多进程导致的模块导入或 PyTorch 初始化问题
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8123, workers=1)
>>>>>>> origin/main
