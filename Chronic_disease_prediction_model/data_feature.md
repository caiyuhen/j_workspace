<<<<<<< HEAD


## 1. 基本信息
- **patient_id**: 患者ID
- **exam_date**: 检查日期

## 2. 人口统计学特征
- **age**: 年龄
- **gender**: 性别 (0=女性, 1=男性)
- **ethnicity**: 种族 (Asian, Black, Hispanic, White, Other)
- **education_years**: 教育年限 (0-20年)
- **socioeconomic_score**: 社会经济评分 (1-10分)

## 3. 临床生理指标
- **systolic_bp**: 收缩压 (80-220 mmHg)
- **diastolic_bp**: 舒张压 (40-130 mmHg)
- **total_cholesterol**: 总胆固醇 (100-350 mg/dL)
- **hdl_cholesterol**: HDL胆固醇 (20-100 mg/dL)
- **ldl_cholesterol**: LDL胆固醇 (30-250 mg/dL)
- **triglycerides**: 甘油三酯 (50-500 mg/dL)
- **fasting_glucose**: 空腹血糖 (70-300 mg/dL)
- **hba1c**: 糖化血红蛋白 (4-14%)
- **bmi**: 体重指数 (15-45)
- **waist_circumference**: 腰围 (60-150 cm)
- **waist_hip_ratio**: 腰臀比 (0.6-1.2)
- **heart_rate**: 心率 (40-120 bpm)

## 4. 疾病史
- **atrial_fibrillation**: 房颤 (0=无, 1=有)
- **previous_stroke**: 既往卒中史 (0=无, 1=有)
- **previous_tia**: 既往TIA史 (0=无, 1=有)
- **heart_disease**: 心脏病史 (0=无, 1=有)
- **diabetes_years**: 糖尿病年限 (0-20年)
- **hypertension_years**: 高血压年限 (0-25年)
- **hypertension_controlled**: 高血压是否控制 (0=否, 1=是)
- **chronic_kidney_disease**: 慢性肾病 (0=无, 1=有)
- **peripheral_artery_disease**: 外周动脉疾病 (0=无, 1=有)

## 5. 生活方式因素
- **smoking_status**: 吸烟状态 (never, former, current)
- **alcohol_units_week**: 每周饮酒单位 (0-35)
- **physical_activity_days**: 每周体力活动天数 (0-7天)
- **mediterranean_diet_score**: 地中海饮食评分 (1-14分)
- **sleep_hours**: 睡眠时长 (3-10小时)

## 6. 家族史
- **family_stroke_history**: 家族卒中史 (0=无, 1=有)
- **family_heart_disease**: 家族心脏病史 (0=无, 1=有)

## 7. 生物标志物
- **crp**: C反应蛋白 (0.1-15 mg/L)
- **fibrinogen**: 纤维蛋白原 (150-700 mg/dL)
- **genetic_risk_score**: 基因风险评分 (1-10分)

## 8. 影像学数据
- **carotid_plaque**: 颈动脉斑块 (0=无, 1=有)
- **carotid_stenosis_percent**: 颈动脉狭窄百分比 (0-99%)
- **white_matter_lesions**: 白质病变 (0=无, 1=有)
- **left_ventricular_ejection**: 左心室射血分数 (25-75%)

## 9. 可穿戴设备数据
- **avg_systolic_bp_24h**: 24小时平均收缩压
- **bp_variability**: 血压变异性 (2-25)
- **heart_rate_variability**: 心率变异性 (5-60)
- **daily_steps**: 日均步数 (500-15000)
- **sleep_efficiency**: 睡眠效率 (50-95%)

## 10. 目标变量
- **stroke**: 卒中 (0=无, 1=有)

## 特征工程后的重要特征
根据特征选择结果，最重要的20个特征包括：
- age_base, systolic_bp_base, hdl_base, triglycerides_base
- heart_rate_base, activity_base, age, systolic_bp
- total_cholesterol, ldl_cholesterol, diabetes_years
- crp, fibrinogen, avg_systolic_bp_24h
- heart_rate_variability, daily_steps
- 以及一些编码后的分类特征

这个数据集涵盖了脑卒中预测的多个维度，包括传统的临床指标、生活方式因素、家族史、生物标志物和现代可穿戴设备数据，为构建全面的脑卒中风险预测模型提供了丰富的特征基础。
=======


