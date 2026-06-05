# PPG血管功能分析结果变量名中英文对照表

## 文件概述
本文档详细说明了 `analysis_results` 文件夹下JSON分析结果文件中所有变量名的含义和中英文对照。

---

## 1. 基本信息 (Basic Information)

| 英文变量名 | 中文含义 | 数据类型 | 说明 |
|-----------|---------|---------|------|
| `device_id` | 设备ID | String | 唯一标识设备的编号 |
| `analysis_timestamp` | 分析时间戳 | String | 分析完成的时间 (ISO格式) |

---

## 2. 数据摘要 (Data Summary)

| 英文变量名 | 中文含义 | 数据类型 | 说明 |
|-----------|---------|---------|------|
| `total_segments` | 总数据段数 | Integer | 原始数据的总段数 |
| `analyzed_vascular_segments` | 已分析血管功能段数 | Integer | 成功分析的血管功能数据段数 |
| `analyzed_blood_flow_segments` | 已分析血流段数 | Integer | 成功分析的血流数据段数 |
| `analyzed_arrhythmia_segments` | 已分析心律不齐段数 | Integer | 成功分析的心律不齐数据段数 |
| `analyzed_inflammation_segments` | 已分析炎症段数 | Integer | 成功分析的炎症数据段数 |
| `sleep_analysis_data_points` | 睡眠分析数据点数 | Integer | 用于睡眠分析的PPG数据点总数 |
| `vascular_analysis_success_rate` | 血管分析成功率 | Float | 血管功能分析的成功率 (0-1) |
| `blood_flow_analysis_success_rate` | 血流分析成功率 | Float | 血流分析的成功率 (0-1) |
| `arrhythmia_analysis_success_rate` | 心律不齐分析成功率 | Float | 心律不齐分析的成功率 (0-1) |
| `inflammation_analysis_success_rate` | 炎症分析成功率 | Float | 炎症分析的成功率 (0-1) |

---

## 3. 血管功能统计 (Vascular Function Statistics)

### 3.1 基本统计信息
| 英文变量名 | 中文含义 | 数据类型 | 说明 |
|-----------|---------|---------|------|
| `total_segments` | 总段数 | Integer | 血管功能分析的总段数 |
| `valid_segments` | 有效段数 | Integer | 信号质量合格的段数 |
| `signal_quality_rate` | 信号质量率 | Float | 有效段数占总段数的比例 |

### 3.2 心率统计 (Heart Rate Stats)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `heart_rate_stats.mean` | 平均心率 | bpm | 所有段的平均心率 |
| `heart_rate_stats.std` | 心率标准差 | bpm | 心率的变异程度 |
| `heart_rate_stats.min` | 最低心率 | bpm | 记录期间的最低心率 |
| `heart_rate_stats.max` | 最高心率 | bpm | 记录期间的最高心率 |
| `heart_rate_stats.count` | 心率数据点数 | Integer | 有效心率测量次数 |

### 3.3 脉搏波传导速度统计 (PWV Stats)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `pwv_stats.mean` | 平均脉搏波传导速度 | m/s | 动脉硬化程度指标 |
| `pwv_stats.std` | PWV标准差 | m/s | PWV的变异程度 |
| `pwv_stats.min` | 最小PWV | m/s | 记录期间的最小PWV |
| `pwv_stats.max` | 最大PWV | m/s | 记录期间的最大PWV |
| `pwv_stats.count` | PWV数据点数 | Integer | 有效PWV测量次数 |

### 3.4 增强指数统计 (AIx Stats)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `aix_stats.mean` | 平均增强指数 | % | 反映动脉硬化和波反射 |
| `aix_stats.std` | AIx标准差 | % | AIx的变异程度 |
| `aix_stats.min` | 最小AIx | % | 记录期间的最小AIx |
| `aix_stats.max` | 最大AIx | % | 记录期间的最大AIx |
| `aix_stats.count` | AIx数据点数 | Integer | 有效AIx测量次数 |

### 3.5 血管年龄统计 (Vascular Age Stats)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `vascular_age_stats.mean` | 平均血管年龄 | 岁 | 基于血管功能评估的生理年龄 |
| `vascular_age_stats.std` | 血管年龄标准差 | 岁 | 血管年龄的变异程度 |
| `vascular_age_stats.min` | 最小血管年龄 | 岁 | 记录期间的最小血管年龄 |
| `vascular_age_stats.max` | 最大血管年龄 | 岁 | 记录期间的最大血管年龄 |
| `vascular_age_stats.count` | 血管年龄数据点数 | Integer | 有效血管年龄测量次数 |

