# X光 + PDF / 单模态分析工作流说明

本文档说明项目在以下三种场景下的完整工作流：

1. X 光 + PDF 联合分析
2. 仅 X 光分析
3. 仅 PDF 分析

文档同时区分：

- 当前项目已经支持的部分
- 还需要补充的模块
- 最终如何生成 3D 图并完成报告工作流

---

## 1. 结论总览

### 1.1 是否可以做

| 场景 | 是否理论可行 | 当前项目是否已完整支持 | 说明 |
| --- | --- | --- | --- |
| X 光 + PDF 联合分析 | 是 | 否 | 需要新增 X 光分析服务和融合层 |
| 仅 X 光分析 | 是 | 否 | 需要新增 X 光上传、测量、结构化解析 |
| 仅 PDF 分析 | 是 | 是，但为基础版 | 当前项目已经具备 OCR -> 患者解析 -> 模拟 -> 可视化链路 |

### 1.2 当前项目真实状态

当前项目已经具备以下能力：

- 上传 PDF
- OCR 提取文字
- 从 OCR 文本中解析姓名、Cobb 角等基础信息
- 生成结构化患者状态
- 运行脊柱演变模拟
- 生成 Plotly 交互式 3D 演变图

当前项目尚不具备以下能力：

- 直接上传 X 光图片或 DICOM 进入主流程
- 从 X 光中自动提取椎体关键点、分割结果、Cobb 角
- 融合 X 光特征与 PDF 文本特征

---

## 2. 当前系统已具备的通用后半段流程

不论输入来自 PDF、X 光，还是两者融合，只要能形成统一的结构化患者状态，后半段流程都可以复用：

1. 构建 `patient_state`
2. 调用模拟服务生成 `timeline`
3. 调用可视化服务生成 3D 图和趋势图
4. 返回最终报告 JSON

也就是说，项目现在缺的主要是“前半段数据入口与结构化转换”，不是“后半段模拟与可视化”。

---

## 3. 场景一：X 光 + PDF 联合分析

### 3.1 场景目标

同时利用：

- **PDF 文本** 提供病史、诊断、检查时间、历史治疗方案
- **X 光影像** 提供脊柱形态、冠状面偏移、旋转、Cobb 角测量

最终输出：

- 融合后的患者状态
- 演变模拟结果
- 3D 脊柱图
- 最终报告

### 3.2 推荐完整工作流

#### 第一步：输入采集

用户上传：

- PDF 报告
- X 光图像（JPG / PNG / DICOM）
- 可选人工补充信息
  - 年龄
  - 性别
  - 检查日期
  - 治疗方案

#### 第二步：PDF 处理

通过 OCR 服务提取：

- 姓名
- 检查时间
- 报告编号
- 医生诊断文本
- Cobb 角及相关文字描述
- 椎体旋转 / 骨盆倾斜 / 冠状面偏移等文本项

#### 第三步：X 光处理

新增 X 光分析服务，对影像提取：

- 椎体关键点
- 冠状面主弯
- 自动测量 Cobb 角
- 冠状面偏移
- 矢状面轮廓
- 骨盆倾斜 / 骨盆旋转
- 图像质量评分

#### 第四步：融合处理

新增“融合层”将 PDF 与 X 光结果合并为统一 `patient_state`：

- 若 PDF 与 X 光测得的 Cobb 角接近，则自动融合
- 若差异较大，则打上 `review_required`
- 为每个字段记录：
  - `value`
  - `source`
  - `confidence`

#### 第五步：患者状态生成

融合后输出统一结构，例如：

```json
{
  "name": "倪欣然",
  "data_source": "fused",
  "metrics": {
    "cobb_angle": 25.0,
    "kyphosis_max": 38.0,
    "lordosis_max": 28.0
  },
  "curve_data": {
    "vertebral_rotation": [1.2, 1.8, 2.1],
    "coronal_offsets": [3.0, 8.0, 12.0],
    "sagittal_profile": [10.0, 18.0, 12.0]
  },
  "confidence": {
    "cobb_angle": 0.93
  },
  "review_required": false
}
```

#### 第六步：模拟分析

将融合后的 `patient_state` + `treatment_plan` 发送到模拟服务：

- 生成自然发展轨迹
- 生成常规干预轨迹
- 生成强化干预轨迹

