# OCR 输出字段说明文档

本文档说明当前项目中 OCR 服务输出了哪些字段、每个字段表示什么、字段从哪里来，以及它们是否被下游服务实际使用。

---

## 1. 文档目的

OCR 服务是当前系统的数据入口之一。它的职责不是直接做医学诊断，而是：

- 从 PDF 医疗报告中提取文本
- 将提取结果保存为 JSON
- 为患者服务提供后续结构化解析的原始数据

因此，OCR 输出字段可以分为两类：

1. **接口响应字段**：网关和前端会直接看到的字段
2. **OCR 提取结果字段**：保存到 `extracted_data/*.json` 中的字段

---

## 2. OCR 服务接口输入

### 2.1 接口

**接口地址：**

```http
POST /ocr/extract
```

### 2.2 输入参数

| 参数名 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `file` | PDF 文件 | 是 | 待识别的 PDF 医疗报告 |
| `save_json` | Boolean | 否 | 是否将提取结果保存为 JSON，默认 `true` |

### 2.3 当前限制

- 仅支持 PDF 文件
- 不支持直接上传 JPG / PNG / DICOM
- 默认重点处理第 6、7、8 页

---

## 3. OCR 接口响应结构

OCR 服务接口最终返回如下结构：

```json
{
  "filename": "sample.pdf",
  "extracted_data": {
    "raw_text": "...",
    "extracted_pages": [
      {
        "page": 6,
        "content": "...",
        "method": "ocr"
      }
    ],
    "note": "使用了 pdfplumber 和/或 RapidOCR 提取。",
    "filename": "sample.pdf"
  },
  "json_path": "D:/workspace/.../sample_extracted.json",
  "status": "success"
}
```

---

## 4. 顶层响应字段说明

### 4.1 `filename`

- **类型**：`string`
- **示例**：`"sample.pdf"`
- **来源**：上传文件的原始文件名
- **含义**：标识当前处理的是哪个 PDF
- **作用**：
  - 便于前端显示
  - 便于生成输出文件名
  - 便于患者服务后续回溯数据来源

---

### 4.2 `extracted_data`

- **类型**：`object`
- **含义**：OCR 提取出的核心结果对象
- **作用**：
  - 作为 OCR 服务的主要业务输出
  - 保存到 `extracted_data/*.json`
  - 被患者服务加载并解析

---

### 4.3 `json_path`

- **类型**：`string`
- **示例**：`"D:/workspace/Digital_Twin_Project/extracted_data/sample_extracted.json"`
- **来源**：服务在本地保存 JSON 后生成
- **含义**：OCR 结果落盘路径
- **作用**：
  - 方便调试
  - 便于患者服务从共享目录读取

---

### 4.4 `status`

- **类型**：`string`
- **常见值**：`"success"`
- **含义**：OCR 任务执行状态
- **作用**：供前端或网关判断流程是否成功

---

## 5. `extracted_data` 内部字段说明

`extracted_data` 是 OCR 的核心结果对象。

### 5.1 `raw_text`

- **类型**：`string`
- **示例**：多页拼接后的长文本
- **来源**：
  - 优先来自 `pdfplumber` 文字层提取
  - 若文字层不足，则来自 RapidOCR 对页面图像的 OCR 结果
- **含义**：
  - 按页拼接后的完整原始文本
  - 是患者服务后续解析姓名、Cobb 角等信息的主要依据
- **当前下游使用情况**：
  - **已使用**
  - 患者服务主要依赖该字段做规则解析

#### 典型内容包含

- 页码标记，如 `--- 第 6 页 (OCR) ---`
- 姓名
- 采集时间
- 数据编号
- Cobb 角相关文本
- 各种测量项原始字符串

---

### 5.2 `extracted_pages`

- **类型**：`array<object>`
- **含义**：逐页保存的提取结果
- **作用**：
  - 便于调试和人工核查
  - 便于后续按页做更细粒度解析

每个元素结构如下：

```json
{
  "page": 6,
  "content": "...",
  "method": "ocr"
}
```

---

#### 5.2.1 `page`

- **类型**：`integer`
- **示例**：`6`
- **含义**：提取自 PDF 的第几页
- **说明**：
  - 当前默认处理页码是第 6、7、8 页
  - 存储的是“人类页码”，不是零基索引

---

#### 5.2.2 `content`

- **类型**：`string`
- **含义**：当前页提取出的文本内容
- **作用**：
  - 便于定位某条识别内容具体来自哪一页
  - 便于后续做按页结构化解析

---

#### 5.2.3 `method`

- **类型**：`string`
- **常见值**：
  - `text_extraction`
  - `ocr`
- **含义**：当前页文本是通过哪种方式得到的

##### 含义说明

| 值 | 说明 |
| --- | --- |
| `text_extraction` | 直接从 PDF 文字层提取 |
| `ocr` | 先把 PDF 页渲染成图片，再做 OCR |

##### 当前价值

- 用于判断识别可靠性
- 用于区分“原始数字文本”与“图像 OCR 文本”

---

### 5.3 `note`

- **类型**：`string`
- **示例**：`"使用了 pdfplumber 和/或 RapidOCR 提取。"`
- **含义**：对提取方式的说明
- **作用**：
  - 便于调试
  - 帮助开发者理解当前结果来源

---

### 5.4 `filename`

