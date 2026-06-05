# Risk Results 文件夹 JSON 变量说明文档

## 概述

本文档详细说明了 `risk_results` 文件夹中 JSON 文件的所有变量名称、含义和用途。该文件夹包含两种类型的文件：

1. **个人风险评估报告**：`{device_id}_advanced_7day_risk_assessment.json`
2. **批量处理摘要报告**：`advanced_7day_risk_batch_summary.json`

---

## 1. 个人风险评估报告文件结构

### 1.1 基本信息字段

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `device_id` | String | 设备唯一标识符，用于识别具体的PPG监测设备 |
| `analysis_timestamp` | String (ISO 8601) | 风险评估分析的时间戳，格式为ISO 8601标准 |

### 1.2 风险预测 (risk_prediction)

#### 1.2.1 心梗风险预测 (myocardial_infarction)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `7_day_risk_ratio` | Float | 7天心梗风险比率，相对于基线风险的数值 |
| `30_day_risk_ratio` | Float | 30天心梗风险比率，相对于基线风险的数值 |
| `risk_score` | Float | 综合风险评分，范围0-1，数值越高风险越大 |
| `risk_level` | String | 总体风险等级：低风险/中风险/高风险/极高风险 |
| `7_day_percentage` | Float | 7天心梗风险百分比表示 |
| `30_day_percentage` | Float | 30天心梗风险百分比表示 |
| `7_day_risk_level` | String | 7天风险等级分类 |
| `30_day_risk_level` | String | 30天风险等级分类 |
| `7_day_multiplier` | Float | 7天风险倍数，相对于基线风险的倍数 |
| `30_day_multiplier` | Float | 30天风险倍数，相对于基线风险的倍数 |

#### 1.2.2 脑卒中风险预测 (stroke)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `7_day_risk_ratio` | Float | 7天脑卒中风险比率 |
| `30_day_risk_ratio` | Float | 30天脑卒中风险比率 |
| `risk_score` | Float | 脑卒中综合风险评分 |
| `risk_level` | String | 脑卒中总体风险等级 |
| `7_day_percentage` | Float | 7天脑卒中风险百分比 |
| `30_day_percentage` | Float | 30天脑卒中风险百分比 |
| `7_day_risk_level` | String | 7天脑卒中风险等级 |
| `30_day_risk_level` | String | 30天脑卒中风险等级 |
| `7_day_multiplier` | Float | 7天脑卒中风险倍数 |
| `30_day_multiplier` | Float | 30天脑卒中风险倍数 |

### 1.3 特征分析 (feature_analysis)

#### 1.3.1 心梗特征 (mi_features)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `resting_hr_elevation` | Float | 静息心率升高程度，0-1标准化值 |
| `hrv_decline` | Float | 心率变异性下降程度 |
| `pvc_increase` | Float | 室性早搏增加程度 |
| `rhythm_irregularity` | Float | 心律不齐程度 |
| `exercise_tolerance_decline` | Float | 运动耐量下降程度 |
| `spo2_decline` | Float | 血氧饱和度下降程度 |
| `hr_recovery_delay` | Float | 心率恢复延迟程度 |
| `exercise_hr_response` | Float | 运动心率反应异常程度 |
| `hr_reserve_decline` | Float | 心率储备下降程度 |
| `activity_intensity_change` | Float | 活动强度变化程度 |
| `autonomic_dysfunction` | Float | 自主神经功能异常程度 |
| `circadian_rhythm_abnormal` | Float | 昼夜节律异常程度 |

#### 1.3.2 脑卒中特征 (stroke_features)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `afib_detection` | Float | 房颤检出程度 |
| `pac_frequent` | Float | 房性早搏频发程度 |
| `rhythm_irregularity` | Float | 心律不齐程度 |
| `bp_circadian_abnormal` | Float | 血压昼夜节律异常程度 |
| `vascular_elasticity_decline` | Float | 血管弹性下降程度 |
| `sleep_apnea` | Float | 睡眠呼吸暂停程度 |
| `nocturnal_spo2_decline` | Float | 夜间血氧饱和度下降程度 |
| `temperature_elevation` | Float | 体温升高程度 |
| `cerebral_flow_abnormal` | Float | 脑血流异常程度 |
| `acute_phase_reaction` | Float | 急性期反应程度 |
| `activity_pattern` | Float | 活动模式异常程度 |
| `stress_response` | Float | 应激反应程度 |

#### 1.3.3 共同特征 (common_features)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `systemic_inflammation` | Float | 全身炎症程度 |
| `hemodynamic_abnormal` | Float | 血流动力学异常程度 |
| `autonomic_dysfunction` | Float | 自主神经功能异常程度 |
| `metabolic_dysfunction` | Float | 代谢功能异常程度 |
| `lifestyle_factors` | Float | 生活方式因素影响程度 |

### 1.4 风险因素分析 (risk_factors_analysis)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `primary_risk_factors` | Array[String] | 主要风险因素列表，对风险贡献最大的因素 |
| `secondary_risk_factors` | Array[String] | 次要风险因素列表，对风险有一定贡献的因素 |
| `protective_factors` | Array[String] | 保护性因素列表，降低风险的有利因素 |

### 1.5 建议 (recommendations)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `recommendations` | Array[String] | 个性化健康建议列表，基于风险评估结果生成 |

### 1.6 计算详情 (calculation_details)