#### 第七步：3D 图生成

可视化服务基于模拟时间序列生成：

- 3D 脊柱骨格图
- 时间滑块动画
- Cobb 角趋势图
- 后凸角趋势图

#### 第八步：最终报告输出

网关返回：

- 患者信息
- 模拟结果摘要
- 对比数据
- 3D 图表 JSON
- 是否需要人工复核

### 3.3 本场景当前缺少的模块

要实现该工作流，当前项目至少还需要新增：

- X 光上传接口
- X 光分析服务
- 多模态融合服务或融合模块
- 统一置信度模型
- 冲突检测机制

### 3.4 本场景的价值

- 比仅 PDF 更稳，因为 OCR 文本可能有误识别
- 比仅 X 光更完整，因为 PDF 有临床上下文
- 更适合做临床辅助分析和报告生成

---

## 4. 场景二：没有 PDF，只通过 X 光分析并生成 3D 图

### 4.1 是否可行

可行，但当前项目还没有 X 光入口和影像解析模块，因此**现在不能直接运行**。

### 4.2 推荐完整工作流

#### 第一步：输入采集

用户上传：

- X 光正位图
- 可选 X 光侧位图
- 或 DICOM 数据

可选人工补充：

- 姓名
- 年龄
- 性别
- 检查日期

#### 第二步：影像分析

X 光分析服务输出：

- `patient_name` 或匿名 ID
- `metrics.cobb_angle`
- `metrics.kyphosis_max`
- `metrics.lordosis_max`
- `curve_data.vertebral_rotation`
- `curve_data.coronal_offsets`
- `curve_data.sagittal_profile`

#### 第三步：生成统一患者状态

影像服务直接构造可被现有模拟服务接受的结构：

```json
{
  "patient_name": "匿名患者001",
  "initial_state": {
    "metrics": {
      "cobb_angle": 27.0,
      "kyphosis_max": 35.0,
      "lordosis_max": 30.0
    },
    "curve_data": {
      "vertebral_rotation": [0.8, 1.2, 1.7],
      "coronal_offsets": [4.0, 10.0, 15.0],
      "sagittal_profile": [8.0, 16.0, 11.0]
    }
  },
  "treatment_plan": {
    "type": "Brace",
    "duration": 24,
    "compliance": 0.85
  }
}
```

#### 第四步：模拟演变

直接复用当前 `/simulate`：

- 根据 X 光提取的初始结构生成时间演变

#### 第五步：3D 图生成

直接复用当前 `/render/evolution`：

- 生成交互式 3D 脊柱图
- 生成趋势曲线和时间滑块

#### 第六步：最终报告输出

输出内容包含：

- X 光测量摘要
- 模拟结果
- 3D 图表 JSON
- 干预方案对比

### 4.3 本场景当前缺少的模块

- X 光上传入口
- 图像预处理
- 关键点检测 / 分割 / 角度测量
- X 光结构化结果转 `initial_state` 的适配器

### 4.4 本场景的特点

- 优点：不依赖 PDF，可直接分析影像
- 风险：缺少病史、医生文本结论和历史上下文
- 适合：快速评估、单次检查分析、演变模拟入口

---

## 5. 场景三：没有 X 光，只通过 PDF 分析并生成 3D 图

### 5.1 是否可行

可行，而且这就是当前项目已经实现的主流程。

### 5.2 当前实际工作流

#### 第一步：用户上传 PDF

前端或调用方上传 PDF 到网关：

```http
POST /upload/ocr
```

#### 第二步：OCR 提取文本

OCR 服务从 PDF 提取：

- `raw_text`
- `extracted_pages`
- `filename`

#### 第三步：患者解析

患者服务基于 OCR 文本解析：

- 姓名
- Cobb 角

并补齐为完整患者状态：

- `metrics`
- `curve_data`
- `spine_params`

#### 第四步：报告生成请求

用户提交：

- `patient_name`
- `treatment_plan`

到：

```http
POST /report/generate
```

#### 第五步：模拟服务生成时间序列

网关将患者状态发送给模拟服务，生成：

- 自然发展
- 常规干预
- 强化干预

#### 第六步：可视化服务生成 3D 图

可视化服务基于 `timeline` 生成：

