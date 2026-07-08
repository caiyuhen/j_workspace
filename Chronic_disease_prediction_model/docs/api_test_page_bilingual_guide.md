# API测试页中英文对照说明 / Bilingual Guide for API Test Page

## 1. 适用范围 / Scope

- 本文档说明测试页中的“填充示例（请求体）”与“响应结果”字段含义。  
  This document explains the fields in the test page demo payload and response.
- 对应页面入口：`GET /`，核心接口：`POST /api/predict`。  
  Page entry: `GET /`, main endpoint: `POST /api/predict`.

## 2. 填充示例请求体 / Demo Request Payload

### 2.1 顶层字段 / Top-level Fields

| 字段（Field） | 类型（Type） | 中文说明 | English Description |
|---|---|---|---|
| `model_type` | string | 模型类型。测试页默认是 `xgb_multi`。可选 `transformer`。 | Model type. Default is `xgb_multi`. Optional `transformer`. |
| `records` | array<object> | 时序体检记录数组，至少需要满足模型窗口（默认7天序列）。 | Time-series exam records array; should satisfy model window (default 7-day sequence). |
| `thresholds` | object (optional) | 可选自定义风险阈值，按病种覆盖默认阈值。 | Optional custom risk thresholds by disease, overriding defaults. |

### 2.2 `records` 单条记录字段 / Single Record Fields

> 每条记录代表某位患者某天的检查值。  
> Each record represents one patient’s metrics on one exam date.

| 字段（Field） | 中文说明 | English Description |
|---|---|---|
| `patient_id` | 患者ID | Patient ID |
| `exam_date` | 检查日期（`YYYY-MM-DD`） | Exam date (`YYYY-MM-DD`) |
| `age` | 年龄 | Age |
| `gender` | 性别编码 | Gender code |
| `ethnicity` | 民族/人群编码 | Ethnicity code |
| `education_years` | 受教育年限 | Years of education |
| `socioeconomic_score` | 社会经济评分 | Socioeconomic score |
| `atrial_fibrillation` | 房颤标记 | Atrial fibrillation flag |
| `previous_stroke` | 既往卒中 | Previous stroke flag |
| `previous_tia` | 既往TIA | Previous TIA flag |
| `heart_disease` | 心脏病史 | Heart disease flag |
| `diabetes_years` | 糖尿病病程（年） | Diabetes duration (years) |
| `hypertension_years` | 高血压病程（年） | Hypertension duration (years) |
| `hypertension_controlled` | 血压是否控制 | Hypertension controlled flag |
| `chronic_kidney_disease` | 慢性肾病标记 | CKD flag |
| `peripheral_artery_disease` | 外周动脉病标记 | PAD flag |
| `family_stroke_history` | 家族卒中史 | Family stroke history |
| `family_heart_disease` | 家族心脏病史 | Family heart disease history |
| `genetic_risk_score` | 遗传风险评分 | Genetic risk score |
| `carotid_plaque` | 颈动脉斑块 | Carotid plaque flag |
| `white_matter_lesions` | 白质病变 | White matter lesion flag |
| `systolic_bp` | 收缩压 | Systolic blood pressure |
| `diastolic_bp` | 舒张压 | Diastolic blood pressure |
| `total_cholesterol` | 总胆固醇 | Total cholesterol |
| `hdl_cholesterol` | HDL胆固醇 | HDL cholesterol |
| `ldl_cholesterol` | LDL胆固醇 | LDL cholesterol |
| `triglycerides` | 甘油三酯 | Triglycerides |
| `fasting_glucose` | 空腹血糖 | Fasting glucose |
| `hba1c` | 糖化血红蛋白 | HbA1c |
| `bmi` | 体重指数 | BMI |
| `waist_circumference` | 腰围 | Waist circumference |
| `waist_hip_ratio` | 腰臀比 | Waist-hip ratio |
| `heart_rate` | 心率 | Heart rate |
| `alcohol_units_week` | 每周饮酒单位 | Alcohol units per week |
| `physical_activity_days` | 每周运动天数 | Physically active days per week |
| `mediterranean_diet_score` | 地中海饮食评分 | Mediterranean diet score |
| `sleep_hours` | 睡眠时长 | Sleep hours |
| `crp` | C反应蛋白 | CRP |
| `fibrinogen` | 纤维蛋白原 | Fibrinogen |
| `left_ventricular_ejection` | 左室射血分数 | LVEF |
| `avg_systolic_bp_24h` | 24h平均收缩压 | 24h average systolic BP |
| `bp_variability` | 血压变异度 | Blood pressure variability |
| `heart_rate_variability` | 心率变异度 | Heart rate variability |
| `daily_steps` | 日步数 | Daily steps |
| `sleep_efficiency` | 睡眠效率 | Sleep efficiency |
| `air_quality` | 空气质量指数 | Air quality index |
| `season` | 季节编码 | Season code |

