# DICOM/PACS 数据接入与 Staging 运维手册

## 1. 系统架构概述
本平台针对医疗影像数据（DICOM/PACS），采用了先进的 **双通道（Dual-Stream）架构** 接入方案：
- **文件数据流（File Stream）**：专门用于传输和脱敏厚重的 DICOM 影像矩阵文件，处理后落地至对象存储（MinIO 或等效分布式存储）。
- **结构化元数据流（Metadata Stream）**：利用 `pydicom` 轻量级抽提患者信息与检查指标，清洗后落地至核心数据库 Staging 层的 `StagingObservation` / `Measurement` 表。

---

## 2. 数据接入规范与联调指南

### 2.1 接口端点 (Endpoint)
- **URL**: `POST /api/v1/dicom/upload`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (接受 `.dcm` 后缀的二进制影像文件)

### 2.2 接入处理流水线说明
当院内 PACS 系统将影像推送到该接口后，平台会通过 FastApi 的 `BackgroundTasks` 执行以下操作：
1. **轻量级加载**: 通过 `stop_before_pixels=True` 参数，仅加载 DICOM Header 进内存，避免 OOM。
2. **强制脱敏 (De-identification)**:
   - `PatientName` 强制替换为 `ANONYMOUS`。
   - `PatientBirthDate` 强制截断/抹除（保留至年份如 `19900101` 或默认 `19000101`）。
   - `PatientID` 生成脱敏哈希 Token (`hash_{id}`)。
3. **物理归档**: 将脱敏后的 `.dcm` 文件保存至 `data/minio_mock/dicom/<PatientID>/<StudyUID>/`。
4. **元数据入库 (Staging)**: 
   - 提取的设备模态 (Modality)、检查时间 (StudyDate) 将被映射写入 `stg_observation` 表。
   - `observation_concept_id` 自动标记为 `4052536`（OMOP Medical Imaging 概念）。
   - `file_storage_path` 会保留最终的脱敏文件存储寻址路径，以备下游 ODS / 算法系统读取使用。

---

## 3. Staging 层端到端流程与运维保障

为了确保 "双流接入成功率达 99.9% 以上" 及 "端到端数据处理延迟低于 5 分钟"，我们在平台内建了实时监控与告警服务模块 (`app.services.monitor.MonitoringService`)。

### 3.1 监控 API
- **Endpoint**: `GET /api/v1/monitor/health`
- **返回值示例**:
```json
{
  "timestamp": "2026-06-23T08:00:00.000",
  "overall_status": "Healthy",
  "checks": {
    "storage": { "status": "ok", "message": "Storage capacity normal" },
    "latency": { "status": "ok", "message": "Processing latency normal" },
    "error_rates": { "status": "ok", "message": "Error rates normal" }
  }
}
```

### 3.2 告警规则与风险响应 (Playbook)

#### 🚨 风险场景 A：存储容量不足 (Storage Capacity Critical)
- **触发条件**: 检测到对象存储 (MinIO/Mock) 所在磁盘/分区的空闲容量不足 10%（即 `Usage > 90%`）。
- **影响**: DICOM 影像流将无法写入，系统可能大面积抛出 `IOError`。
- **运维动作**: 
  1. 拦截告警通知运维工程师。
  2. 扩容存储集群节点。
  3. 执行冷数据归档脚本，将早期 Staging 影像转移至 S3 Glacier 或磁带库。

#### 🚨 风险场景 B：数据接入延迟 (Processing Latency)
- **触发条件**: 批次任务记录 `SourceBatch` 停留在 `processing` 状态超过 5 分钟（`LATENCY_THRESHOLD_MINUTES`）。
- **影响**: Staging 到 ODS 的数据同步管线卡顿，业务系统无法实时拉取影像结果。
- **运维动作**: 
  1. 检查 `celery` / `BackgroundTasks` 工作线程是否发生死锁。
  2. 针对超大尺寸的多帧 DICOM，考虑扩展 `tmp_path` 解析超时时间，或增加工作节点的 CPU 规格。

#### 🚨 风险场景 C：格式异常 (High Error Rate)
- **触发条件**: 近 24 小时内完成的批次中，异常拦截率（Error Rows）超过 10%。
- **影响**: PACS 接口传输可能发生数据包截断，或 DICOM 标准被院方非标私有化篡改。
- **运维动作**: 
  1. 提取错误日志 (ErrorRecord 表)。
  2. 确认是否缺少必须的 Header Tags (如无 `PatientID`)。
  3. 协同院方调整 PACS 推送策略或在 `dicom_parser.py` 中补充容错补丁。

---
**编写者**: OMOP Data Platform Team
**更新日期**: 2026-06-23
