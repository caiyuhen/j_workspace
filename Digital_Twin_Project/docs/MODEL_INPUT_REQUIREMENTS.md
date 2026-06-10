# 模型输入数据说明

本文档说明当前项目中各核心模型、服务和推理链路所需的输入数据，包括：

- 用户侧需要提供什么
- 各服务之间会传递什么
- 哪些字段是当前实现必填
- 哪些字段是可选或占位字段
- 如果未来扩展到 X 光 + PDF 联合分析，还需要补哪些输入

---

## 1. 总览

当前项目的核心链路为：

1. 用户上传 PDF 报告
2. OCR 服务提取文本
3. 患者服务将 OCR 文本解析为结构化患者状态
4. 模拟服务基于患者状态 + 治疗方案进行演变预测
5. 可视化服务基于模拟结果生成图表

因此，当前“模型输入数据”可以分为四层：

1. 原始输入层：PDF 文件
2. 中间结构化层：OCR 文本、患者状态
3. 模型推理层：初始状态、治疗方案
4. 展示层：时间序列、图表参数

---

## 2. 用户侧输入

### 2.1 OCR 导入链路输入

用于导入患者资料并建立患者档案。

**当前实现必填：**

- `file`: PDF 文件

**当前限制：**

- 仅支持 `.pdf`
- 不支持直接上传 JPG / PNG / DICOM

**输入示例：**

```http
POST /upload/ocr
Content-Type: multipart/form-data

file=<pdf>
```

---

### 2.2 报告生成链路输入

用于调用模拟和可视化流程。

**当前实现必填：**

- `patient_name`: 患者姓名
- `treatment_plan.type`: 治疗类型
- `treatment_plan.duration`: 持续月数
- `treatment_plan.compliance`: 依从性

**输入示例：**

```json
{
  "patient_name": "倪欣然",
  "treatment_plan": {
    "type": "Brace",
    "duration": 24,
    "compliance": 0.9
  }
}
```

---

## 3. OCR 服务输入

OCR 服务的目标是把 PDF 转成结构化文本结果。

### 3.1 输入字段

**接口：** `POST /ocr/extract`

**必填：**

- `file`: PDF 文件

**可选：**

- `save_json`: 是否保存提取结果，默认 `true`

### 3.2 实际依赖的数据条件

为了让 OCR 结果有意义，PDF 中最好包含：

- 患者姓名
- 检查时间
- Cobb 角或相关诊断结论
- 第 6、7、8 页中的正文内容

### 3.3 OCR 输出结构

OCR 服务返回：

```json
{
  "filename": "sample.pdf",
  "extracted_data": {
    "raw_text": "...",
    "extracted_pages": [
      {
        "page": 6,
        "content": "...",
        "method": "text_extraction"
      }
    ],
    "note": "使用了 pdfplumber 和/或 RapidOCR 提取。"
  },
  "json_path": "path/to/file.json",
  "status": "success"
}
```

### 3.4 当前实现特点

- 优先提取 PDF 文字层
- 文字层不足时再做 OCR
- 当前不直接分析 X 光图像本身，只提取图像里的文字

---

## 4. 患者服务输入

患者服务负责把 OCR 文本转换成“患者状态”。

### 4.1 输入来源

患者服务当前不直接接收复杂请求体，而是从 `extracted_data/*.json` 加载 OCR 结果。

### 4.2 患者解析所依赖的关键数据

解析器当前主要依赖：

- `raw_text`
- `filename`

### 4.3 当前会尝试提取的字段

从 OCR 文本中尝试解析：

- `name`
- `cobb_angle`

并基于默认逻辑生成：

- `metrics`
  - `cobb_angle`
  - `kyphosis_max`
  - `lordosis_max`
- `curve_data`
  - `vertebral_rotation`
  - `coronal_offsets`
  - `sagittal_profile`
- `spine_params`
  - `vertebral_rotation`
  - `coronal_offset`
  - `sagittal_profile`
  - `flexibility`

### 4.4 当前患者状态结构

```json
{
  "id": "PAT-12345",
  "name": "倪欣然",
  "age": 14,
  "gender": "Female",
  "diagnosis": "Scoliosis (Cobb 25°)",
  "spine_params": {
    "vertebral_rotation": [0.1, 0.2],
    "coronal_offset": [1.0, 2.0],
    "sagittal_profile": [10.0, 10.0],
    "flexibility": 0.8
  },
  "cobb_angle": 25.0,
  "metrics": {
    "cobb_angle": 25.0,
    "kyphosis_max": 40.0,
    "lordosis_max": 30.0
  },
  "curve_data": {
    "vertebral_rotation": [0.1, 0.2],
    "coronal_offsets": [1.0, 2.0],
    "sagittal_profile": [10.0, 10.0]
  }
}
```

### 4.5 当前实现中的默认值

以下字段并不是从真实临床数据中提取，而是当前实现中的占位或推导值：

- `age = 14`
- `gender = Female`
- `kyphosis_max = 40.0`
- `lordosis_max = 30.0`
- `spine_params` / `curve_data` 的列表数据

这意味着当前系统对患者状态的要求是“结构完整”，而不是“所有字段都来自真实测量”。

---

## 5. 模拟服务输入

模拟服务是当前最核心的“模型推理”层。

### 5.1 接口输入结构

**接口：** `POST /simulate`

**必填字段：**

- `patient_name`
- `initial_state.metrics`
- `initial_state.curve_data`
- `treatment_plan`

### 5.2 当前真实请求体