### 2.3 阈值覆盖示例 / Threshold Override Example

```json
{
  "model_type": "xgb_multi",
  "thresholds": {
    "stroke": [0.25, 0.4, 0.55]
  },
  "records": []
}
```

## 3. 响应结果说明 / Response Structure

### 3.1 成功响应 / Success Response

```json
{
  "success": true,
  "predictions": {
    "stroke": {
      "risk_7d": 0.18,
      "risk_30d": 0.31,
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
      "factors": ["feature_a", "feature_b", "feature_c"]
    }
  ],
  "model_variant": "A",
  "model_type": "xgb_multi"
}
```

### 3.2 顶层字段说明 / Top-level Response Fields

| 字段（Field） | 中文说明 | English Description |
|---|---|---|
| `success` | 是否成功 | Whether request succeeded |
| `predictions` | 每个病种的风险预测结果 | Risk prediction result for each disease |
| `top_factors` | 每个病种的Top特征列表 | Top factors list per disease |
| `model_variant` | 使用的模型版本（默认A，可由请求头`X-Model-Variant`指定） | Model variant used (default A, can be set by `X-Model-Variant`) |
| `model_type` | 使用的模型类型 | Model type used |

### 3.3 `predictions.<disease>` 字段 / Fields in `predictions.<disease>`

| 字段（Field） | 中文说明 | English Description |
|---|---|---|
| `risk_7d` | 7天风险概率（0~1） | 7-day risk probability (0~1) |
| `risk_30d` | 30天风险概率（0~1） | 30-day risk probability (0~1) |
| `risk_level_7d` | 7天风险等级（低/中/高/极高） | 7-day risk level (low/medium/high/very high) |
| `risk_level_30d` | 30天风险等级（低/中/高/极高） | 30-day risk level (low/medium/high/very high) |
| `thresholds` | 风险分级阈值 `(low, mid, high)` | Risk level thresholds `(low, mid, high)` |
| `recommendations_7d` | 7天风险对应建议列表 | Recommendation list for 7-day risk |
| `recommendations_30d` | 30天风险对应建议列表 | Recommendation list for 30-day risk |

### 3.4 `top_factors` 字段 / `top_factors` Field

| 字段（Field） | 中文说明 | English Description |
|---|---|---|
| `disease` | 病种代码名 | Disease code name |
| `factors` | 该病种最重要特征名称列表（最多5个） | Most important feature names for that disease (up to 5) |

## 4. 常见失败响应 / Common Error Responses

### 4.1 `records_missing`

```json
{
  "success": false,
  "error": "records_missing"
}
```

- 中文：请求体为空，或缺少 `records` 字段。  
  English: Request body is empty or missing `records`.

### 4.2 `model_not_found`

```json
{
  "success": false,
  "error": "model_not_found",
  "message": "[Errno 2] No such file or directory: 'models/xgb_multi_7d_A.joblib'",
  "hint": "请先训练并导出模型到 models 目录，例如运行 scripts/train.py"
}
```

- 中文：模型文件不存在，需要先训练并导出到 `models` 目录。  
  English: Model file is missing; train and export to `models` first.

### 4.3 `predict_failed`

```json
{
  "success": false,
  "error": "predict_failed",
  "message": "..."
}
```

- 中文：预测过程中发生其他异常，请根据 `message` 排查。  
  English: Other runtime error during prediction; inspect `message`.

## 5. 测试建议 / Testing Tips

- 优先使用“填充示例”按钮，确保字段完整。  
  Use the demo payload button first to ensure required fields are present.
- 同一患者建议至少提供7天连续记录。  
  Provide at least 7 consecutive records for the same patient.
- 若切换模型版本，在请求头设置 `X-Model-Variant`。  
  To switch model variant, set request header `X-Model-Variant`.