#### 1.6.1 基线风险 (baseline_risks)

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `mi_7day` | Float | 7天心梗基线风险值 |
| `mi_30day` | Float | 30天心梗基线风险值 |
| `stroke_7day` | Float | 7天脑卒中基线风险值 |
| `stroke_30day` | Float | 30天脑卒中基线风险值 |

#### 1.6.2 风险权重 (risk_weights)

##### 心梗权重 (mi_weights)
| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `resting_hr_elevation` | Float | 静息心率升高的权重系数 |
| `hr_recovery_delay` | Float | 心率恢复延迟的权重系数 |
| `exercise_hr_response` | Float | 运动心率反应的权重系数 |
| `hr_reserve_decline` | Float | 心率储备下降的权重系数 |
| `pvc_increase` | Float | 室性早搏增加的权重系数 |
| `hrv_decline` | Float | 心率变异性下降的权重系数 |
| `rhythm_irregularity` | Float | 心律不齐的权重系数 |
| `exercise_tolerance_decline` | Float | 运动耐量下降的权重系数 |
| `activity_intensity_change` | Float | 活动强度变化的权重系数 |
| `autonomic_dysfunction` | Float | 自主神经功能异常的权重系数 |
| `circadian_rhythm_abnormal` | Float | 昼夜节律异常的权重系数 |
| `spo2_decline` | Float | 血氧饱和度下降的权重系数 |

##### 脑卒中权重 (stroke_weights)
| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `afib_detection` | Float | 房颤检出的权重系数 |
| `pac_frequent` | Float | 房性早搏频发的权重系数 |
| `rhythm_irregularity` | Float | 心律不齐的权重系数 |
| `bp_circadian_abnormal` | Float | 血压昼夜节律异常的权重系数 |
| `vascular_elasticity_decline` | Float | 血管弹性下降的权重系数 |
| `cerebral_flow_abnormal` | Float | 脑血流异常的权重系数 |
| `sleep_apnea` | Float | 睡眠呼吸暂停的权重系数 |
| `nocturnal_spo2_decline` | Float | 夜间血氧饱和度下降的权重系数 |
| `temperature_elevation` | Float | 体温升高的权重系数 |
| `acute_phase_reaction` | Float | 急性期反应的权重系数 |
| `activity_pattern` | Float | 活动模式异常的权重系数 |
| `stress_response` | Float | 应激反应的权重系数 |

##### 共同风险权重 (common_weights)
| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `systemic_inflammation` | Float | 全身炎症的权重系数 |
| `hemodynamic_abnormal` | Float | 血流动力学异常的权重系数 |
| `autonomic_dysfunction` | Float | 自主神经功能异常的权重系数 |
| `metabolic_dysfunction` | Float | 代谢功能异常的权重系数 |
| `lifestyle_factors` | Float | 生活方式因素的权重系数 |

#### 1.6.3 方法学信息

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `methodology` | String | 风险评估方法学描述和版本信息 |

---

## 2. 批量处理摘要报告文件结构

### 2.1 批量处理统计信息

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `total_files` | Integer | 总处理文件数量 |
| `processed_files` | Integer | 成功处理的文件数量 |
| `failed_files` | Integer | 处理失败的文件数量 |
| `processing_timestamp` | String (ISO 8601) | 批量处理完成的时间戳 |

### 2.2 处理结果详情 (results)

每个结果项包含以下字段：

| 变量名 | 数据类型 | 说明 |
|--------|----------|------|
| `input_file` | String | 输入文件的完整路径 |
| `output_file` | String | 输出文件的完整路径 |
| `device_id` | String | 设备ID |
| `mi_risk_level` | String | 心梗风险等级（低风险/中风险/高风险/极高风险） |
| `stroke_risk_level` | String | 脑卒中风险等级（低风险/中风险/高风险/极高风险） |
| `status` | String | 处理状态（success/failed） |

---

## 3. 风险等级分类标准

### 3.1 总体风险等级

- **低风险**：风险评分 < 0.3
- **中风险**：0.3 ≤ 风险评分 < 0.6
- **高风险**：0.6 ≤ 风险评分 < 0.8
- **极高风险**：风险评分 ≥ 0.8

### 3.2 30天风险等级（基于风险倍数）

- **低风险**：风险倍数 < 2.0
- **中风险**：2.0 ≤ 风险倍数 < 5.0
- **高风险**：5.0 ≤ 风险倍数 < 10.0
- **极高风险**：风险倍数 ≥ 10.0

---

## 4. 数据使用说明

### 4.1 特征值范围
- 所有特征值均为0-1之间的标准化数值
- 0表示该特征正常或无异常
- 1表示该特征异常程度最高

### 4.2 风险计算方法
1. **特征提取**：从PPG信号中提取各类生理指标特征
2. **权重计算**：根据医学研究确定的权重系数计算风险评分
3. **风险比率**：结合基线风险计算相对风险比率
4. **等级分类**：根据风险评分和倍数确定风险等级

### 4.3 临床应用建议
- **低风险**：定期监测，保持健康生活方式
- **中风险**：建议1-2周内就医检查
- **高风险**：建议1周内就医检查
- **极高风险**：建议立即就医

---

## 5. 版本信息

- **模型版本**：基于PPG信号分析的高级多因子风险评估模型v2.0
- **文档版本**：1.0
- **最后更新**：2025-10-28

---

## 6. 注意事项

1. 本风险评估结果仅供参考，不能替代专业医学诊断
2. 建议结合其他临床检查结果综合判断
3. 风险评估基于PPG信号分析，可能受到设备佩戴、环境等因素影响
4. 定期校准和更新评估模型以确保准确性