## 1. 基本信息
- **patient_id**: 患者ID
- **exam_date**: 检查日期

## 2. 人口统计学特征
- **age**: 年龄
- **gender**: 性别 (0=女性, 1=男性)
- **ethnicity**: 种族 (Asian, Black, Hispanic, White, Other)
- **education_years**: 教育年限 (0-20年)
- **socioeconomic_score**: 社会经济评分 (1-10分)

## 3. 临床生理指标
- **systolic_bp**: 收缩压 (80-220 mmHg)
- **diastolic_bp**: 舒张压 (40-130 mmHg)
- **total_cholesterol**: 总胆固醇 (100-350 mg/dL)
- **hdl_cholesterol**: HDL胆固醇 (20-100 mg/dL)
- **ldl_cholesterol**: LDL胆固醇 (30-250 mg/dL)
- **triglycerides**: 甘油三酯 (50-500 mg/dL)
- **fasting_glucose**: 空腹血糖 (70-300 mg/dL)
- **hba1c**: 糖化血红蛋白 (4-14%)
- **bmi**: 体重指数 (15-45)
- **waist_circumference**: 腰围 (60-150 cm)
- **waist_hip_ratio**: 腰臀比 (0.6-1.2)
- **heart_rate**: 心率 (40-120 bpm)
- **eGFR**：<45 mL/min/1.73m²

## 4. 疾病史
- **atrial_fibrillation**: 房颤 (0=无, 1=有)
- **previous_stroke**: 既往卒中史 (0=无, 1=有)
- **previous_tia**: 既往TIA史 (0=无, 1=有)
- **heart_disease**: 心脏病史 (0=无, 1=有)
- **diabetes_years**: 糖尿病年限 (0-20年)
- **hypertension_years**: 高血压年限 (0-25年)
- **hypertension_controlled**: 高血压是否控制 (0=否, 1=是)
- **chronic_kidney_disease**: 慢性肾病 (0=无, 1=有)
- **peripheral_artery_disease**: 外周动脉疾病 (0=无, 1=有)

## 5. 生活方式因素
- **smoking_status**: 吸烟状态 (never, former, current)
- **alcohol_units_week**: 每周饮酒单位 (0-35)
- **physical_activity_days**: 每周体力活动天数 (0-7天)
- **mediterranean_diet_score**: 地中海饮食评分 (1-14分)
- **sleep_hours**: 睡眠时长 (3-10小时)

## 6. 家族史
- **family_stroke_history**: 家族卒中史 (0=无, 1=有)
- **family_heart_disease**: 家族心脏病史 (0=无, 1=有)

## 7. 生物标志物
- **crp**: C反应蛋白 (0.1-15 mg/L)
- **fibrinogen**: 纤维蛋白原 (150-700 mg/dL)
- **genetic_risk_score**: 基因风险评分 (1-10分)

## 8. 影像学数据
- **carotid_plaque**: 颈动脉斑块 (0=无, 1=有)
- **carotid_stenosis_percent**: 颈动脉狭窄百分比 (0-99%)
- **white_matter_lesions**: 白质病变 (0=无, 1=有)
- **left_ventricular_ejection**: 左心室射血分数 (25-75%)

## 9. 可穿戴设备数据
- **avg_systolic_bp_24h**: 24小时平均收缩压
- **bp_variability**: 血压变异性 (2-25)
- **heart_rate_variability**: 心率变异性 (5-60)
- **daily_steps**: 日均步数 (500-15000)
- **sleep_efficiency**: 睡眠效率 (50-95%)

## 10. 目标变量
- **stroke**: 卒中 (0=无, 1=有)

## 特征工程后的重要特征
根据特征选择结果，最重要的20个特征包括：
- age_base, systolic_bp_base, hdl_base, triglycerides_base
- heart_rate_base, activity_base, age, systolic_bp
- total_cholesterol, ldl_cholesterol, diabetes_years
- crp, fibrinogen, avg_systolic_bp_24h
- heart_rate_variability, daily_steps
- 以及一些编码后的分类特征

这个数据集涵盖了脑卒中预测的多个维度，包括传统的临床指标、生活方式因素、家族史、生物标志物和现代可穿戴设备数据，为构建全面的脑卒中风险预测模型提供了丰富的特征基础。
>>>>>>> origin/main
        