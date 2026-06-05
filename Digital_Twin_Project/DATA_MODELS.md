# 脊柱数字孪生 - 数据模型定义 (Data Models)

为了确保各微服务（Patient, Simulation, Visualization）之间能够顺畅地交换数据，我们定义了一套标准的 JSON 数据模型。这些模型将作为 API 的 Request/Response Body。

## 1. 核心实体 (Core Entities)

### 1.1 患者基本信息 (PatientProfile)
用于 **Patient Service**。

```json
{
  "id": "string (uuid)",
  "name": "string",
  "gender": "string (M/F)",
  "age": "integer",
  "diagnosis_date": "string (ISO8601 Date)",
  "medical_history": "string (optional)"
}
```

### 1.2 脊柱度量指标 (SpineMetrics)
用于描述脊柱当前的几何状态。这是 **Simulation Service** 的主要输入。

```json
{
  "patient_id": "string (uuid)",
  "timestamp": "string (ISO8601 DateTime)",
  
  // 关键临床指标
  "cobb_angle_main": "float (degrees)",
  "kyphosis_max": "float (degrees)",
  "lordosis_max": "float (degrees)",
  
  // 详细椎体旋转数据 (T1-L5)
  "vertebral_rotation": [
    0.0, 2.5, 5.0, ... // List of floats
  ],
  
  // 冠状面偏移量 (用于 3D 重建)
  "coronal_offsets": [
    0.0, 1.2, ... // List of floats
  ]
}
```

### 1.3 治疗方案 (TreatmentPlan)
用于配置模拟参数。

```json
{
  "plan_id": "string (uuid)",
  "type": "string (enum: Brace, PT, Intensive, Surgery, Observation)",
  
  // 方案参数
  "duration_weeks": "integer (default: 96)",
  "compliance_rate": "float (0.0 - 1.0)", // 依从性
  "intensity_level": "string (enum: Low, Medium, High)" // 针对 PT/Intensive
}
```

---

## 2. 模拟与预测 (Simulation & Prediction)

### 2.1 模拟请求 (SimulationRequest)
发送给 **Simulation Service**。

```json
{
  "initial_state": {
    "metrics": "SpineMetrics object",
    "curve_data": "CurveData object (internal representation)"
  },
  "treatment_plan": "TreatmentPlan object"
}
```

### 2.2 模拟结果 (SimulationResult)
**Simulation Service** 的输出，包含时间序列数据。

```json
{
  "simulation_id": "string (uuid)",
  "patient_id": "string",
  "plan_summary": "string",
  
  "timeline": [
    {
      "week": 0,
      "control_group": {
        "cobb_angle": 25.0,
        "kyphosis": 30.0,
        "rotation_max": 10.0
      },
      "intervention_group": {
        "cobb_angle": 25.0, // Week 0 starts same
        "kyphosis": 30.0,
        "rotation_max": 10.0
      }
    },
    {
      "week": 1,
      "control_group": { ... },
      "intervention_group": { ... }
    },
    ...
  ]
}
```

---

## 3. 可视化渲染 (Visualization)

### 3.1 渲染请求 (RenderRequest)
发送给 **Visualization Service**。

```json
{
  "patient_name": "string",
  "simulation_data": "SimulationResult object",
  "render_options": {
    "show_control_group": true,
    "show_intervention_group": true,
    "theme": "light/dark"
  }
}
```

### 3.2 渲染响应 (RenderResponse)
**Visualization Service** 返回的图表配置。

```json
{
  "chart_type": "string (plotly_json / html_snippet)",
  "data": "object (Plotly figure JSON)",
  "layout": "object (Plotly layout JSON)"
}
```
