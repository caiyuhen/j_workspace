# API 规范文档

## 概述
本文档定义了脊柱数字孪生微服务系统的 RESTful API 接口。

---

## 1. 报告网关 (Report Gateway)
**基础 URL**: `http://localhost:8000`

### 1.1 上传并处理 OCR
*   **端点**: `POST /upload/ocr`
*   **描述**: 上传 PDF 文件，触发 OCR 服务提取，保存数据，并通知患者服务。
*   **请求**: `multipart/form-data`
    *   `file`: PDF 文件
*   **响应**:
    ```json
    {
      "message": "文件已处理且患者数据已更新",
      "ocr_result": {
        "filename": "sample.pdf",
        "extracted_data": { ... },
        "json_path": "path/to/data.json",
        "status": "success"
      }
    }
    ```

### 1.2 生成报告
*   **端点**: `POST /report/generate`
*   **描述**: 编排整个流程（患者 -> 模拟 -> 可视化）以生成综合报告。
*   **请求**:
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
*   **响应**:
    ```json
    {
      "patient_info": { ... },
      "simulation_summary": { ... },
      "evolution_chart_json": { ... }, // 包含 Plotly 动画帧
      "3d_model_url": "http://..."
    }
    ```

---

## 2. 患者服务 (Patient Service)
**基础 URL**: `http://localhost:8003`

### 2.1 获取患者数据
*   **端点**: `GET /patients/{patient_name}`
*   **描述**: 获取解析后的结构化患者数据。
*   **响应**:
    ```json
    {
      "id": "PAT-12345",
      "name": "倪欣然",
      "diagnosis": "Scoliosis (Cobb 25°)",
      "spine_params": {
        "vertebral_rotation": [...],
        "coronal_offset": [...]
      },
      "cobb_angle": 25.0,
      "metrics": { ... },
      "curve_data": { ... }
    }
    ```

---

## 3. 模拟服务 (Simulation Service)
**基础 URL**: `http://localhost:8001`

### 3.1 运行模拟
*   **端点**: `POST /simulate`
*   **描述**: 根据当前状态预测脊柱演变。
*   **请求**:
    ```json
    {
      "current_state": { ... }, // 来自患者服务的输出
      "treatment_plan": {
        "type": "Brace",
        "duration": 24, // 月
        "compliance": 0.9
      }
    }
    ```
*   **响应**:
    ```json
    {
      "summary": {
        "initial_cobb": 25.0,
        "final_cobb": 18.5
      },
      "timeseries_data": {
        "timeline": [
          { "week": 0, "control": {...}, "intervention": {...} },
          { "week": 1, "control": {...}, "intervention": {...} },
          ...
        ]
      }
    }
    ```

---

## 4. 可视化服务 (Visualization Service)
**基础 URL**: `http://localhost:8002`

### 4.1 生成演变图表
*   **端点**: `POST /visualize/evolution`
*   **描述**: 生成带有时间滑块的 Plotly 图表 JSON。
*   **请求**:
    ```json
    {
      "simulation_data": { ... } // 模拟服务的输出
    }
    ```
*   **响应**:
    ```json
    {
      "data": [...],
      "layout": { ... },
      "frames": [...] // 动画帧数据
    }
    ```

---

## 5. OCR 服务 (OCR Service)
**基础 URL**: `http://localhost:8004`

### 5.1 提取文本
*   **端点**: `POST /ocr/extract`
*   **描述**: 上传 PDF 并提取关键文本数据。
*   **请求**: `multipart/form-data`
    *   `file`: PDF 文件
*   **响应**:
    ```json
    {
      "filename": "sample.pdf",
      "extracted_data": {
        "raw_text": "...",
        "extracted_pages": [...]
      },
      "json_path": "path/to/data.json",
      "status": "success"
    }
    ```
      ]
    }
    ```

---

## 4. 可视化服务 (Visualization Service)
**基础 URL**: `http://localhost:8001`

### 4.1 生成可视化
*   **端点**: `POST /visualize`
*   **描述**: 将模拟数据转换为图表配置（Plotly JSON）。
*   **请求**:
    ```json
    {
      "simulation_result": { ... } // 来自模拟服务的输出
    }
    ```
*   **响应**:
    ```json
    {
      "evolution_chart_json": { "data": [...], "layout": [...] },
      "3d_model_url": "http://placeholder..."
    }
    ```

---

## 5. OCR 服务 (OCR Service)
**基础 URL**: `http://localhost:8004`

### 5.1 提取 PDF 内容
*   **端点**: `POST /extract/pdf`
*   **描述**: 接收 PDF，提取文本（针对特定页面），返回结构化结果。
*   **请求**: `multipart/form-data`
    *   `file`: PDF 文件
*   **响应**:
    ```json
    {
      "raw_text": "Full extracted text content...",
      "extracted_pages": [
        { "page": 6, "content": "..." }
      ]
    }
    ```