- 三组 3D 脊柱骨格图
- 时间滑块动画
- Cobb 角对比趋势图
- 后凸角对比趋势图

#### 第七步：最终响应

网关返回：

- `patient_id`
- `simulation_id`
- `evolution_chart_json`
- `comparison_data`
- `summary`

### 5.3 本场景当前限制

虽然已经可用，但它仍属于“基础版”流程，限制包括：

- 依赖 OCR 文本质量
- 目前主要只稳定解析姓名、Cobb 角
- 年龄、性别、后凸角、前凸角等很多字段仍是默认值或推导值
- 没有真正读取 X 光图像本身

### 5.4 本场景的适用性

- 适合快速打通从 PDF 到报告的完整演示链路
- 适合报告驱动的数据录入
- 不适合替代真正的影像级诊断

---

## 6. 三种工作流的统一架构建议

为了同时支持三种场景，建议把系统输入层改造成“多入口、统一中台”的模式。

### 6.1 推荐新增模块

#### 输入层

- `pdf-ingestion`
- `xray-ingestion`
- `manual-input`

#### 解析层

- `ocr-service`
- `xray-analysis-service`
- `text-structuring-service`

#### 融合层

- `multimodal-fusion-service`

#### 复用层

- `patient-service`
- `simulation-service`
- `visualization-service`
- `report-gateway`

### 6.2 统一数据模型

三种输入最终都收敛到统一 `patient_state`：

```json
{
  "name": "患者A",
  "data_source": "pdf | xray | fused",
  "metrics": {
    "cobb_angle": 25.0,
    "kyphosis_max": 38.0,
    "lordosis_max": 30.0
  },
  "curve_data": {
    "vertebral_rotation": [1.0, 2.0, 3.0],
    "coronal_offsets": [2.0, 6.0, 10.0],
    "sagittal_profile": [9.0, 15.0, 11.0]
  },
  "confidence": {
    "cobb_angle": 0.9
  },
  "review_required": false
}
```

只要满足这个统一结构，后续模拟和可视化就不需要关心数据究竟来自 PDF、X 光还是融合结果。

---

## 7. 最终工作流建议

### 7.1 最优方案

优先支持：

1. PDF-only
2. X光-only
3. X光 + PDF fused

原因是：

- PDF-only 最容易延续现有系统
- X光-only 可以最快补齐“影像直连”
- 两者打通后再做 fused 成本最低

### 7.2 实施顺序建议

第一阶段：

- 保持现有 PDF 流程可用
- 提升 OCR 结构化字段提取

第二阶段：

- 新增 X 光上传和影像测量服务
- 让 X 光结果可直接转成 `patient_state`

第三阶段：

- 引入 PDF + X 光 融合层
- 增加置信度和人工复核机制

第四阶段：

- 优化 3D 模型表现
- 输出真正的 3D 模型文件（GLB / OBJ），而不仅是 Plotly 图表

---

## 8. 一句话总结

### 8.1 X 光 + PDF 联合分析

可以做，但当前项目还缺 X 光解析和融合层。

### 8.2 只有 X 光

可以做，但当前项目还缺 X 光上传和影像测量服务；一旦能输出统一 `patient_state`，现有模拟和 3D 图流程即可复用。

### 8.3 只有 PDF

已经可以做，这就是当前项目现有主流程；但它本质上还是“文本驱动 + 规则补齐”的基础版工作流。

---

## 9. 当前实现状态

- PDF-only: 已实现
- X光-only: 已实现（工程可用版）
- X光 + PDF: 已实现（轻量融合版）

### 9.1 本次实现包含

- 新增 `xray-analysis-service`
- 网关新增统一接口 `POST /workflow/analyze`
- 前端支持三种工作流切换和统一提交流程
- 备用启动脚本已纳入 X 光服务与 `XRAY_SERVICE_URL`

### 9.2 当前实现边界

- X 光分析仍是工程近似版，不代表临床级自动测量
- DICOM 当前只支持单张图像读取，不支持序列三维重建
- PDF 与 X 光联合分析采用轻量融合规则，不包含复杂学习型融合模型

### 9.3 联调现状

- 当前联调使用 `run_multimodal_smoke_checks.py`
- 真实 DICOM 样本联调待用户补充 `.dcm` 样本后执行
- X 光增强版输出 `image_quality_score` 与 `analysis_meta`
