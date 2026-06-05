from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from visualizer import SpineVisualizer
import logging
import json

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisualizationService")

app = FastAPI(title="Spine Visualization Service", version="1.0.0")
visualizer = SpineVisualizer()

# --- Pydantic 模型 ---
class RenderRequest(BaseModel):
    patient_name: str
    timeline: List[Dict[str, Any]]
    treatment_plan: Dict[str, Any]
    
# --- 端点 ---

@app.post("/render/evolution")
def create_evolution_chart(request: RenderRequest):
    """
    生成 3D 脊柱演变图表。
    """
    import json # Ensure json is imported inside function scope if needed, or rely on top-level
    
    logger.info(f"正在为 {request.patient_name} 生成演变图表...")
    try:
        # 构造 visualizer 期望的 simulation_data 字典
        simulation_data = {
            "patient_name": request.patient_name,
            "timeline": request.timeline,
            "treatment_plan": request.treatment_plan
        }
        
        # 调用 visualizer 生成图表 (不再需要 is_intensive 参数，因为图表现在总是显示对比)
        fig = visualizer.create_evolution_chart(simulation_data)
        
        # 转换为 JSON 对象
        # Figure.to_json() 返回的是 JSON 字符串，我们需要将其解析为 Python 字典以便 FastAPI 序列化
        chart_json_str = fig.to_json()
        chart_dict = json.loads(chart_json_str)
        
        return {
            "data": chart_dict,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"可视化错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "visualization-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
