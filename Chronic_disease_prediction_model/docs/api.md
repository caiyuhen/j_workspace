# 慢病风险预测 API 接口文档

## 1. 基本信息

- 基础地址：`http://<host>:5008`
- 数据格式：`application/json`
- 当前接口：
  - `GET /`：测试页面
  - `GET /health`：健康检查
  - `POST /api/predict`：慢病风险预测

## 2. 健康检查

### 请求

- 方法：`GET`
- 路径：`/health`

### 成功响应示例

```json
{
  "status": "healthy"
}
```

## 3. 风险预测

### 请求

- 方法：`POST`
- 路径：`/api/predict`
- Header：
  - `Content-Type: application/json`
  - `X-Model-Variant: A`（可选，默认 `A`）

### 请求体字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `records` | array<object> | 是 | 时序体检记录，建议同一患者至少7条连续记录 |
| `model_type` | string | 否 | 模型类型：`xgb_multi`（默认）或 `transformer` |
| `thresholds` | object | 否 | 自定义阈值，按病种覆盖默认值，如 `{ "stroke": [0.25, 0.4, 0.55] }` |

### `records` 单条记录字段

每条记录需包含以下核心字段：

- 身份与时间：`patient_id`、`exam_date`
- 静态特征：`age`、`gender`、`ethnicity`、`education_years`、`socioeconomic_score`、`atrial_fibrillation`、`previous_stroke`、`previous_tia`、`heart_disease`、`diabetes_years`、`hypertension_years`、`hypertension_controlled`、`chronic_kidney_disease`、`peripheral_artery_disease`、`family_stroke_history`、`family_heart_disease`、`genetic_risk_score`、`carotid_plaque`、`white_matter_lesions`
- 动态特征：`systolic_bp`、`diastolic_bp`、`total_cholesterol`、`hdl_cholesterol`、`ldl_cholesterol`、`triglycerides`、`fasting_glucose`、`hba1c`、`bmi`、`waist_circumference`、`waist_hip_ratio`、`heart_rate`、`alcohol_units_week`、`physical_activity_days`、`mediterranean_diet_score`、`sleep_hours`、`crp`、`fibrinogen`、`left_ventricular_ejection`、`avg_systolic_bp_24h`、`bp_variability`、`heart_rate_variability`、`daily_steps`、`sleep_efficiency`、`air_quality`、`season`

### 请求示例

```json
{
  "model_type": "xgb_multi",
  "records": [
    {
      "patient_id": "P_TEST_001",
      "exam_date": "2026-03-18",
      "age": 56,
      "gender": 1,
      "ethnicity": 1,
      "education_years": 12,
      "socioeconomic_score": 6,
      "atrial_fibrillation": 0,
      "previous_stroke": 0,
      "previous_tia": 0,
      "heart_disease": 0,
      "diabetes_years": 3,
      "hypertension_years": 5,
      "hypertension_controlled": 1,
      "chronic_kidney_disease": 0,
      "peripheral_artery_disease": 0,
      "family_stroke_history": 1,
      "family_heart_disease": 1,
      "genetic_risk_score": 5,
      "carotid_plaque": 0,
      "white_matter_lesions": 0,
      "systolic_bp": 132,
      "diastolic_bp": 82,
      "total_cholesterol": 192,
      "hdl_cholesterol": 48,
      "ldl_cholesterol": 118,
      "triglycerides": 150,
      "fasting_glucose": 107,
      "hba1c": 6.1,
      "bmi": 26.2,
      "waist_circumference": 92,
      "waist_hip_ratio": 0.93,
      "heart_rate": 74,
      "alcohol_units_week": 2,
      "physical_activity_days": 4,
      "mediterranean_diet_score": 8,
      "sleep_hours": 7,
      "crp": 1.7,
      "fibrinogen": 320,
      "left_ventricular_ejection": 60,
      "avg_systolic_bp_24h": 128,
      "bp_variability": 9,
      "heart_rate_variability": 28,
      "daily_steps": 7800,
      "sleep_efficiency": 83,
      "air_quality": 56,
      "season": 1
    }
  ]
}
```

### 成功响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `success` | boolean | 是否成功 |
| `predictions` | object | 各病种预测结果 |
| `top_factors` | array<object> | 每个病种Top特征 |
| `model_variant` | string | 使用的模型版本（A/B） |
| `model_type` | string | 使用的模型类型 |

`predictions.<disease>` 子字段：

- `risk_7d`：7天风险概率
- `risk_30d`：30天风险概率
- `risk_level_7d`：7天风险等级（低风险/中风险/高风险/极高风险）
- `risk_level_30d`：30天风险等级
- `thresholds`：当前病种阈值 `(low, mid, high)`
- `recommendations_7d`：7天风险建议
- `recommendations_30d`：30天风险建议

### 成功响应示例

```json
{
  "success": true,
  "predictions": {
    "stroke": {
      "risk_7d": 0.21,
      "risk_30d": 0.33,
      "risk_level_7d": "低风险",
      "risk_level_30d": "中风险",
      "thresholds": [0.3, 0.45, 0.6],
      "recommendations_7d": ["保持健康生活方式", "定期体检与监测"],
      "recommendations_30d": ["加强生活方式干预", "增加关键指标监测频率"]
    }
  },
  "top_factors": [
    {
      "disease": "stroke",
      "factors": ["num__systolic_bp_mean_7d", "num__hba1c_mean_7d"]
    }
  ],
  "model_variant": "A",
  "model_type": "xgb_multi"
}
```

## 4. 错误响应

### 4.1 缺少 records

- HTTP：`400`

```json
{
  "success": false,
  "error": "records_missing"
}
```

### 4.2 模型文件不存在

- HTTP：`500`

```json
{
  "success": false,
  "error": "model_not_found",
  "message": "[Errno 2] No such file or directory: 'models/xgb_multi_7d_A.joblib'",
  "hint": "请先训练并导出模型到 models 目录，例如运行 scripts/train.py"
}
```

### 4.3 预测失败

- HTTP：`500`

```json
{
  "success": false,
  "error": "predict_failed",
  "message": "..."
}
```

## 5. 调用示例

```bash
curl -X POST "http://127.0.0.1:5008/api/predict" \
  -H "Content-Type: application/json" \
  -H "X-Model-Variant: A" \
  -d @request.json
```

## 6. 注意事项

- `X-Model-Variant` 默认是 `A`，可切换到 `B`。
- 若 `model_type=transformer`，需存在 `models/transformer_7d_A.pt` 与 `models/transformer_30d_A.pt`。
- 若 `model_type=xgb_multi`，需存在 `models/xgb_multi_7d_A.joblib` 与 `models/xgb_multi_30d_A.joblib`。
- 风险等级由阈值控制，默认每病种阈值为 `(0.3, 0.45, 0.6)`，可通过 `thresholds` 自定义覆盖。
