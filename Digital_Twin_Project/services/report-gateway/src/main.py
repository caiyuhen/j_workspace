<<<<<<< HEAD
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
CURRENT_DIR = Path(__file__).resolve().parent
STATIC_DIR = CURRENT_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 服务 URL (可通过环境变量配置)
PATIENT_SERVICE_URL = os.getenv("PATIENT_SERVICE_URL", "http://127.0.0.1:9003")
SIMULATION_SERVICE_URL = os.getenv("SIMULATION_SERVICE_URL", "http://127.0.0.1:9001")
VISUALIZATION_SERVICE_URL = os.getenv("VISUALIZATION_SERVICE_URL", "http://127.0.0.1:9002")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://127.0.0.1:9004")
XRAY_SERVICE_URL = os.getenv("XRAY_SERVICE_URL", "http://127.0.0.1:9005")

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
    return FileResponse(str(STATIC_DIR / "index.html"))


def build_simulation_payload(patient_state: Dict[str, Any], treatment_plan: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "patient_name": patient_state["name"],
        "initial_state": {
            "metrics": patient_state["metrics"],
            "curve_data": patient_state["curve_data"],
        },
        "treatment_plan": treatment_plan,
    }


def fuse_patient_states(pdf_state: Dict[str, Any], xray_state: Dict[str, Any], explicit_name: Optional[str]) -> Dict[str, Any]:
    pdf_metrics = pdf_state.get("metrics", {})
    xray_metrics = xray_state.get("metrics", {})
    pdf_cobb = pdf_metrics.get("cobb_angle")
    xray_cobb = xray_metrics.get("cobb_angle")
    has_conflict = pdf_cobb is not None and xray_cobb is not None and abs(pdf_cobb - xray_cobb) > 8.0
    fused_cobb = xray_cobb if xray_cobb is not None else pdf_cobb
    if pdf_cobb is not None and xray_cobb is not None:
        fused_cobb = round((pdf_cobb + xray_cobb) / 2.0, 1)

    return {
        "name": explicit_name or pdf_state.get("name") or xray_state.get("name") or "匿名患者",
        "data_source": "fused",
        "metrics": {
            "cobb_angle": fused_cobb or 20.0,
            "kyphosis_max": xray_metrics.get("kyphosis_max", pdf_metrics.get("kyphosis_max", 40.0)),
            "lordosis_max": xray_metrics.get("lordosis_max", pdf_metrics.get("lordosis_max", 30.0)),
        },
        "curve_data": xray_state.get("curve_data") or pdf_state.get("curve_data"),
        "confidence": {
            "cobb_angle": xray_state.get("confidence", {}).get("cobb_angle", 0.5),
        },
        "image_quality_score": xray_state.get("image_quality_score", 0.0),
        "analysis_meta": xray_state.get("analysis_meta", {}),
        "review_required": has_conflict or xray_state.get("review_required", False),
    }


