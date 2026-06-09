<<<<<<< HEAD
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import os

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReportGateway")

app = FastAPI(title="Spine Report Gateway", version="1.0.0")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 服务 URL (可通过环境变量配置)
PATIENT_SERVICE_URL = os.getenv("PATIENT_SERVICE_URL", "http://127.0.0.1:8003")
SIMULATION_SERVICE_URL = os.getenv("SIMULATION_SERVICE_URL", "http://127.0.0.1:8001")
VISUALIZATION_SERVICE_URL = os.getenv("VISUALIZATION_SERVICE_URL", "http://127.0.0.1:8002")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://127.0.0.1:8004")

# --- Pydantic 模型 ---
class TreatmentPlan(BaseModel):
    type: str = "Brace"
    duration: int = 24
    compliance: float = 0.8

class ReportRequest(BaseModel):
    patient_name: str
    treatment_plan: TreatmentPlan

class ReportResponse(BaseModel):
    patient_id: str
    simulation_id: str
    evolution_chart_json: Dict[str, Any]
    summary: str
    comparison_data: Optional[Dict[str, Any]] = None

# --- 端点 ---

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/patients")
async def list_patients():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{PATIENT_SERVICE_URL}/patients")
            resp.raise_for_status() # 抛出 HTTP 异常
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch patients: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    async with httpx.AsyncClient() as client:
        try:
            # 如果可能，我们使用 gather 并发运行检查，但为了错误处理，顺序执行更安全
            services = {}
            
            try:
                services["patient"] = (await client.get(f"{PATIENT_SERVICE_URL}/health")).json()
            except Exception as e:
                services["patient"] = {"status": "down", "error": str(e)}
                
            try:
                services["simulation"] = (await client.get(f"{SIMULATION_SERVICE_URL}/health")).json()
            except Exception as e:
                services["simulation"] = {"status": "down", "error": str(e)}
                
            try:
                services["visualization"] = (await client.get(f"{VISUALIZATION_SERVICE_URL}/health")).json()
            except Exception as e:
                services["visualization"] = {"status": "down", "error": str(e)}
                
            try:
                services["ocr"] = (await client.get(f"{OCR_SERVICE_URL}/health")).json()
            except Exception as e:
                services["ocr"] = {"status": "down", "error": str(e)}

            return {
                "status": "active",
                "services": services
            }
        except Exception as e:
             return {"status": "degraded", "error": str(e)}

