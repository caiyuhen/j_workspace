import json
import re
import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("PatientParser")

class PatientParser:
    @staticmethod
    def parse(ocr_data: Dict[str, Any], patient_name: str) -> Dict[str, Any]:
        """
        将原始 OCR 数据解析为结构化患者对象。
        """
        # 处理可能的嵌套结构
        if isinstance(ocr_data, dict) and "extracted_data" in ocr_data:
            ocr_data = ocr_data["extracted_data"]
            
        raw_text = ocr_data.get("raw_text", "")
        
        # 1. 提取基本信息（如果 OCR 文本中有）
        # 尝试从文本中提取姓名
        name_match = re.search(r"姓名[:：]\s*(\S+)", raw_text)
        if name_match:
            extracted_name = name_match.group(1).strip()
            # 如果提取到的名字看起来合理（不是太长），则使用它
            if extracted_name and len(extracted_name) < 20:
                patient_name = extracted_name
        
        # 2. 解析 Cobb 角和测量值
        cobb_angle = PatientParser._extract_cobb_angle(raw_text)
        
        # 3. 构造脊柱参数
        spine_params = PatientParser._generate_spine_params(cobb_angle)
        
        # 确保 metrics 中的字段完整
        metrics = {
            "cobb_angle": cobb_angle,
            "kyphosis_max": 40.0,
            "lordosis_max": 30.0
        }
        
        # 确保 curve_data 中的字段完整且为列表
        curve_data = {
            "vertebral_rotation": spine_params["vertebral_rotation"],
            "coronal_offsets": spine_params["coronal_offset"], # 注意：这里 simulation 用的是 coronal_offsets (复数)
            "sagittal_profile": spine_params["sagittal_profile"]
        }
        
        return {
            "id": f"PAT-{int(time.time())}",
            "name": patient_name,
            "age": 14, # 默认/占位符
            "gender": "Female", # 默认/占位符
            "diagnosis": f"Scoliosis (Cobb {cobb_angle}°)",
            "spine_params": spine_params,
            "cobb_angle": cobb_angle,
            "metrics": metrics,
            "curve_data": curve_data
        }

    @staticmethod
    def _extract_cobb_angle(text: str) -> float:
        """
        尝试使用正则表达式从文本中查找 Cobb 角。
        """
        # 查找类似 "Cobb角: 25" 或 "Cobb Angle 25" 的模式
        # 更新：查找度数符号或“度”
        match = re.search(r"Cobb.*?(\d+)[°d度]", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        # 备用：查找任何后跟度的数字，这可能有风险
        match = re.search(r"(\d+)[°度]", text)
        if match:
             return float(match.group(1))

        return 20.0 # 默认值，如果未找到

    @staticmethod
    def _generate_spine_params(cobb_angle: float) -> Dict[str, Any]:
        """
        根据 Cobb 角生成脊柱参数。
        在真实系统中，这将解析每个椎骨的测量值。
        """
        # 确保我们有用于可视化的列表数据
        # 默认 17 个椎骨 (T1-L5)
        num_vertebrae = 17 
        
        # 创建默认数组以避免“max() iterable argument is empty”错误
        # 即使我们只有单个值，可视化服务也可能期待数组
        
        # 模拟曲率：简单的正弦波受 Cobb 角影响
        import math
        # 简单的 S 形曲线
        curve_data = [math.sin(i/num_vertebrae * math.pi * 2) * (cobb_angle/2) for i in range(num_vertebrae)]
        
        return {
            "vertebral_rotation": curve_data, # 占位符列表
            "coronal_offset": [x * 0.5 for x in curve_data], # 占位符列表
            "sagittal_profile": [10.0] * num_vertebrae, # 默认后凸/前凸
            "flexibility": 0.8 # 刚度系数
        }
