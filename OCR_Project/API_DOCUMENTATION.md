# OCR Microservice API Documentation / OCR 微服务接口说明

This document provides details on the OCR microservice interface for medical report recognition.
本文档提供了用于医疗报告识别的 OCR 微服务接口详细信息。

---

## 1. OCR Recognition Endpoint / OCR 识别接口

**URL:** `/ocr`
**Method:** `POST`
**Content-Type:** `multipart/form-data`

### Request Parameters / 请求参数

| Parameter Name / 参数名 | Type / 类型 | Required / 必填 | Description / 描述 |
| :--- | :--- | :--- | :--- |
| `file` | File (Binary) | Yes / 是 | The image file of the medical report (JPG, PNG). <br> 医疗报告的图片文件 (JPG, PNG)。 |

### Response Structure / 响应结构

The response is a JSON object containing the structured data extracted from the image.
响应是一个包含从图像中提取的结构化数据的 JSON 对象。

```json
{
  "status": "success",
  "filename": "output_filename.json",
  "result_file": "path/to/output_filename.json",
  "test_name": "Internal test name / 内部检测名称",
  "patient_name": "Internal patient name / 内部患者姓名",
  "check_date": "Internal check date / 内部检查日期",
  "idhao": "Patient ID / 病人ID",
  "yangben": "Sample / 样本",
  "xingming": "Patient Name / 姓名",
  "baogaoTime": "Report Time / 报告时间",
  "biaobentype": "Sample Type / 标本类型",
  "yiyuan": "Hospital Name / 医院名称",
  "jianyanTime": "Test Date / 检验日期",
  "zhuyuanhao": "Admission No / 住院号",
  "sex": "Gender / 性别",
  "fangfa": "Method / 方法",
  "diagnosis": "Diagnosis info (Prescription only) / 诊断信息 (仅处方)",
  "details": [
    {
      "parameter": "Raw Item Name / 原始项目名",
      "value": "Raw Value / 原始结果值",
      "unit": "Raw Unit / 原始单位",
      "reference_range": "Raw Reference Range / 原始参考区间",
      "result_status": "Raw Status / 原始状态",
      "project_zh": "Item Name (Chinese) / 项目中文",
      "daihaos": "Item Code / 项目代号",
      "result": "Value / 结果",
      "reference": "Reference Range / 参考值",
      "minReference": "Min Reference Value / 最小参考值",
      "maxReference": "Max Reference Value / 最大参考值",
      "tishi": "Status (正常/偏高/偏低) / 提示",
      "usage": "Usage (Prescription only) / 用法 (仅处方)"
    }
  ],
  "results": [
    {
      "project_zh": "Item Name (Chinese) / 项目中文",
      "daihaos": "Item Code / 项目代号",
      "result": "Value / 结果",
      "unit": "Unit / 单位",
      "reference": "Reference Range / 参考值",
      "minReference": "Min Reference Value / 最小参考值",
      "maxReference": "Max Reference Value / 最大参考值",
      "tishi": "Status (正常/偏高/偏低) / 提示",
      "usage": "Usage (Prescription only) / 用法 (仅处方)"
    }
  ],
  "debug_info": { ... }
}
```

### Field Descriptions / 字段说明