### 3.6 其他血管功能参数
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `rise_time_ratio_stats` | 上升时间比统计 | 脉搏波形态参数 |
| `systolic_diastolic_ratio_stats` | 收缩舒张比统计 | 血压相关参数 |
| `amplitude_variation_stats` | 振幅变异统计 | 脉搏波振幅变化 |
| `aging_index_stats` | 老化指数统计 | 血管老化程度指标 |
| `lf_hf_ratio_stats` | 低频高频比统计 | 心率变异性频域参数 |
| `total_power_stats` | 总功率统计 | 心率变异性总功率 |

---

## 4. 血流统计 (Blood Flow Statistics)

### 4.1 灌注相关参数
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `perfusion_index_stats` | 灌注指数统计 | % | 外周血流灌注程度 |
| `flow_velocity_stats` | 血流速度统计 | cm/s | 血液流动速度 |
| `flow_velocity_index_stats` | 血流速度指数统计 | - | 血流速度相关指数 |
| `cardiac_output_index_stats` | 心输出量指数统计 | L/min/m² | 心脏泵血能力指标 |

### 4.2 血管参数
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `vascular_compliance_stats` | 血管顺应性统计 | - | 血管弹性程度 |
| `vascular_resistance_stats` | 血管阻力统计 | - | 血管对血流的阻力 |

### 4.3 血流状态分布
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `flow_status_distribution.高灌注` | 高灌注段数 | 血流灌注过高的数据段数量 |
| `flow_status_distribution.正常灌注` | 正常灌注段数 | 血流灌注正常的数据段数量 |
| `flow_status_distribution.低灌注` | 低灌注段数 | 血流灌注不足的数据段数量 |
| `total_analyzed_segments` | 总分析段数 | 血流分析的总段数 |

---

## 5. 心律不齐统计 (Arrhythmia Statistics)

### 5.1 时域统计 (Time Domain Statistics)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `mean_ppi` | 平均脉搏间期 | ms | 相邻脉搏间的平均时间间隔 |
| `sdnn` | 正常间期标准差 | ms | 心率变异性时域指标 |
| `rmssd` | 相邻间期差值均方根 | ms | 短期心率变异性指标 |
| `pnn50` | 相邻间期差值>50ms百分比 | % | 心率变异性指标 |
| `cv` | 变异系数 | % | 心率变异的相对程度 |
| `irregularity_index` | 不规律指数 | - | 心律不规律程度 |

### 5.2 频域统计 (Frequency Domain Statistics)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `lf_hf_ratio` | 低频高频比 | 自主神经平衡指标 |

### 5.3 心律不齐检测统计
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `afib_detection_rate` | 房颤检出率 | 房颤事件占总段数的比例 |
| `pac_detection_rate` | 房性早搏检出率 | 房性早搏事件占总段数的比例 |
| `pvc_detection_rate` | 室性早搏检出率 | 室性早搏事件占总段数的比例 |
| `sinus_arrhythmia_rate` | 窦性心律不齐率 | 窦性心律不齐占总段数的比例 |
| `normal_rhythm_rate` | 正常心律率 | 正常心律占总段数的比例 |

---

## 6. 炎症统计 (Inflammation Statistics)

### 6.1 基本炎症指标
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `total_segments` | 总段数 | 炎症分析的总段数 |
| `average_inflammation_score` | 平均炎症评分 | 整体炎症水平评估 |
| `inflammation_score_std` | 炎症评分标准差 | 炎症评分的变异程度 |

### 6.2 炎症等级分布
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `inflammation_grade_distribution.mild` | 轻度炎症分布 | 轻度炎症的段数和百分比 |
| `inflammation_grade_distribution.moderate` | 中度炎症分布 | 中度炎症的段数和百分比 |
| `inflammation_grade_distribution.severe` | 重度炎症分布 | 重度炎症的段数和百分比 |

### 6.3 灌注统计
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `perfusion_statistics.average_perfusion_index` | 平均灌注指数 | 炎症分析中的平均灌注水平 |
| `perfusion_statistics.perfusion_index_std` | 灌注指数标准差 | 灌注指数的变异程度 |
| `perfusion_statistics.average_perfusion_variability` | 平均灌注变异性 | 灌注变化的程度 |
| `perfusion_statistics.perfusion_variability_std` | 灌注变异性标准差 | 灌注变异性的标准差 |

