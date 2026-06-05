# 数据模型定义

本文档描述了微服务之间交换的核心数据结构 (Pydantic Models)。

## 1. 治疗方案 (Treatment Plan)

用于定义应用于患者的干预措施。

```json
{
  "type": "Brace", // 枚举: "Brace", "Surgery", "Observation"
  "duration": 24,  // 持续时间（月）
  "compliance": 0.9 // 依从性 (0.0 - 1.0)，仅适用于 Brace
}
```

## 2. 脊柱参数 (Spine Parameters)

描述脊柱的几何形态，通常包含 17 个椎骨 (T1-L5) 的数据。

```json
{
  "vertebral_rotation": [0.5, 1.2, ...], // 每个椎骨的轴向旋转度（列表）
  "coronal_offset": [2.0, 5.5, ...],     // 冠状面偏移量 (mm)
  "sagittal_profile": [10.0, ...],       // 矢状面角度 (Kyphosis/Lordosis)
  "flexibility": 0.8                     // 脊柱柔韧性系数
}
```

## 3. 患者状态 (Patient State)

患者的完整快照，用于模拟输入。

```json
{
  "id": "PAT-12345",
  "name": "倪欣然",
  "age": 14,
  "gender": "Female",
  "diagnosis": "Scoliosis",
  "cobb_angle": 25.0,
  "spine_params": { ... }, // 基础脊柱参数
  "metrics": {             // 关键指标
    "cobb_angle": 25.0,
    "kyphosis_max": 40.0,
    "lordosis_max": 30.0
  },
  "curve_data": {          // 详细曲线数据
    "vertebral_rotation": [...],
    "coronal_offsets": [...],
    "sagittal_profile": [...]
  }
}
```

## 4. 模拟结果 (Simulation Result)

模拟服务的输出，包含时间序列数据。

```json
{
  "summary": {
    "initial_cobb": 25.0,
    "final_cobb": 18.5,
    "prediction_horizon_weeks": 104
  },
  "timeseries_data": {
    "timeline": [
      {
        "week": 0,
        "control": { // 对照组（未治疗/自然生长）
          "cobb_angle": 25.0,
          "spine_params": { ... }
        },
        "intervention": { // 干预组（当前治疗方案）
          "cobb_angle": 25.0,
          "spine_params": { ... }
        },
        "intensive": { // 强化干预组（高依从性/强化方案）
          "cobb_angle": 20.0,
          "spine_params": { ... }
        }
      },
      // ... 更多周的数据
    ]
  }
}
```