@app.post("/upload/ocr")
async def upload_ocr(file: UploadFile = File(...)):
    """
    上传 PDF 文件，通过 OCR 服务提取文本，保存提取结果，
    并触发患者服务重新加载数据。
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
        
    # 增加 OCR 处理的超时时间（可能需要 10-30 秒）
    timeout = httpx.Timeout(60.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # 1. 转发到 OCR 服务
            # 我们需要读取文件内容以转发它
            file_content = await file.read()
            files = {
                'file': (file.filename, file_content, 'application/pdf')
            }
            data = {'save_json': 'true'}
            
            logger.info(f"正在将 {file.filename} 转发到 OCR 服务 {OCR_SERVICE_URL}/ocr/extract ...")
            ocr_resp = await client.post(f"{OCR_SERVICE_URL}/ocr/extract", files=files, data=data)
            
            if ocr_resp.status_code != 200:
                raise HTTPException(status_code=ocr_resp.status_code, detail=f"OCR 服务失败: {ocr_resp.text}")
            
            result = ocr_resp.json()
            
            # 2. 触发患者服务重新加载
            logger.info("正在触发患者服务重新加载...")
            try:
                await client.post(f"{PATIENT_SERVICE_URL}/reload")
            except Exception as e:
                logger.warning(f"无法重新加载患者服务: {e}")
                # 如果重新加载失败，不要让整个请求失败，只是警告
            
            return {
                "message": "文件已处理且患者数据已更新",
                "ocr_result": result
            }
            
        except httpx.RequestError as e:
            logger.error(f"与 OCR 的服务通信错误: {repr(e)}")
            raise HTTPException(status_code=503, detail=f"服务通信错误: {repr(e)}")
        except Exception as e:
            logger.error(f"上传失败: {e}")
            raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/report/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1. 获取患者数据
        try:
            logger.info(f"正在获取 {request.patient_name} 的数据...")
            p_resp = await client.get(f"{PATIENT_SERVICE_URL}/patients/{request.patient_name}")
            p_resp.raise_for_status()
            patient_data = p_resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=404, detail=f"未找到患者: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"患者服务错误: {e}")

        # 2. 运行模拟
        try:
            logger.info(f"正在为 {request.patient_name} 运行模拟...")
            sim_payload = {
                "patient_name": request.patient_name,
                "initial_state": {
                    "metrics": patient_data['metrics'],
                    "curve_data": patient_data['curve_data']
                },
                "treatment_plan": request.treatment_plan.dict()
            }
            s_resp = await client.post(f"{SIMULATION_SERVICE_URL}/simulate", json=sim_payload)
            s_resp.raise_for_status()
            simulation_result = s_resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"模拟服务错误: {e}")

        # 3. 生成可视化
        try:
            logger.info(f"正在为 {request.patient_name} 生成可视化...")
            # 模拟结果结构与可视化工具期望的匹配（时间轴 + 患者姓名 + 计划）
            v_resp = await client.post(f"{VISUALIZATION_SERVICE_URL}/render/evolution", json=simulation_result)
            v_resp.raise_for_status()
            visualization_result = v_resp.json()
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=504, detail=f"可视化服务超时: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"可视化服务错误: {e}")

        # 4. 构建最终报告
        
        # 提取关键对比数据
        timeline = simulation_result.get('timeline', [])
        comparison = {}
        if timeline:
            final_state = timeline[-1]
            initial_state = timeline[0]
            
            # Cobb Angle Comparison
            comparison['initial_cobb'] = initial_state.get('control', {}).get('metrics', {}).get('cobb_angle', 0)
            comparison['final_control'] = final_state.get('control', {}).get('metrics', {}).get('cobb_angle', 0)
            comparison['final_intervention'] = final_state.get('intervention', {}).get('metrics', {}).get('cobb_angle', 0)
            
            # Safe access for intensive
            intensive_metrics = final_state.get('intensive', {}).get('metrics')
            if not intensive_metrics:
                 intensive_metrics = final_state['intervention']['metrics']
            comparison['final_intensive'] = intensive_metrics.get('cobb_angle', 0)
            
            # Improvement calculation (relative to initial)
            comparison['improvement_intervention'] = comparison['initial_cobb'] - comparison['final_intervention']
            comparison['improvement_intensive'] = comparison['initial_cobb'] - comparison['final_intensive']
            
        return {
            "patient_id": patient_data['id'],
            "simulation_id": f"sim-{abs(hash(request.patient_name))}",
            "evolution_chart_json": visualization_result['data'],
            "summary": f"为 {request.patient_name} 生成的报告，治疗方案为 {request.treatment_plan.type}。",
            "comparison_data": comparison
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
=======
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import os

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReportGateway")

app = FastAPI(title="Spine Report Gateway", version="1.0.0")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 服务 URL (可通过环境变量配置)
PATIENT_SERVICE_URL = os.getenv("PATIENT_SERVICE_URL", "http://127.0.0.1:8003")
SIMULATION_SERVICE_URL = os.getenv("SIMULATION_SERVICE_URL", "http://127.0.0.1:8001")
VISUALIZATION_SERVICE_URL = os.getenv("VISUALIZATION_SERVICE_URL", "http://127.0.0.1:8002")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://127.0.0.1:8004")

# --- Pydantic 模型 ---
class TreatmentPlan(BaseModel):
    type: str = "Brace"
    duration: int = 24
    compliance: float = 0.8

class ReportRequest(BaseModel):
    patient_name: str
    treatment_plan: TreatmentPlan

class ReportResponse(BaseModel):
    patient_id: str
    simulation_id: str
    evolution_chart_json: Dict[str, Any]
    summary: str
    comparison_data: Optional[Dict[str, Any]] = None

# --- 端点 ---

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/patients")
async def list_patients():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{PATIENT_SERVICE_URL}/patients")
            resp.raise_for_status() # 抛出 HTTP 异常
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch patients: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    async with httpx.AsyncClient() as client:
        try:
            # 如果可能，我们使用 gather 并发运行检查，但为了错误处理，顺序执行更安全
            services = {}
            
            try:
                services["patient"] = (await client.get(f"{PATIENT_SERVICE_URL}/health")).json()
            except Exception as e:
                services["patient"] = {"status": "down", "error": str(e)}
                
            try:
                services["simulation"] = (await client.get(f"{SIMULATION_SERVICE_URL}/health")).json()
            except Exception as e:
                services["simulation"] = {"status": "down", "error": str(e)}
                
            try:
                services["visualization"] = (await client.get(f"{VISUALIZATION_SERVICE_URL}/health")).json()
            except Exception as e:
                services["visualization"] = {"status": "down", "error": str(e)}
                
            try:
                services["ocr"] = (await client.get(f"{OCR_SERVICE_URL}/health")).json()
            except Exception as e:
                services["ocr"] = {"status": "down", "error": str(e)}

            return {
                "status": "active",
                "services": services
            }
        except Exception as e:
             return {"status": "degraded", "error": str(e)}

@app.post("/upload/ocr")
async def upload_ocr(file: UploadFile = File(...)):
    """
    上传 PDF 文件，通过 OCR 服务提取文本，保存提取结果，
    并触发患者服务重新加载数据。
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
        
    # 增加 OCR 处理的超时时间（可能需要 10-30 秒）
    timeout = httpx.Timeout(60.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # 1. 转发到 OCR 服务
            # 我们需要读取文件内容以转发它
            file_content = await file.read()
            files = {
                'file': (file.filename, file_content, 'application/pdf')
            }
            data = {'save_json': 'true'}
            
            logger.info(f"正在将 {file.filename} 转发到 OCR 服务 {OCR_SERVICE_URL}/ocr/extract ...")
            ocr_resp = await client.post(f"{OCR_SERVICE_URL}/ocr/extract", files=files, data=data)
            
            if ocr_resp.status_code != 200:
                raise HTTPException(status_code=ocr_resp.status_code, detail=f"OCR 服务失败: {ocr_resp.text}")
            
            result = ocr_resp.json()
            
            # 2. 触发患者服务重新加载
            logger.info("正在触发患者服务重新加载...")
            try:
                await client.post(f"{PATIENT_SERVICE_URL}/reload")
            except Exception as e:
                logger.warning(f"无法重新加载患者服务: {e}")
                # 如果重新加载失败，不要让整个请求失败，只是警告
            
            return {
                "message": "文件已处理且患者数据已更新",
                "ocr_result": result
            }
            
        except httpx.RequestError as e:
            logger.error(f"与 OCR 的服务通信错误: {repr(e)}")
            raise HTTPException(status_code=503, detail=f"服务通信错误: {repr(e)}")
        except Exception as e:
            logger.error(f"上传失败: {e}")
            raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/report/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1. 获取患者数据
        try:
            logger.info(f"正在获取 {request.patient_name} 的数据...")
            p_resp = await client.get(f"{PATIENT_SERVICE_URL}/patients/{request.patient_name}")
            p_resp.raise_for_status()
            patient_data = p_resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=404, detail=f"未找到患者: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"患者服务错误: {e}")

        # 2. 运行模拟
        try:
            logger.info(f"正在为 {request.patient_name} 运行模拟...")
            sim_payload = {
                "patient_name": request.patient_name,
                "initial_state": {
                    "metrics": patient_data['metrics'],
                    "curve_data": patient_data['curve_data']
                },
                "treatment_plan": request.treatment_plan.dict()
            }
            s_resp = await client.post(f"{SIMULATION_SERVICE_URL}/simulate", json=sim_payload)
            s_resp.raise_for_status()
            simulation_result = s_resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"模拟服务错误: {e}")

        # 3. 生成可视化
        try:
            logger.info(f"正在为 {request.patient_name} 生成可视化...")
            # 模拟结果结构与可视化工具期望的匹配（时间轴 + 患者姓名 + 计划）
            v_resp = await client.post(f"{VISUALIZATION_SERVICE_URL}/render/evolution", json=simulation_result)
            v_resp.raise_for_status()
            visualization_result = v_resp.json()
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=504, detail=f"可视化服务超时: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"可视化服务错误: {e}")

        # 4. 构建最终报告
        
        # 提取关键对比数据
        timeline = simulation_result.get('timeline', [])
        comparison = {}
        if timeline:
            final_state = timeline[-1]
            initial_state = timeline[0]
            
            # Cobb Angle Comparison
            comparison['initial_cobb'] = initial_state.get('control', {}).get('metrics', {}).get('cobb_angle', 0)
            comparison['final_control'] = final_state.get('control', {}).get('metrics', {}).get('cobb_angle', 0)
            comparison['final_intervention'] = final_state.get('intervention', {}).get('metrics', {}).get('cobb_angle', 0)
            
            # Safe access for intensive
            intensive_metrics = final_state.get('intensive', {}).get('metrics')
            if not intensive_metrics:
                 intensive_metrics = final_state['intervention']['metrics']
            comparison['final_intensive'] = intensive_metrics.get('cobb_angle', 0)
            
            # Improvement calculation (relative to initial)
            comparison['improvement_intervention'] = comparison['initial_cobb'] - comparison['final_intervention']
            comparison['improvement_intensive'] = comparison['initial_cobb'] - comparison['final_intensive']
            
        return {
            "patient_id": patient_data['id'],
            "simulation_id": f"sim-{abs(hash(request.patient_name))}",
            "evolution_chart_json": visualization_result['data'],
            "summary": f"为 {request.patient_name} 生成的报告，治疗方案为 {request.treatment_plan.type}。",
            "comparison_data": comparison
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
