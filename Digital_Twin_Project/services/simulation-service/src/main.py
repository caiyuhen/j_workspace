from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from engine import SimulationEngine
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimulationService")

app = FastAPI(title="Spine Treatment Simulation Service", version="1.0.0")
engine = SimulationEngine()

# --- Pydantic 模型 ---
class TreatmentPlan(BaseModel):
    type: str = "Brace" # 支具, 理疗 (PT), 强化训练 (Intensive), 手术 (Surgery)
    duration: int = 24 # 持续月数
    compliance: float = 0.8 # 依从性

class SpineMetrics(BaseModel):
    kyphosis_max: float
    lordosis_max: float
    # 根据需要添加其他字段

class CurveData(BaseModel):
    vertebral_rotation: List[float]
    coronal_offsets: Optional[List[float]] = None

class InitialState(BaseModel):
    metrics: Dict[str, Any]
    curve_data: Dict[str, Any]

class SimulationRequest(BaseModel):
    patient_name: str
    initial_state: InitialState
    treatment_plan: TreatmentPlan

# --- 端点 ---

@app.post("/simulate")
def run_simulation_endpoint(request: SimulationRequest):
    """
    根据当前状态和治疗方案运行脊柱演变模拟。
    """
    logger.info(f"收到模拟请求。治疗类型: {request.treatment_plan.type}")
    try:
        # 运行模拟引擎
        # 将 Pydantic 模型转换为字典传递给引擎
        initial_state_dict = {
            "metrics": request.initial_state.metrics,
            "curve_data": request.initial_state.curve_data
        }
        treatment_plan_dict = request.treatment_plan.dict()
        
        result = engine.run_simulation(
            request.patient_name,
            initial_state_dict,
            treatment_plan_dict
        )
        return result
    except Exception as e:
        logger.error(f"模拟错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "simulation-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