| Field / 字段 | Type / 类型 | Description / 描述 |
| :--- | :--- | :--- |
| `status` | string | Status of the request (e.g., "success"). <br> 请求状态。 |
| `test_name` | string | Internal parsed test name (may include OCR noise in difficult scans). <br> 内部解析的检验名称（复杂场景可能有 OCR 噪声）。 |
| `patient_name` | string | Internal parsed patient name. <br> 内部解析的患者姓名。 |
| `check_date` | string | Internal parsed check date. <br> 内部解析的检查日期。 |
| `idhao` | string | Patient ID. <br> 病人ID。 |
| `yangben` | string | Sample identifier/barcode. <br> 样本编号/条码。 |
| `xingming` | string | Name of the patient. <br> 患者姓名。 |
| `baogaoTime` | string | Report generation time. <br> 报告时间。 |
| `biaobentype` | string | Type of sample (e.g., Blood, Urine). <br> 标本类型（如血液、尿液）。 |
| `yiyuan` | string | Hospital Name. <br> 医院名称。 |
| `jianyanTime` | string | Test execution date. <br> 检验日期。 |
| `zhuyuanhao` | string | Inpatient Admission Number. <br> 住院号。 |
| `sex` | string | Patient Gender. <br> 性别。 |
| `fangfa` | string | Testing Method. <br> 检验方法。 |
| `diagnosis` | string | (Optional) Clinical diagnosis extracted from prescriptions. <br> (可选) 从处方中提取的临床诊断。 |
| `details` | list | Detailed raw+normalized items (same records as `results`, with extra raw fields). <br> 明细列表（与 `results` 为同一组记录，包含更多原始字段）。 |
| `results` | list | List of structured result items. <br> 结构化结果项列表。 |
| `details[].parameter` | string | Raw item name recognized from OCR. <br> OCR 识别出的原始项目名。 |
| `details[].value` | string | Raw value recognized from OCR. <br> OCR 识别出的原始结果值。 |
| `details[].unit` | string | Raw unit recognized from OCR. <br> OCR 识别出的原始单位。 |
| `details[].reference_range` | string | Raw reference range recognized from OCR. <br> OCR 识别出的原始参考区间。 |
| `details[].result_status` | string | Raw status value before final normalization. <br> 归一化前的原始状态值。 |
| `results[].project_zh` | string | Chinese Name of the inspection item. <br> 检查项目中文名称。 |
| `results[].daihaos` | string | Code/Abbreviation of the item (e.g., WBC). <br> 项目代号/缩写。 |
| `results[].result` | string | Measured value. <br> 测量结果。 |
| `results[].unit` | string | Unit of measurement. <br> 测量单位。 |
| `results[].reference` | string | Reference range for the item. <br> 参考值。 |
| `results[].minReference` | string | Minimum reference value extracted from range. <br> 提取的最小参考值。 |
| `results[].maxReference` | string | Maximum reference value extracted from range. <br> 提取的最大参考值。 |
| `results[].tishi` | string | Status judgment: "正常" (Normal), "偏高" (High), "偏低" (Low). <br> 提示：正常、偏高、偏低。 |
| `results[].usage` | string | (Optional) Usage instructions for drugs (Prescription only). <br> (可选) 药品用法说明（仅处方）。 |

---

## 2. Example / 示例

### Request (cURL) / 请求示例

```bash
curl -X POST "http://localhost:9080/ocr" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/medical_report.jpg"
```

### Response Example / 响应示例

```json
{
    "status": "success",
    "filename": "blood_test_1731234567_abc123.json",
    "result_file": "d:\\workspace\\OCR_Project\\output\\blood_test_1731234567_abc123.json",
    "test_name": "医学检查报告",
    "patient_name": "张三",
    "check_date": "2024-10-28 07:53",
    "idhao": "12345678",
    "yangben": "112233",
    "xingming": "张三",
    "baogaoTime": "2024-10-28 08:30",
    "biaobentype": "全血",
    "yiyuan": "北京协和医院",
    "jianyanTime": "2024-10-28 07:53",
    "zhuyuanhao": "87654321",
    "sex": "男",
    "fangfa": "仪器法",
    "details": [
        {
            "parameter": "白细胞计数",
            "value": "10.66",
            "unit": "10^9/L",
            "reference_range": "3.5-9.5",
            "result_status": "偏高",
            "project_zh": "白细胞计数",
            "daihaos": "WBC",
            "result": "10.66",
            "unit": "10^9/L",
            "reference": "3.5-9.5",
            "minReference": "3.5",
            "maxReference": "9.5",
            "tishi": "偏高"
        }
    ],
    "results": [
        {
            "project_zh": "白细胞计数",
            "daihaos": "WBC",
            "result": "10.66",
            "unit": "10^9/L",
            "reference": "3.5-9.5",
            "minReference": "3.5",
            "maxReference": "9.5",
            "tishi": "偏高"
        },
        {
            "project_zh": "红细胞计数",
            "daihaos": "RBC",
            "result": "4.06",
            "unit": "10^12/L",
            "reference": "4.3-5.8",
            "minReference": "4.3",
            "maxReference": "5.8",
            "tishi": "偏低"
        }
    ],
    "debug_info": {}
}
```

---

## 3. Notes / 注意事项

1.  **Supported Formats / 支持格式**:
    *   The service supports standard image formats like JPG, PNG.
    *   支持常见的图像格式，如 JPG, PNG。

2.  **Output Location / 输出位置**:
    *   Processed JSON files are saved in the `output/` directory on the server.
    *   处理后的 JSON 文件保存在服务器的 `output/` 目录下。

3.  **Prescription Mode / 处方模式**:
    *   If the image is identified as a prescription, the `diagnosis` field will be populated, and `usage` instructions may be included in the results.
    *   如果图像被识别为处方，`diagnosis` 字段将被填充，且结果中可能包含 `usage` 用法说明。

4.  **Reference Range Split / 参考区间拆分**:
    *   The service automatically splits ranges like `0.00~0.93`, `45-376`, `45--376` into `minReference` / `maxReference`.
    *   服务会自动将 `0.00~0.93`、`45-376`、`45--376` 等区间拆分为 `minReference` / `maxReference`。