### 6.4 心率变异性统计
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `hrv_statistics.average_sdnn` | 平均SDNN | 心率变异性时域指标 |
| `hrv_statistics.sdnn_std` | SDNN标准差 | SDNN的变异程度 |
| `hrv_statistics.average_rmssd` | 平均RMSSD | 短期心率变异性指标 |
| `hrv_statistics.rmssd_std` | RMSSD标准差 | RMSSD的变异程度 |
| `hrv_statistics.average_lf_hf_ratio` | 平均低频高频比 | 自主神经平衡指标 |
| `hrv_statistics.lf_hf_ratio_std` | 低频高频比标准差 | LF/HF比值的变异程度 |

### 6.5 预测标志物统计
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `predicted_markers_statistics.average_predicted_crp` | 平均预测CRP | 预测的C反应蛋白水平 |
| `predicted_markers_statistics.predicted_crp_std` | 预测CRP标准差 | 预测CRP的变异程度 |
| `predicted_markers_statistics.average_predicted_il6` | 平均预测IL-6 | 预测的白介素-6水平 |
| `predicted_markers_statistics.predicted_il6_std` | 预测IL-6标准差 | 预测IL-6的变异程度 |

### 6.6 分析质量分布
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `analysis_quality_distribution.poor` | 差质量分布 | 分析质量差的段数和百分比 |
| `analysis_quality_distribution.fair` | 一般质量分布 | 分析质量一般的段数和百分比 |
| `analysis_quality_distribution.good` | 良好质量分布 | 分析质量良好的段数和百分比 |
| `analysis_quality_distribution.excellent` | 优秀质量分布 | 分析质量优秀的段数和百分比 |

---

## 7. 睡眠分析 (Sleep Analysis)

### 7.1 睡眠呼吸暂停分析 (Sleep Apnea Analysis)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `apnea_events` | 呼吸暂停事件 | Array | 检测到的呼吸暂停事件列表 |
| `apnea_events[].start_time` | 开始时间 | String | 呼吸暂停事件开始时间 |
| `apnea_events[].end_time` | 结束时间 | String | 呼吸暂停事件结束时间 |
| `apnea_events[].duration_seconds` | 持续时间 | 秒 | 呼吸暂停持续时间 |
| `apnea_events[].severity` | 严重程度 | String | mild/moderate/severe |
| `hypopnea_events` | 低通气事件 | Array | 检测到的低通气事件列表 |
| `hypopnea_events[].reduction_percentage` | 减少百分比 | % | 呼吸流量减少的百分比 |
| `ahi_index` | 呼吸暂停低通气指数 | 次/小时 | AHI指数，睡眠呼吸暂停严重程度指标 |
| `severity` | 严重程度 | String | normal/mild/moderate/severe |
| `total_events` | 总事件数 | Integer | 呼吸暂停和低通气事件总数 |
| `apnea_count` | 呼吸暂停次数 | Integer | 纯呼吸暂停事件数量 |
| `hypopnea_count` | 低通气次数 | Integer | 低通气事件数量 |

### 7.2 呼吸统计 (Respiratory Statistics)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `respiratory_statistics.respiratory_rate` | 呼吸频率 | 次/分钟 | 平均呼吸频率 |
| `respiratory_statistics.respiratory_variability` | 呼吸变异性 | - | 呼吸节律的变异程度 |
| `respiratory_statistics.respiratory_regularity` | 呼吸规律性 | - | 呼吸节律的规律程度 |
| `respiratory_statistics.signal_strength` | 信号强度 | - | 呼吸信号的强度 |
| `analysis_quality` | 分析质量 | String | poor/fair/good/excellent |

### 7.3 夜间血氧分析 (Nocturnal SpO2 Analysis)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `mean_spo2` | 平均血氧饱和度 | % | 夜间平均血氧饱和度 |
| `min_spo2` | 最低血氧饱和度 | % | 夜间最低血氧饱和度 |
| `spo2_below_90_percent` | 血氧<90%时间比例 | % | 血氧饱和度低于90%的时间占比 |
| `desaturation_events` | 血氧饱和度下降事件 | Array | 血氧饱和度显著下降的事件 |
| `odi_index` | 氧减指数 | 次/小时 | 每小时血氧饱和度下降次数 |

### 7.4 血氧统计 (SpO2 Statistics)
| 英文变量名 | 中文含义 | 单位 | 说明 |
|-----------|---------|------|------|
| `spo2_statistics.mean_spo2` | 平均血氧 | % | 统计期间平均血氧饱和度 |
| `spo2_statistics.median_spo2` | 血氧中位数 | % | 血氧饱和度中位数 |
| `spo2_statistics.std_spo2` | 血氧标准差 | % | 血氧饱和度标准差 |
| `spo2_statistics.min_spo2` | 最低血氧 | % | 最低血氧饱和度 |
| `spo2_statistics.max_spo2` | 最高血氧 | % | 最高血氧饱和度 |
| `spo2_statistics.spo2_range` | 血氧范围 | % | 最高与最低血氧的差值 |

