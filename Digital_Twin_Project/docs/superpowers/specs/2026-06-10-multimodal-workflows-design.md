# 三种工作流实现设计

## 1. 背景

当前项目已经具备基于 PDF 的基础工作流：

1. 通过网关上传 PDF
2. OCR 服务提取文本
3. 患者服务解析文本并生成患者状态
4. 模拟服务生成演变时间序列
5. 可视化服务输出 3D Plotly 图和趋势图

本次目标是在现有微服务框架下扩展三种工作流：

1. PDF-only
2. X 光-only
3. X 光 + PDF 联合分析

本次实现采用工程可用版策略：

- 保持现有 PDF 流程兼容
- 新增 X 光分析服务
- 支持 JPG、PNG、DICOM 输入
- 使用轻量规则和基础图像处理生成统一患者状态
- 复用现有模拟和可视化链路
- 不在本次实现中引入重型医学 AI 模型或高精度临床级 Cobb 自动测量

## 2. 目标与非目标

### 2.1 目标

- 在现有项目框架内实现三种工作流的统一入口
- 为 X 光-only 和 X 光 + PDF 场景提供可运行的后端链路
- 在前端增加工作流选择、文件上传和结果展示入口
- 将三种输入统一转换为 `patient_state` / `initial_state`
- 复用现有模拟与 3D 可视化能力

### 2.2 非目标

- 不实现医疗级精度的影像诊断
- 不实现完整 DICOM 序列三维重建
- 不重写现有前端技术栈
- 不替换现有模拟和可视化服务核心逻辑

## 3. 用户场景

### 3.1 PDF-only

用户上传 PDF，系统通过 OCR 提取文本，生成患者状态，运行模拟，输出 3D 图和对比结果。

### 3.2 X 光-only

用户上传 X 光图片或 DICOM，系统提取基础影像特征，生成患者状态，运行模拟，输出 3D 图和对比结果。

### 3.3 X 光 + PDF

用户同时上传 PDF 和 X 光，系统分别提取文本和影像特征，融合后生成患者状态，运行模拟，输出 3D 图和对比结果。

## 4. 总体设计

### 4.1 架构变化

新增一个独立微服务：

- `xray-analysis-service`

扩展一个现有服务：

- `report-gateway`

复用现有服务：

- `ocr-service`
- `patient-service`
- `simulation-service`
- `visualization-service`

### 4.2 核心原则

- 输入多态，内部模型统一
- 网关负责编排，不承载重计算
- X 光分析服务负责图像读取和基础特征抽取
- 最终一律收敛为统一的 `patient_state`

## 5. 数据流设计

### 5.1 统一入口

网关新增统一接口：

- `POST /workflow/analyze`

请求采用 `multipart/form-data`，支持以下字段：

- `workflow_type`: `pdf_only` / `xray_only` / `multimodal`
- `pdf_file`: 可选
- `xray_file`: 可选
- `patient_name`: 可选
- `treatment_type`
- `duration`
- `compliance`

### 5.2 PDF-only 数据流

1. 网关接收 `workflow_type=pdf_only`
2. 网关调用 OCR 服务提取 PDF 文本
3. 网关触发患者服务重新加载或直接调用解析逻辑
4. 网关获取患者状态
5. 网关调用模拟服务
6. 网关调用可视化服务
7. 网关返回最终报告

### 5.3 X 光-only 数据流

1. 网关接收 `workflow_type=xray_only`
2. 网关将 X 光文件发送给 X 光分析服务
3. X 光分析服务返回结构化 `patient_state`
4. 网关构造模拟请求
5. 网关调用模拟服务
6. 网关调用可视化服务
7. 网关返回最终报告

### 5.4 X 光 + PDF 数据流

1. 网关接收 `workflow_type=multimodal`
2. 网关并行调用 OCR 服务和 X 光分析服务
3. 网关对文本结果和影像结果做轻量融合
4. 生成统一 `patient_state`
5. 调用模拟服务
6. 调用可视化服务
7. 返回最终报告

## 6. 新增服务设计

### 6.1 服务名称

- `services/xray-analysis-service`

### 6.2 接口

#### `POST /xray/analyze`

输入：

- `file`: JPG / PNG / DICOM
- `patient_name`: 可选

输出：

```json
{
  "status": "success",
  "patient_state": {
    "name": "匿名患者001",
    "data_source": "xray",
    "metrics": {
      "cobb_angle": 24.0,
      "kyphosis_max": 35.0,
      "lordosis_max": 30.0
    },
    "curve_data": {
      "vertebral_rotation": [1.0, 2.0, 3.0],
      "coronal_offsets": [2.0, 7.0, 11.0],
      "sagittal_profile": [9.0, 15.0, 12.0]
    },
    "confidence": {
      "cobb_angle": 0.65
    },
    "review_required": false
  }
}
```