async def call_visualization(client: httpx.AsyncClient, simulation_result: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.post(f"{VISUALIZATION_SERVICE_URL}/render/evolution", json=simulation_result)
    response.raise_for_status()
    return response.json()


async def call_xray_service(client: httpx.AsyncClient, upload: UploadFile, patient_name: Optional[str]) -> Dict[str, Any]:
    content = await upload.read()
    files = {
        "file": (upload.filename, content, upload.content_type or "application/octet-stream"),
    }
    data = {}
    if patient_name:
        data["patient_name"] = patient_name
    response = await client.post(f"{XRAY_SERVICE_URL}/xray/analyze", files=files, data=data)
    response.raise_for_status()
    return response.json()


async def call_ocr_service(client: httpx.AsyncClient, upload: UploadFile) -> Dict[str, Any]:
    content = await upload.read()
    files = {"file": (upload.filename, content, "application/pdf")}
    response = await client.post(f"{OCR_SERVICE_URL}/ocr/extract", files=files, data={"save_json": "false"})
    response.raise_for_status()
    return response.json()


def build_pdf_patient_state(ocr_result: Dict[str, Any], explicit_name: Optional[str]) -> Dict[str, Any]:
    extracted = ocr_result.get("extracted_data", {})
    raw_text = extracted.get("raw_text", "")
    filename = extracted.get("filename", "PDF患者.pdf")
    name = explicit_name or filename.replace(".pdf", "")
    cobb = 20.0
    for line in raw_text.splitlines():
        if "cobb" in line.lower():
            digits = "".join(ch for ch in line if ch.isdigit() or ch == ".")
            if digits:
                cobb = float(digits)
                break
    return {
        "name": name,
        "data_source": "pdf",
        "metrics": {
            "cobb_angle": cobb,
            "kyphosis_max": 40.0,
            "lordosis_max": 30.0,
        },
        "curve_data": {
            "vertebral_rotation": [1.0] * 17,
            "coronal_offsets": [0.0] * 17,
            "sagittal_profile": [10.0] * 17,
        },
        "confidence": {"cobb_angle": 0.5},
        "review_required": False,
    }


async def run_pipeline_from_patient_state(
    client: httpx.AsyncClient,
    workflow_type: str,
    patient_state: Dict[str, Any],
    treatment_plan: Dict[str, Any],
) -> Dict[str, Any]:
    sim_payload = build_simulation_payload(patient_state, treatment_plan)
    sim_resp = await client.post(f"{SIMULATION_SERVICE_URL}/simulate", json=sim_payload)
    sim_resp.raise_for_status()
    simulation_result = sim_resp.json()
    visualization_result = await call_visualization(client, simulation_result)
    return {
        "workflow_type": workflow_type,
        "patient_state": patient_state,
        "simulation_id": f"sim-{abs(hash(patient_state['name']))}",
        "evolution_chart_json": visualization_result["data"],
        "comparison_data": simulation_result.get("comparison_data", {}),
        "summary": f"已完成 {workflow_type} 工作流分析",
        "review_required": patient_state.get("review_required", False),
    }

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


@app.post("/workflow/analyze")
async def workflow_analyze(
    workflow_type: str = Form(...),
    treatment_type: str = Form("Brace"),
    duration: int = Form(24),
    compliance: float = Form(0.8),
    patient_name: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    xray_file: Optional[UploadFile] = File(None),
):
    treatment_plan = {
        "type": treatment_type,
        "duration": duration,
        "compliance": compliance,
    }
    if workflow_type == "pdf_only" and pdf_file is None:
        raise HTTPException(status_code=400, detail="PDF-only 工作流必须上传 PDF")
    if workflow_type == "xray_only" and xray_file is None:
        raise HTTPException(status_code=400, detail="X光-only 工作流必须上传 X光文件")
    if workflow_type == "multimodal" and (pdf_file is None or xray_file is None):
        raise HTTPException(status_code=400, detail="联合工作流必须同时上传 PDF 和 X光文件")
    if workflow_type not in {"pdf_only", "xray_only", "multimodal"}:
        raise HTTPException(status_code=400, detail="不支持的 workflow_type")

    if workflow_type == "xray_only":
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                xray_result = await call_xray_service(client, xray_file, patient_name)
                patient_state = xray_result["patient_state"]
                return await run_pipeline_from_patient_state(client, workflow_type, patient_state, treatment_plan)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"X光工作流调用失败: {exc}") from exc

    if workflow_type == "pdf_only":
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                ocr_result = await call_ocr_service(client, pdf_file)
                patient_state = build_pdf_patient_state(ocr_result, patient_name)
                return await run_pipeline_from_patient_state(client, workflow_type, patient_state, treatment_plan)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"PDF工作流调用失败: {exc}") from exc

    if workflow_type == "multimodal":
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                ocr_result = await call_ocr_service(client, pdf_file)
                pdf_state = build_pdf_patient_state(ocr_result, patient_name)
                xray_result = await call_xray_service(client, xray_file, patient_name)
                patient_state = fuse_patient_states(pdf_state, xray_result["patient_state"], patient_name)
                return await run_pipeline_from_patient_state(client, workflow_type, patient_state, treatment_plan)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"联合工作流调用失败: {exc}") from exc

    raise HTTPException(status_code=501, detail="后续步骤实现真实编排")