### 7.5 血氧变异性 (SpO2 Variability)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `spo2_variability.coefficient_of_variation` | 变异系数 | 血氧饱和度的相对变异程度 |
| `spo2_variability.rmssd` | 相邻差值均方根 | 血氧饱和度短期变异性 |
| `spo2_variability.variability_index` | 变异性指数 | 血氧饱和度变异性综合指标 |
| `night_duration_hours` | 夜间持续时间 | 小时 | 夜间监测的总时长 |

### 7.6 血压节律分析 (Blood Pressure Rhythm Analysis)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `circadian_analysis` | 昼夜节律分析 | 24小时血压变化模式 |
| `circadian_analysis.hourly_means` | 每小时平均值 | 每个小时的平均血压值 |
| `circadian_analysis.day_mean` | 白天平均值 | 白天时段的平均血压 |
| `circadian_analysis.night_mean` | 夜间平均值 | 夜间时段的平均血压 |
| `circadian_analysis.day_night_ratio` | 昼夜比值 | 白天与夜间血压的比值 |
| `circadian_analysis.circadian_amplitude` | 昼夜节律振幅 | 血压昼夜变化的幅度 |

### 7.7 夜间血压下降 (Nocturnal Dipping)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `nocturnal_dipping.day_mean` | 白天平均血压 | 白天时段平均血压 |
| `nocturnal_dipping.night_mean` | 夜间平均血压 | 夜间时段平均血压 |
| `nocturnal_dipping.dipping_percentage` | 下降百分比 | 夜间血压相对白天的下降百分比 |
| `nocturnal_dipping.dipping_pattern` | 下降模式 | dipper/non_dipper/reverse_dipper |

### 7.8 血压变异性 (BP Variability)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `bp_variability.short_term_variability` | 短期变异性 | 短时间内血压的变异程度 |
| `bp_variability.long_term_variability` | 长期变异性 | 长时间内血压的变异程度 |
| `bp_variability.coefficient_of_variation` | 变异系数 | 血压变异的相对程度 |
| `rhythm_pattern` | 节律模式 | 血压昼夜节律的总体模式 |
| `rhythm_quality` | 节律质量 | 血压节律分析的质量评估 |

### 7.9 睡眠分析基本信息
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `analysis_timestamp` | 分析时间戳 | 睡眠分析完成的时间 |
| `data_duration_hours` | 数据持续时间 | 用于睡眠分析的数据总时长（小时） |

---

## 8. 风险评估 (Risk Assessment)

### 8.1 心血管风险评估 (Cardiovascular Risk Assessment)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `risk_level` | 风险等级 | 低风险/中等风险/高风险 |
| `risk_score` | 风险评分 | 数值化的风险评分 |
| `risk_factors` | 风险因素 | 识别出的具体风险因素列表 |
| `recommendations` | 建议 | 针对风险的具体建议措施 |

### 8.2 血流风险评估 (Blood Flow Risk Assessment)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `risk_level` | 风险等级 | 血流正常/血流异常/血流风险 |
| `risk_score` | 风险评分 | 血流相关的风险评分 |
| `risk_factors` | 风险因素 | 血流相关的风险因素 |
| `recommendations` | 建议 | 血流改善建议 |

### 8.3 心律不齐风险评估 (Arrhythmia Risk Assessment)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `risk_level` | 风险等级 | normal/mild/moderate/severe |
| `risk_description` | 风险描述 | 风险等级的文字描述 |
| `risk_score` | 风险评分 | 心律不齐风险评分 |
| `risk_factors` | 风险因素 | 心律不齐相关风险因素 |
| `recommendations` | 建议 | 心律管理建议 |
| `detection_summary` | 检测摘要 | 各类心律不齐的检出率汇总 |

### 8.4 炎症风险评估 (Inflammation Risk Assessment)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `overall_risk_level` | 总体风险等级 | low/moderate/high |
| `risk_score` | 风险评分 | 炎症相关的总体风险评分 |
| `risk_factors` | 风险因素 | 炎症相关的风险因素 |
| `recommendations` | 建议 | 炎症控制和改善建议 |
| `detailed_assessment` | 详细评估 | 各项炎症指标的详细风险评估 |

---

## 9. 详细分析结果 (Detailed Analysis Results)

### 9.1 详细血管分析 (Detailed Vascular Analysis)
每个数据段包含以下信息：

| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `signal_quality` | 信号质量 | poor/fair/good/excellent |
| `heart_rate` | 心率 | 该段的心率值 (bpm) |
| `estimated_pwv` | 估算脉搏波传导速度 | 该段的PWV值 (m/s) |
| `augmentation_index` | 增强指数 | 该段的AIx值 (%) |
| `vascular_age` | 血管年龄 | 该段评估的血管年龄 (岁) |
| `segment_index` | 段索引 | 数据段的序号 |
| `collect_time` | 采集时间 | 数据采集的时间 |
| `create_time` | 创建时间 | 数据创建的时间 |

### 9.2 形态学特征 (Morphological Features)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `dicrotic_notch_index` | 重搏切迹指数 | 脉搏波形态特征 |
| `rise_time_ratio` | 上升时间比 | 脉搏波上升相对时间 |
| `systolic_diastolic_ratio` | 收缩舒张比 | 收缩期与舒张期比值 |
| `pulse_width` | 脉搏宽度 | 脉搏波的宽度 |
| `amplitude_variation` | 振幅变异 | 脉搏波振幅的变化 |

### 9.3 二阶导数特征 (SDPPG Features)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `a_wave_amplitude` | a波振幅 | 二阶导数a波的振幅 |
| `b_wave_amplitude` | b波振幅 | 二阶导数b波的振幅 |
| `c_wave_amplitude` | c波振幅 | 二阶导数c波的振幅 |
| `d_wave_amplitude` | d波振幅 | 二阶导数d波的振幅 |
| `aging_index` | 老化指数 | 基于SDPPG的血管老化指标 |

### 9.4 频域特征 (Frequency Domain Features)
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `vlf_power` | 极低频功率 | 心率变异性极低频段功率 |
| `lf_power` | 低频功率 | 心率变异性低频段功率 |
| `hf_power` | 高频功率 | 心率变异性高频段功率 |
| `total_power` | 总功率 | 心率变异性总功率 |
| `lf_hf_ratio` | 低频高频比 | LF/HF比值 |
| `normalized_lf` | 标准化低频 | 标准化的低频功率 |
| `normalized_hf` | 标准化高频 | 标准化的高频功率 |

### 9.5 数据质量信息
| 英文变量名 | 中文含义 | 说明 |
|-----------|---------|------|
| `data_length` | 数据长度 | 该段数据的采样点数 |
| `peaks_count` | 波峰数量 | 检测到的脉搏波峰数量 |
| `valleys_count` | 波谷数量 | 检测到的脉搏波谷数量 |

---

## 10. 数据质量等级说明

### 信号质量等级 (Signal Quality Levels)
- `excellent`: 优秀 - 信号清晰，噪声极少
- `good`: 良好 - 信号质量好，轻微噪声
- `fair`: 一般 - 信号可用，有一定噪声
- `poor`: 差 - 信号质量差，噪声较多

### 风险等级说明 (Risk Level Descriptions)
- `低风险/low`: 各项指标正常，风险较小
- `中等风险/moderate`: 部分指标异常，需要关注
- `高风险/high`: 多项指标异常，需要及时干预
- `严重风险/severe`: 指标严重异常，需要立即处理

### 严重程度等级 (Severity Levels)
- `normal`: 正常
- `mild`: 轻度
- `moderate`: 中度  
- `severe`: 重度

---

## 11. 单位说明 (Unit Descriptions)

| 单位 | 中文名称 | 说明 |
|------|---------|------|
| `bpm` | 次/分钟 | 心率单位 |
| `m/s` | 米/秒 | 脉搏波传导速度单位 |
| `%` | 百分比 | 百分比数值 |
| `ms` | 毫秒 | 时间单位 |
| `岁` | 年龄 | 年龄单位 |
| `次/小时` | 每小时次数 | 频率单位 |
| `L/min/m²` | 升/分钟/平方米 | 心输出量指数单位 |
| `cm/s` | 厘米/秒 | 血流速度单位 |

---

## 12. 注意事项

1. **数据完整性**: 某些字段可能为 `null`，表示该段数据无法计算该参数
2. **统计意义**: `count` 字段表示参与统计的有效数据段数量
3. **质量评估**: 建议优先关注 `signal_quality` 为 `good` 或 `excellent` 的数据段
4. **临床意义**: 所有数值仅供参考，具体诊断需结合临床医生判断
5. **时间格式**: 所有时间戳均采用 ISO 8601 格式或 "YYYY-MM-DD HH:MM:SS" 格式

---

*本文档基于PPG血管功能分析系统v1.0生成，如有疑问请参考相关技术文档或联系开发团队。*