```json
{
  "patient_name": "倪欣然",
  "initial_state": {
    "metrics": {
      "cobb_angle": 25.0,
      "kyphosis_max": 40.0,
      "lordosis_max": 30.0
    },
    "curve_data": {
      "vertebral_rotation": [0.1, 0.2],
      "coronal_offsets": [1.0, 2.0],
      "sagittal_profile": [10.0, 10.0]
    }
  },
  "treatment_plan": {
    "type": "Brace",
    "duration": 24,
    "compliance": 0.9
  }
}
```

### 5.3 模拟服务对字段的实际要求

#### metrics

当前实现中至少应包含：

- `cobb_angle`
- `kyphosis_max`
- `lordosis_max`

#### curve_data

当前实现中至少应包含：

- `vertebral_rotation`

建议包含：

- `coronal_offsets`
- `sagittal_profile`

#### treatment_plan

当前实现中使用：

- `type`
- `duration`
- `compliance`

### 5.4 治疗方案含义

- `type`: 治疗类型，如 `Brace`、`PT`、`Intensive`
- `duration`: 月数，服务内部会转为周数
- `compliance`: 依从性，影响干预效果强弱

---

## 6. 可视化服务输入

可视化服务接收模拟结果，而不是原始患者数据。

### 6.1 接口输入结构

**接口：** `POST /render/evolution`

**必填字段：**

- `patient_name`
- `timeline`
- `treatment_plan`

### 6.2 当前真实输入示例

```json
{
  "patient_name": "倪欣然",
  "timeline": [
    {
      "week": 0,
      "control": {
        "metrics": { "cobb_angle": 25.0 },
        "curve_data": { "vertebral_rotation": [0.1, 0.2] }
      },
      "intervention": {
        "metrics": { "cobb_angle": 25.0 },
        "curve_data": { "vertebral_rotation": [0.1, 0.2] }
      },
      "intensive": {
        "metrics": { "cobb_angle": 22.0 },
        "curve_data": { "vertebral_rotation": [0.1, 0.2] }
      }
    }
  ],
  "treatment_plan": {
    "type": "Brace",
    "duration": 24,
    "compliance": 0.9
  }
}
```

### 6.3 可视化依赖的关键内容

为了正确绘图，至少需要：

- 患者名
- 每个时间点的 `week`
- 每组方案下的 `metrics.cobb_angle`

如果要扩展 3D 或更精细曲线图，则还需要：

- `curve_data.vertebral_rotation`
- `curve_data.coronal_offsets`
- `curve_data.sagittal_profile`

---

## 7. 网关编排层输入

网关是业务编排层，不直接做医学计算，但它决定了上游必须提供哪些字段。

### 7.1 生成报告时网关依赖的数据

网关需要：

- 患者服务返回完整患者状态
- 模拟服务返回 `timeline`
- 可视化服务返回图表 JSON

### 7.2 网关最终拼装时使用的关键字段

从患者服务读取：

- `id`
- `metrics`
- `curve_data`

从模拟服务读取：

- `timeline`
- 各阶段 `control/intervention/intensive.metrics.cobb_angle`

从可视化服务读取：

- `data`（完整 Plotly JSON）

---

## 8. 当前项目中“模型真正需要的最小输入”

如果只看当前实现，而不看未来扩展，最小可运行输入如下。

### 8.1 最小 OCR 输入

- 1 个 PDF 文件

### 8.2 最小患者状态输入

- `name`
- `metrics.cobb_angle`
- `metrics.kyphosis_max`
- `metrics.lordosis_max`
- `curve_data.vertebral_rotation`

### 8.3 最小模拟输入

- `patient_name`
- `initial_state.metrics`
- `initial_state.curve_data`
- `treatment_plan.type`
- `treatment_plan.duration`
- `treatment_plan.compliance`

### 8.4 最小可视化输入

- `patient_name`
- `timeline[].week`
- `timeline[].control.metrics.cobb_angle`
- `timeline[].intervention.metrics.cobb_angle`
- `timeline[].intensive.metrics.cobb_angle`
- `treatment_plan`

---

## 9. 若扩展到 X 光 + PDF 联合分析，还需增加哪些输入

如果后续要做更真实的联合建模，建议新增以下输入层。

### 9.1 影像原始输入

- X 光图片文件（JPG / PNG）
- 或 DICOM 文件
- 拍摄位信息（正位 / 侧位）
- 分辨率、像素间距

### 9.2 影像结构化特征

- 椎体关键点
- 冠状面主弯角度
- 胸椎 / 腰椎分段信息
- 骨盆倾斜/旋转
- 自动测得的 Cobb 角
- 影像质量评分

### 9.3 文本上下文输入

- 既往检查时间
- 历史治疗方案
- 医生诊断结论
- 年龄 / 性别 / 生长阶段
- 随访间隔

### 9.4 融合层新增字段

- `data_source`: `pdf` / `xray` / `manual` / `fused`
- `confidence`: 每个字段的置信度
- `conflict_flags`: 文本与影像冲突标记
- `review_required`: 是否需要人工复核

---

## 10. 建议

### 10.1 若仅维持当前版本

建议确保 PDF 至少能稳定提供：

- 姓名
- Cobb 角
- 检查页内容

### 10.2 若要提升模拟可信度

建议把以下字段从“默认值/占位值”改为“真实输入”：

- 年龄
- 性别
- 胸椎后凸 / 腰椎前凸
- 冠状面偏移
- 椎体旋转

### 10.3 若要走向临床级联合分析

建议增加：

- X 光图像上传入口
- 图像关键点检测 / Cobb 角测量服务
- 文本与影像融合的数据模型

---

## 11. 一句话总结

当前项目的核心模型输入，本质上是：

- **PDF 提取出的结构化患者状态**
- **治疗方案参数**

而不是直接基于 X 光图像做建模。若要扩展到“X 光 + PDF 联合分析”，需要额外补齐影像输入、影像特征提取和融合层数据模型。