#### `GET /health`

返回服务健康状态。

### 6.3 实现策略

X 光工程可用版不做复杂 AI 识别，采用以下流程：

1. 文件读取
2. 图像归一化
3. 灰度化和对比度增强
4. 前景区域估计
5. 估计脊柱中心线和弯曲趋势
6. 生成近似 `cobb_angle`、`coronal_offsets`、`sagittal_profile`
7. 根据偏移强度推导简化 `vertebral_rotation`

### 6.4 DICOM 支持策略

- 若环境可用 `pydicom`，优先读取 DICOM 像素数据
- 若 DICOM 解码失败，接口返回明确错误
- 本次只支持单张 DICOM 图像，不处理序列体数据

## 7. 融合策略设计

### 7.1 融合位置

融合逻辑放在 `report-gateway`，避免引入第二个新服务。

### 7.2 融合规则

- 姓名优先级：显式输入 > OCR 解析 > X 光默认匿名名
- `cobb_angle`：若 OCR 与 X 光都存在，取平均或优先采用高置信来源
- `kyphosis_max` / `lordosis_max`：优先采用 X 光结果，缺失时退回默认值
- `curve_data`：优先采用 X 光结果
- 记录：
  - `data_source`
  - `confidence`
  - `review_required`

### 7.3 冲突规则

若 OCR 与 X 光 `cobb_angle` 差值超过阈值，例如 8 度：

- `review_required = true`
- 在响应 summary 中提示存在模态冲突

## 8. 网关改造设计

### 8.1 新增接口

#### `POST /workflow/analyze`

统一接收三种工作流输入并编排后续处理。

### 8.2 保留现有接口

继续保留：

- `POST /upload/ocr`
- `POST /report/generate`
- `GET /patients`
- `GET /health`

### 8.3 新接口返回结构

```json
{
  "workflow_type": "multimodal",
  "patient_state": {},
  "simulation_id": "sim-123",
  "evolution_chart_json": {},
  "comparison_data": {},
  "summary": "已完成联合分析",
  "review_required": false
}
```

## 9. 前端改造设计

### 9.1 修改文件

- `services/report-gateway/src/static/index.html`

### 9.2 新增交互元素

- 工作流类型选择器
- PDF 上传控件
- X 光上传控件
- 可选患者姓名输入
- 根据工作流动态显示所需文件输入项

### 9.3 前端行为

- 选择工作流后，显示对应输入项
- 统一调用 `/workflow/analyze`
- 成功后渲染 3D Plotly 图
- 显示对比表格和工作流摘要
- 若 `review_required=true`，在界面上高亮提醒

## 10. 统一数据模型

### 10.1 patient_state

统一内部模型如下：

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

### 10.2 模拟输入适配

网关将 `patient_state` 转换成现有模拟服务可接受的：

```json
{
  "patient_name": "患者A",
  "initial_state": {
    "metrics": {},
    "curve_data": {}
  },
  "treatment_plan": {}
}
```

## 11. 错误处理

### 11.1 PDF-only

- 未上传 PDF：返回 400
- OCR 失败：返回 502 或 500
- 未解析到患者：返回 404

### 11.2 X 光-only

- 未上传 X 光：返回 400
- 文件格式不支持：返回 400
- DICOM 读取失败：返回 422
- X 光特征提取失败：返回 500

### 11.3 X 光 + PDF

- 缺少任一必要文件：返回 400
- 任一子流程失败：返回明确错误源
- 融合冲突不阻断流程，但标记 `review_required`

## 12. 测试策略

### 12.1 后端

- X 光分析服务单元测试
- 网关三种工作流接口测试
- 模拟链路集成测试

### 12.2 前端

- 工作流切换显示逻辑
- 表单校验
- 统一上传提交逻辑
- 成功和失败提示渲染

### 12.3 验证重点

- 三种工作流都能返回图表 JSON
- 现有 PDF-only 工作流不回归
- X 光-only 和 multimodal 都能进入模拟与可视化

## 13. 实施顺序

1. 新增 `xray-analysis-service`
2. 扩展网关统一接口与融合逻辑
3. 扩展前端页面
4. 补充测试
5. 端到端验证三种工作流

## 14. 风险

- 当前 X 光分析为工程近似，不代表临床精度
- DICOM 解析受依赖库和样本格式影响较大
- 如果输入图像质量过差，生成的 `patient_state` 置信度有限

## 15. 交付标准

- 三种工作流可通过前端完成提交
- 三种工作流都能获得模拟结果和 3D 图
- 网关返回统一结构结果
- 现有 PDF 工作流继续可用
