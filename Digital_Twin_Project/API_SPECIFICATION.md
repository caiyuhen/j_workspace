# 脊柱数字孪生 - API 接口规范 (API Specification)

本文档定义了微服务架构下各服务的 RESTful API 接口。

## 1. 患者数据服务 (Patient Digital Twin Service)

### 1.1 获取患者列表
*   **GET** `/api/v1/patients`
*   **Parameters**: `page` (int), `limit` (int), `search` (string)
*   **Response**: `200 OK`
    ```json
    {
      "items": [
        { "id": "uuid", "name": "张三", "age": 14 }
      ],
      "total": 100
    }
    ```

### 1.2 获取患者详情
*   **GET** `/api/v1/patients/{id}`
*   **Response**: `200 OK` (PatientProfile + SpineMetrics)

### 1.3 上传影像数据
*   **POST** `/api/v1/patients/{id}/images`
*   **Body**: `multipart/form-data` (image/png, image/jpeg, application/pdf)
*   **Response**: `201 Created` (ImageID, OCR Status)

---

## 2. 治疗模拟服务 (Treatment Simulation Service)

### 2.1 运行单次模拟
*   **POST** `/api/v1/simulation/run`
*   **Body**: `SimulationRequest` (见 DATA_MODELS.md)
*   **Response**: `200 OK` (SimulationResult)
    *   此接口是**同步**的，适用于快速计算（如 < 5秒）。

### 2.2 提交长时间模拟任务
*   **POST** `/api/v1/simulation/batch`
*   **Body**: `BatchSimulationRequest` (包含多个 Patient IDs)
*   **Response**: `202 Accepted` (TaskID)

### 2.3 查询模拟任务状态
*   **GET** `/api/v1/simulation/tasks/{task_id}`
*   **Response**: `200 OK`
    ```json
    {
      "status": "processing",
      "progress": 45,
      "estimated_remaining": "10s"
    }
    ```

---

## 3. 可视化渲染服务 (Visualization & Rendering Service)

### 3.1 生成演变趋势图 (HTML/JSON)
*   **POST** `/api/v1/visualization/evolution-chart`
*   **Body**: `RenderRequest`
*   **Response**: `200 OK` (Plotly JSON / HTML Fragment)

### 3.2 生成 3D 脊柱模型
*   **POST** `/api/v1/visualization/3d-model`
*   **Body**: `SpineMetrics`
*   **Response**: `200 OK` (Mesh Data / Three.js JSON)

---

## 4. 报告与编排服务 (Report Gateway / BFF)

### 4.1 生成完整报告
*   **POST** `/api/v1/reports/full-report`
*   **Body**: `{ "patient_id": "uuid", "plan_type": "Brace" }`
*   **Response**: `200 OK` (HTML Document URL)

此接口将协调上述服务：
1.  调用 **Patient Service** 获取最新 `SpineMetrics`。
2.  调用 **Simulation Service** 获取 96 周预测数据。
3.  调用 **Visualization Service** 将预测数据渲染为图表和 3D 模型。
4.  组装 HTML 并返回。