- **类型**：`string`
- **示例**：`"sample_medical_record.pdf"`
- **来源**：OCR 服务在提取后补充
- **含义**：原始 PDF 文件名
- **作用**：
  - 患者服务会将其作为候选患者名来源之一
  - 在 OCR 文本姓名识别不可靠时，可用于回退

---

## 6. OCR 结果里“隐含包含”的医学信息

虽然 OCR 当前没有直接输出结构化医学字段，但在 `raw_text` 和 `content` 中，通常会包含这些信息：

### 6.1 患者身份信息

- 姓名
- 编号
- 数据编号

### 6.2 检查时间信息

- 采集时间

### 6.3 脊柱相关测量信息

可能出现但当前未完整结构化解析的内容包括：

- Cobb 角
- 最大后凸角
- 最大前凸角
- 前凸顶点
- 椎体旋转
- 椎体偏移
- 骨盆倾斜
- 骨盆旋转
- 冠状面偏移

### 6.4 原始页面内容

- 第 6 页正文
- 第 7 页正文
- 第 8 页正文

这些内容目前大多还保留在原始文本中，尚未被完整映射成字段。

---

## 7. 当前真正被下游消费的 OCR 字段

患者服务当前并不会完整使用所有 OCR 输出，而是主要消费以下内容：

### 7.1 实际使用字段

| 字段 | 是否被使用 | 用途 |
| --- | --- | --- |
| `raw_text` | 是 | 解析姓名、Cobb 角 |
| `filename` | 是 | 作为患者名后备来源 |
| `extracted_pages` | 否 | 当前主要用于调试和保留原始页内容 |
| `note` | 否 | 仅作说明 |

### 7.2 当前解析器会尝试提取

基于 OCR 文本，患者解析器主要提取：

- `name`
- `cobb_angle`

并进一步生成：

- `metrics`
- `curve_data`
- `spine_params`

也就是说，OCR 输出本身是“原始文本层”，真正的结构化医学字段是在患者服务里生成的。

---

## 8. 当前字段存在的局限性

### 8.1 不是完整结构化医学结果

OCR 结果更接近“文本抽取结果”，不是“医学语义解析结果”。

例如：

- 有“最大后凸角度”字样
- 但没有单独的 `kyphosis_max` OCR 字段
- 最终 `kyphosis_max` 是患者服务中的默认值

### 8.2 识别可能有 OCR 误差

例如姓名可能出现：

- 黄渲渲 -> 黄谊道
- 薛博文 -> 薛博）

所以 OCR 文本不能直接视为高置信度临床数据。

### 8.3 当前页码固定

OCR 默认只处理第 6、7、8 页，这意味着：

- 如果关键数据不在这些页，OCR 可能提不到
- 如果不同医院报告模板差异较大，识别稳定性会下降

### 8.4 不直接识别 X 光图像本身

当前 OCR 只识别图像中的“文字”，不会输出：

- 椎体关键点
- 自动 Cobb 角测量
- 脊柱分割结果
- 影像质量评分

---

## 9. 建议补充的 OCR 结构化字段

如果后续想让 OCR 输出更适合模型直接消费，建议在 OCR 后处理阶段补齐以下字段：

### 9.1 基础结构化字段

- `patient_name`
- `record_id`
- `acquisition_time`
- `exam_date`

### 9.2 脊柱测量字段

- `cobb_angle`
- `kyphosis_max`
- `lordosis_max`
- `vertebral_rotation_avg`
- `vertebral_rotation_max`
- `coronal_offset`
- `pelvic_tilt`
- `pelvic_rotation`

### 9.3 质量与来源字段

- `source_page`
- `source_method`
- `confidence`
- `needs_review`

### 9.4 联合分析扩展字段

如果未来要接 X 光图像分析，建议增加：

- `image_available`
- `image_type`
- `report_text_confidence`
- `fusion_ready`

---

## 10. OCR 字段总表

| 字段路径 | 类型 | 当前是否输出 | 当前是否被下游使用 | 说明 |
| --- | --- | --- | --- | --- |
| `filename` | string | 是 | 是 | 原始 PDF 文件名 |
| `extracted_data` | object | 是 | 是 | OCR 核心结果对象 |
| `json_path` | string | 是 | 否 | 本地 JSON 保存路径 |
| `status` | string | 是 | 否 | OCR 任务状态 |
| `extracted_data.raw_text` | string | 是 | 是 | 拼接后的完整 OCR / 文本提取结果 |
| `extracted_data.extracted_pages` | array | 是 | 否 | 按页保存的提取结果 |
| `extracted_data.extracted_pages[].page` | integer | 是 | 否 | 页码 |
| `extracted_data.extracted_pages[].content` | string | 是 | 否 | 页文本内容 |
| `extracted_data.extracted_pages[].method` | string | 是 | 否 | 提取方式 |
| `extracted_data.note` | string | 是 | 否 | 提取方式说明 |
| `extracted_data.filename` | string | 是 | 是 | 原始文件名的结果内镜像 |

---

## 11. 一句话总结

当前 OCR 服务输出的核心参数，本质上是：

- **原始文件名**
- **完整 OCR 文本**
- **按页提取文本**
- **提取方式说明**

它更像“文本采集层”，而不是“医学结构化分析层”。真正被模型链路消费的关键 OCR 参数，当前主要只有：

- `raw_text`
- `filename`