@app.post("/workflow/compare")
async def workflow_compare(
    source_type: str = Form(...),
    duration: int = Form(24),
    compliance: float = Form(0.8),
    patient_name: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    xray_file: Optional[UploadFile] = File(None),
):
    """
    针对同一患者（新上传或已有），自动运行所有 4 种治疗方案（Brace, PT, Intensive, Surgery），
    返回它们的演变对比结果。
    """
    if source_type == "pdf_only" and pdf_file is None:
        raise HTTPException(status_code=400, detail="PDF-only 工作流必须上传 PDF")
    if source_type == "xray_only" and xray_file is None:
        raise HTTPException(status_code=400, detail="X光-only 工作流必须上传 X光文件")
    if source_type == "multimodal" and (pdf_file is None or xray_file is None):
        raise HTTPException(status_code=400, detail="联合工作流必须同时上传 PDF 和 X光文件")
    if source_type == "existing" and not patient_name:
        raise HTTPException(status_code=400, detail="选择已有患者时必须提供 patient_name")

    patient_state = None
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1. 解析 patient_state
        if source_type == "existing":
            try:
                p_resp = await client.get(f"{PATIENT_SERVICE_URL}/patients/{patient_name}")
                p_resp.raise_for_status()
                patient_data = p_resp.json()
                # 重建 patient_state 结构
                patient_state = {
                    "name": patient_name,
                    "data_source": "existing",
                    "metrics": patient_data["metrics"],
                    "curve_data": patient_data["curve_data"],
                    "review_required": False
                }
            except Exception as exc:
                raise HTTPException(status_code=404, detail=f"未找到患者数据或服务错误: {exc}")
        elif source_type == "xray_only":
            try:
                xray_result = await call_xray_service(client, xray_file, patient_name)
                patient_state = xray_result["patient_state"]
            except Exception as exc:
                raise HTTPException(status_code=502, detail=f"X光工作流调用失败: {exc}")
        elif source_type == "pdf_only":
            try:
                ocr_result = await call_ocr_service(client, pdf_file)
                patient_state = build_pdf_patient_state(ocr_result, patient_name)
            except Exception as exc:
                raise HTTPException(status_code=502, detail=f"PDF工作流调用失败: {exc}")
        elif source_type == "multimodal":
            try:
                ocr_result = await call_ocr_service(client, pdf_file)
                pdf_state = build_pdf_patient_state(ocr_result, patient_name)
                xray_result = await call_xray_service(client, xray_file, patient_name)
                patient_state = fuse_patient_states(pdf_state, xray_result["patient_state"], patient_name)
            except Exception as exc:
                raise HTTPException(status_code=502, detail=f"联合工作流调用失败: {exc}")
        else:
            raise HTTPException(status_code=400, detail="不支持的 source_type")

        # 2. 依次跑 4 种治疗方案的模拟
        treatments = ["Brace", "PT", "Intensive", "Surgery"]
        results_by_treatment = {}
        first_success_sim = None
        first_success_plan = None
        
        for t_type in treatments:
            t_plan = {"type": t_type, "duration": duration, "compliance": compliance}
            sim_payload = build_simulation_payload(patient_state, t_plan)
            try:
                sim_resp = await client.post(f"{SIMULATION_SERVICE_URL}/simulate", json=sim_payload)
                sim_resp.raise_for_status()
                sim_data = sim_resp.json()
                results_by_treatment[t_type] = {
                    "timeline": sim_data.get("timeline", []),
                    "comparison_data": sim_data.get("comparison_data", {})
                }
                if first_success_sim is None:
                    first_success_sim = sim_data
                    first_success_plan = t_plan
            except Exception as exc:
                logger.error(f"模拟治疗 {t_type} 失败: {exc}")
                results_by_treatment[t_type] = {"error": str(exc)}

        # 3. 为了显示 3D，生成一个基础图表（使用第一个成功的方案作为代表去渲染3D结构）
        evolution_chart_json = None
        if first_success_sim:
            try:
                v_payload = {
                    "patient_name": patient_state["name"],
                    "timeline": first_success_sim.get("timeline", []),
                    "treatment_plan": first_success_plan
                }
                v_resp = await client.post(f"{VISUALIZATION_SERVICE_URL}/render/evolution", json=v_payload)
                v_resp.raise_for_status()
                evolution_chart_json = v_resp.json().get("data")
            except Exception as exc:
                logger.error(f"对比模式生成 3D 失败: {exc}")

    return {
        "source_type": source_type,
        "patient_state": patient_state,
        "duration": duration,
        "compliance": compliance,
        "results_by_treatment": results_by_treatment,
        "evolution_chart_json": evolution_chart_json,
        "summary": f"已完成 {patient_state['name']} 的 4 种治疗方案对比模拟"
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
>>>>>>> origin/main
