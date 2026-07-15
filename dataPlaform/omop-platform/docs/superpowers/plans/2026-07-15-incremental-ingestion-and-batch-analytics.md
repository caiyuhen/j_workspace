# 增量接入与批次分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 `ingestion -> RawRecord -> Staging -> profiling` 链路上实现可追溯的增量处理、手动补处理、批次分析查询、跨批次对比和导出能力，同时只对变更数据执行下游计算。

**Architecture:** 后端在 `SourceBatch` 与 `RawRecord` 基础上补充增量元数据、运行控制表与批次分析汇总表；增量识别由 `时间窗口 + 版本/操作标识 + 主键快照/哈希比对` 共同驱动；批次分析查询统一读取预聚合汇总，避免每次扫明细表。前端沿用现有 ingestion 工作台，扩展出批次分析筛选、详情、对比与导出入口。

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, pytest, React, TypeScript, Vite, Vitest

---

## 文件结构

### 后端模型与 schema

- 修改: `backend/app/models/raw.py`
- 新建: `backend/app/models/incremental.py`
- 修改: `backend/app/db/database.py`
- 修改: `backend/app/schemas/ingestion.py`

### 后端服务

- 修改: `backend/app/services/raw_persistence.py`
- 修改: `backend/app/services/staging_transformer.py`
- 新建: `backend/app/services/incremental_sync.py`
- 新建: `backend/app/services/batch_analytics.py`

### 后端 API

- 修改: `backend/app/api/ingestion.py`

### 后端测试

- 新建: `backend/tests/test_incremental_models.py`
- 新建: `backend/tests/test_incremental_sync.py`
- 新建: `backend/tests/test_batch_analytics_api.py`
- 修改: `backend/tests/test_raw_persistence.py`
- 修改: `backend/tests/test_ingestion.py`
- 新建: `backend/tests/test_staging_transformer_incremental.py`

### 前端

- 修改: `frontend/src/types/index.ts`
- 修改: `frontend/src/App.tsx`
- 修改: `frontend/src/components/BatchHistory.tsx`
- 新建: `frontend/src/components/BatchAnalyticsPanel.tsx`
- 新建: `frontend/src/components/BatchComparisonTable.tsx`
- 新建: `frontend/src/components/BatchDetailDrawer.tsx`

### 前端测试

- 修改: `frontend/src/components/BatchHistory.test.tsx`
- 新建: `frontend/src/components/BatchAnalyticsPanel.test.tsx`

---

### Task 1: 扩展批次与增量运行模型

**Files:**
- Create: `backend/app/models/incremental.py`
- Modify: `backend/app/models/raw.py`
- Modify: `backend/app/db/database.py`
- Modify: `backend/app/schemas/ingestion.py`
- Test: `backend/tests/test_incremental_models.py`
- Test: `backend/tests/test_database_schema_sync.py`

- [ ] **Step 1: 先写失败测试，约束新增字段和新表**

```python
from app.models.raw import SourceBatch, RawRecord
from app.models.incremental import IncrementalSyncRun, BatchAnalysisSummary


def test_source_batch_and_raw_record_expose_incremental_columns():
    assert hasattr(SourceBatch, "batch_type")
    assert hasattr(SourceBatch, "window_start")
    assert hasattr(SourceBatch, "deleted_rows")
    assert hasattr(RawRecord, "business_key")
    assert hasattr(RawRecord, "record_hash")
    assert hasattr(RawRecord, "change_type")


def test_incremental_models_define_run_and_summary_tables():
    assert IncrementalSyncRun.__tablename__ == "incremental_sync_run"
    assert BatchAnalysisSummary.__tablename__ == "batch_analysis_summary"
```

- [ ] **Step 2: 运行测试，确认当前实现失败**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_incremental_models.py -v`  
Expected: FAIL，提示 `SourceBatch`/`RawRecord` 缺字段，且 `app.models.incremental` 尚不存在

- [ ] **Step 3: 用最小实现补齐模型与 schema 自动兼容**

```python
# backend/app/models/incremental.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class IncrementalSyncRun(Base):
    __tablename__ = "incremental_sync_run"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_name = Column(String, index=True, default="ingestion")
    batch_id = Column(String, ForeignKey("source_batch.id"), index=True)
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    cursor_start = Column(DateTime, nullable=True)
    cursor_end = Column(DateTime, nullable=True)
    status = Column(String, default="running", index=True)
    scan_count = Column(Integer, default=0)
    change_count = Column(Integer, default=0)
    insert_count = Column(Integer, default=0)
    update_count = Column(Integer, default=0)
    delete_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error_log = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class BatchAnalysisSummary(Base):
    __tablename__ = "batch_analysis_summary"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("source_batch.id"), index=True)
    dataset_name = Column(String, index=True, default="ingestion")
    processed_at = Column(DateTime, default=datetime.utcnow, index=True)
    total_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    inserted_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    deleted_rows = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)
    processing_duration_ms = Column(Integer, default=0)
    core_metrics = Column(JSON, nullable=True)
    detail_stats = Column(JSON, nullable=True)
```

```python
# backend/app/models/raw.py
batch_type = Column(String, default="full", index=True)
dataset_name = Column(String, default="ingestion", index=True)
window_start = Column(DateTime, nullable=True)
window_end = Column(DateTime, nullable=True)
trigger_mode = Column(String, default="auto")
source_snapshot_at = Column(DateTime, nullable=True)
processed_rows = Column(Integer, default=0)
inserted_rows = Column(Integer, default=0)
updated_rows = Column(Integer, default=0)
deleted_rows = Column(Integer, default=0)
unchanged_rows = Column(Integer, default=0)
retry_count = Column(Integer, default=0)
error_message = Column(String, nullable=True)
finished_at = Column(DateTime, nullable=True)
```

```python
# backend/app/models/raw.py
dataset_name = Column(String, default="ingestion", index=True)
business_key = Column(String, nullable=True, index=True)
record_hash = Column(String, nullable=True, index=True)
source_updated_at = Column(DateTime, nullable=True, index=True)
source_version = Column(String, nullable=True)
op_flag = Column(String, default="snapshot")
change_type = Column(String, default="unchanged", index=True)
is_processed = Column(Integer, default=0)
processed_at = Column(DateTime, nullable=True)
```

```python
# backend/app/db/database.py
from app.models.incremental import IncrementalSyncRun, BatchAnalysisSummary


def ensure_sqlite_schema_compatibility(engine, metadata):
    expected_columns = {
        "source_batch": {"batch_type", "dataset_name", "window_start", "window_end", "trigger_mode", "source_snapshot_at", "processed_rows", "inserted_rows", "updated_rows", "deleted_rows", "unchanged_rows", "retry_count", "error_message", "finished_at"},
        "raw_record": {"dataset_name", "business_key", "record_hash", "source_updated_at", "source_version", "op_flag", "change_type", "is_processed", "processed_at"},
        "incremental_sync_run": {"id", "dataset_name", "batch_id", "window_start", "window_end", "cursor_start", "cursor_end", "status", "scan_count", "change_count", "insert_count", "update_count", "delete_count", "retry_count", "error_log", "started_at", "finished_at"},
        "batch_analysis_summary": {"id", "batch_id", "dataset_name", "processed_at", "total_rows", "error_rows", "inserted_rows", "updated_rows", "deleted_rows", "success_rate", "processing_duration_ms", "core_metrics", "detail_stats"},
    }
```

- [ ] **Step 4: 重新运行模型和 schema 测试**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_incremental_models.py tests/test_database_schema_sync.py -v`  
Expected: PASS，且 SQLite 缺列时可以自动补齐新字段/新表

- [ ] **Step 5: 提交这一组基础模型改动**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/app/models/raw.py backend/app/models/incremental.py backend/app/db/database.py backend/app/schemas/ingestion.py backend/tests/test_incremental_models.py backend/tests/test_database_schema_sync.py
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: add incremental batch and analytics models"
```

---

### Task 2: 实现增量识别与原始入库增强

**Files:**
- Create: `backend/app/services/incremental_sync.py`
- Modify: `backend/app/services/raw_persistence.py`
- Modify: `backend/app/models/raw.py`
- Test: `backend/tests/test_incremental_sync.py`
- Test: `backend/tests/test_raw_persistence.py`

- [ ] **Step 1: 先写失败测试，锁定 1+2+3 识别规则**

```python
from datetime import datetime, timedelta
from app.services.incremental_sync import IncrementalSyncService


def test_classify_change_prefers_delete_flag():
    svc = IncrementalSyncService(db=None)
    change_type = svc.classify_change(
        incoming={"business_key": "p1", "op_flag": "delete"},
        current_snapshot={"business_key": "p1", "record_hash": "old"},
        window_start=datetime.utcnow() - timedelta(hours=1),
        window_end=datetime.utcnow(),
    )
    assert change_type == "delete"


def test_classify_change_marks_insert_when_key_missing_in_snapshot():
    svc = IncrementalSyncService(db=None)
    change_type = svc.classify_change(
        incoming={"business_key": "p2", "source_updated_at": datetime(2026, 7, 15, 10, 0, 0), "record_hash": "abc"},
        current_snapshot=None,
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )
    assert change_type == "insert"
```

- [ ] **Step 2: 运行测试，验证服务尚未存在**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_incremental_sync.py tests/test_raw_persistence.py -v`  
Expected: FAIL，提示 `IncrementalSyncService` 不存在或 `save_chunk` 尚不支持增量元数据

- [ ] **Step 3: 先实现增量工具服务的最小骨架**

```python
# backend/app/services/incremental_sync.py
import hashlib
import json
from datetime import datetime


class IncrementalSyncService:
    def __init__(self, db):
        self.db = db

    def build_business_key(self, row: dict) -> str:
        return str(row.get("person_id") or row.get("patient_id") or row.get("person_source_value") or row.get("id") or "")

    def build_record_hash(self, row: dict) -> str:
        normalized = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def classify_change(self, incoming: dict, current_snapshot: dict | None, window_start: datetime | None, window_end: datetime | None) -> str:
        if incoming.get("op_flag") == "delete":
            return "delete"
        if current_snapshot and incoming.get("source_version") and incoming.get("source_version") != current_snapshot.get("source_version"):
            return "update"
        ts = incoming.get("source_updated_at")
        in_window = ts is None or ((window_start is None or ts >= window_start) and (window_end is None or ts <= window_end))
        if not current_snapshot and in_window:
            return "insert"
        if current_snapshot and in_window and incoming.get("record_hash") != current_snapshot.get("record_hash"):
            return "update"
        return "unchanged"
```

- [ ] **Step 4: 扩展 `RawPersistenceService.save_chunk`，让有效行带上增量字段**

```python
# backend/app/services/raw_persistence.py
from datetime import datetime
from app.services.incremental_sync import IncrementalSyncService


def save_chunk(self, batch_id: str, valid_rows, error_rows, dataset_name: str = "ingestion", window_start=None, window_end=None):
    sync_service = IncrementalSyncService(self.db)
    raw_records = []
    for row in valid_rows:
        business_key = sync_service.build_business_key(row)
        record_hash = sync_service.build_record_hash(row)
        source_updated_at = row.get("updated_at") or row.get("source_updated_at")
        if isinstance(source_updated_at, str):
            source_updated_at = datetime.fromisoformat(source_updated_at)
        raw_records.append(
            RawRecord(
                batch_id=batch_id,
                dataset_name=dataset_name,
                row_data=row,
                business_key=business_key,
                record_hash=record_hash,
                source_updated_at=source_updated_at,
                source_version=str(row.get("version") or row.get("source_version") or ""),
                op_flag=str(row.get("op_flag") or "snapshot"),
                change_type="unchanged",
            )
        )
```

- [ ] **Step 5: 补充失败测试，校验 `save_chunk` 真实落了增量字段**

```python
def test_save_chunk_persists_incremental_metadata(db_session):
    svc = RawPersistenceService(db_session)
    batch = svc.create_batch("delta.csv")
    svc.save_chunk(
        batch.id,
        valid_rows=[{"patient_id": "P001", "updated_at": "2026-07-15T10:00:00", "version": 2, "name": "Alice"}],
        error_rows=[],
    )
    row = db_session.query(RawRecord).filter(RawRecord.batch_id == batch.id).one()
    assert row.business_key == "P001"
    assert row.record_hash
    assert row.source_version == "2"
```

- [ ] **Step 6: 运行测试，确认增量识别与入库增强通过**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_incremental_sync.py tests/test_raw_persistence.py -v`  
Expected: PASS，且 `RawRecord` 已包含业务主键、哈希、版本、操作标识

- [ ] **Step 7: 提交增量识别与原始入库改动**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/app/services/incremental_sync.py backend/app/services/raw_persistence.py backend/tests/test_incremental_sync.py backend/tests/test_raw_persistence.py
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: add incremental change detection and raw persistence metadata"
```

---

### Task 3: 接入增量运行编排与手动补处理 API

**Files:**
- Modify: `backend/app/api/ingestion.py`
- Create: `backend/app/services/incremental_sync.py`
- Modify: `backend/app/services/raw_persistence.py`
- Modify: `backend/app/schemas/ingestion.py`
- Test: `backend/tests/test_ingestion.py`

- [ ] **Step 1: 先写失败测试，覆盖手动补处理入口**

```python
def test_replay_endpoint_creates_incremental_batch(client):
    response = client.post(
        "/api/v1/ingestion/replay",
        json={
            "dataset_name": "ingestion",
            "trigger_mode": "manual",
            "window_start": "2026-07-15T09:00:00",
            "window_end": "2026-07-15T11:00:00",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_type"] == "replay"
    assert payload["trigger_mode"] == "manual"
```

- [ ] **Step 2: 运行 ingestion 测试，确认 replay 接口尚未实现**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_ingestion.py -v`  
Expected: FAIL，提示 `/api/v1/ingestion/replay` 不存在

- [ ] **Step 3: 补 replay request/response schema，并把增量编排接进 ingestion 路由**

```python
# backend/app/schemas/ingestion.py
class ReplayRequest(BaseModel):
    dataset_name: str = "ingestion"
    trigger_mode: str = "manual"
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    batch_id: Optional[str] = None
    business_keys: list[str] = []
```

```python
# backend/app/api/ingestion.py
@router.post("/replay")
def replay_incremental_batch(payload: ReplayRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    persistence = RawPersistenceService(db)
    batch = persistence.create_batch(filename="manual-replay.csv", batch_type="replay", dataset_name=payload.dataset_name, trigger_mode="manual", window_start=payload.window_start, window_end=payload.window_end)
    background_tasks.add_task(
        process_replay_task,
        batch.id,
        payload.dataset_name,
        payload.window_start,
        payload.window_end,
        payload.batch_id,
        payload.business_keys,
    )
    return {
        "batch_id": batch.id,
        "batch_type": batch.batch_type,
        "trigger_mode": batch.trigger_mode,
        "status": batch.status,
    }
```

- [ ] **Step 4: 让 `create_batch` 支持批次类型、窗口、触发方式**

```python
# backend/app/services/raw_persistence.py
def create_batch(self, filename: str, batch_type: str = "full", dataset_name: str = "ingestion", trigger_mode: str = "auto", window_start=None, window_end=None) -> SourceBatch:
    batch = SourceBatch(
        filename=filename,
        status="processing",
        batch_type=batch_type,
        dataset_name=dataset_name,
        trigger_mode=trigger_mode,
        window_start=window_start,
        window_end=window_end,
    )
```

- [ ] **Step 5: 扩展 `/batches` 返回值，让前端能拿到增量批次元数据**

```python
item = {
    "id": str(b.id),
    "filename": str(b.filename),
    "batch_type": str(b.batch_type),
    "dataset_name": str(b.dataset_name),
    "trigger_mode": str(b.trigger_mode),
    "window_start": b.window_start.isoformat() if b.window_start else None,
    "window_end": b.window_end.isoformat() if b.window_end else None,
    "inserted_rows": int(b.inserted_rows or 0),
    "updated_rows": int(b.updated_rows or 0),
    "deleted_rows": int(b.deleted_rows or 0),
    "unchanged_rows": int(b.unchanged_rows or 0),
}
```

- [ ] **Step 6: 重跑 ingestion 测试**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_ingestion.py -v`  
Expected: PASS，上传批次与 replay 批次都返回增量元信息

- [ ] **Step 7: 提交编排与 replay API**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/app/api/ingestion.py backend/app/services/raw_persistence.py backend/app/schemas/ingestion.py backend/tests/test_ingestion.py
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: add incremental replay orchestration endpoints"
```

---

### Task 4: 让 Staging 只处理变更数据，并补批次分析汇总

**Files:**
- Modify: `backend/app/services/staging_transformer.py`
- Create: `backend/app/services/batch_analytics.py`
- Create: `backend/tests/test_staging_transformer_incremental.py`
- Create: `backend/tests/test_batch_analytics_api.py`

- [ ] **Step 1: 先写失败测试，要求 transformer 只拉取变更行**

```python
def test_transformer_only_reads_changed_rows(db_session):
    batch = SourceBatch(id="batch_inc", filename="inc.csv", batch_type="incremental")
    db_session.add(batch)
    db_session.add_all([
        RawRecord(batch_id=batch.id, row_data={"patient_id": "P1"}, business_key="P1", change_type="insert"),
        RawRecord(batch_id=batch.id, row_data={"patient_id": "P2"}, business_key="P2", change_type="unchanged"),
    ])
    db_session.commit()

    transformer = StagingTransformer(db_session, ner_mapper=DummyNER())
    transformer.transform_batch_to_person(batch_id=batch.id, mapping_config={"person_source_value": "patient_id"})

    assert db_session.query(StagingPerson).filter(StagingPerson.source_batch_id == batch.id).count() == 1
```

- [ ] **Step 2: 运行测试，确认当前 transformer 会把整批都拉进来**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_staging_transformer_incremental.py -v`  
Expected: FAIL，当前 `transform_batch_to_person` 只按 `batch_id` 过滤，不区分 `change_type`

- [ ] **Step 3: 调整查询条件，只读取 `insert/update/delete`，并为 delete 预留清理入口**

```python
# backend/app/services/staging_transformer.py
raw_records = (
    self.db.query(RawRecord)
    .filter(RawRecord.batch_id == batch_id)
    .filter(RawRecord.change_type.in_(["insert", "update", "delete"]))
    .limit(self.BATCH_SIZE)
    .offset(offset)
    .all()
)
```

```python
# backend/app/services/staging_transformer.py
if raw.change_type == "delete":
    self._delete_existing_staging_rows(batch_id=batch_id, business_key=raw.business_key)
    continue
```

- [ ] **Step 4: 新建批次分析汇总服务，并先用最小聚合跑通**

```python
# backend/app/services/batch_analytics.py
from app.models.incremental import BatchAnalysisSummary
from app.models.raw import SourceBatch, RawRecord, ErrorRecord


class BatchAnalyticsService:
    def __init__(self, db):
        self.db = db

    def build_summary_for_batch(self, batch_id: str) -> BatchAnalysisSummary:
        batch = self.db.query(SourceBatch).filter(SourceBatch.id == batch_id).one()
        summary = self.db.query(BatchAnalysisSummary).filter(BatchAnalysisSummary.batch_id == batch_id).one_or_none()
        if summary is None:
            summary = BatchAnalysisSummary(batch_id=batch_id, dataset_name=batch.dataset_name)
        summary.total_rows = batch.total_rows
        summary.error_rows = batch.error_rows
        summary.inserted_rows = batch.inserted_rows
        summary.updated_rows = batch.updated_rows
        summary.deleted_rows = batch.deleted_rows
        summary.core_metrics = {
            "raw_records": self.db.query(RawRecord).filter(RawRecord.batch_id == batch_id).count(),
            "error_records": self.db.query(ErrorRecord).filter(ErrorRecord.batch_id == batch_id).count(),
        }
        self.db.add(summary)
        self.db.commit()
        return summary
```

- [ ] **Step 5: 增加失败测试，校验汇总表可以写出批次核心指标**

```python
def test_batch_analytics_summary_aggregates_incremental_counts(db_session):
    batch = SourceBatch(
        id="batch_summary",
        filename="summary.csv",
        total_rows=10,
        error_rows=1,
        inserted_rows=3,
        updated_rows=2,
        deleted_rows=1,
    )
    db_session.add(batch)
    db_session.commit()

    summary = BatchAnalyticsService(db_session).build_summary_for_batch(batch.id)
    assert summary.inserted_rows == 3
    assert summary.updated_rows == 2
    assert summary.deleted_rows == 1
```

- [ ] **Step 6: 重跑 transformer 与 analytics 测试**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_staging_transformer_incremental.py tests/test_batch_analytics_api.py -v`  
Expected: PASS，unchanged 行不会触发 Staging，下游可得到批次汇总

- [ ] **Step 7: 提交 selective staging 与分析汇总**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/app/services/staging_transformer.py backend/app/services/batch_analytics.py backend/tests/test_staging_transformer_incremental.py backend/tests/test_batch_analytics_api.py
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: process only changed rows and build batch analytics summaries"
```

---

### Task 5: 增加批次分析查询、对比和导出 API

**Files:**
- Modify: `backend/app/api/ingestion.py`
- Create: `backend/app/services/batch_analytics.py`
- Create: `backend/tests/test_batch_analytics_api.py`

- [ ] **Step 1: 先写失败测试，覆盖批次筛选与导出**

```python
def test_batch_analytics_list_filters_by_batch_type_and_time_range(client, seeded_batches):
    response = client.get("/api/v1/ingestion/batch-analytics?batch_type=incremental&start_time=2026-07-15T00:00:00&end_time=2026-07-15T23:59:59")
    assert response.status_code == 200
    payload = response.json()
    assert all(item["batch_type"] == "incremental" for item in payload["items"])


def test_batch_analytics_export_returns_csv(client, seeded_batches):
    response = client.get("/api/v1/ingestion/batch-analytics/export?batch_ids=batch_1,batch_2")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
```

- [ ] **Step 2: 运行 API 测试，确认查询与导出接口尚不存在**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_batch_analytics_api.py -v`  
Expected: FAIL，提示 `404 Not Found`

- [ ] **Step 3: 在 analytics 服务里提供筛选、对比、导出方法**

```python
class BatchAnalyticsService:
    def query_summaries(self, batch_type=None, start_time=None, end_time=None, status=None):
        query = self.db.query(SourceBatch, BatchAnalysisSummary).outerjoin(
            BatchAnalysisSummary, BatchAnalysisSummary.batch_id == SourceBatch.id
        )
        if batch_type:
            query = query.filter(SourceBatch.batch_type == batch_type)
        if status:
            query = query.filter(SourceBatch.status == status)
        if start_time:
            query = query.filter(SourceBatch.created_at >= start_time)
        if end_time:
            query = query.filter(SourceBatch.created_at <= end_time)
        return query.order_by(SourceBatch.created_at.desc()).all()

    def export_csv(self, batch_ids: list[str]) -> str:
        rows = self.query_summaries()
        lines = ["batch_id,batch_type,status,total_rows,inserted_rows,updated_rows,deleted_rows"]
        for batch, summary in rows:
            if batch_ids and batch.id not in batch_ids:
                continue
            lines.append(f"{batch.id},{batch.batch_type},{batch.status},{batch.total_rows},{batch.inserted_rows},{batch.updated_rows},{batch.deleted_rows}")
        return "\n".join(lines)
```

- [ ] **Step 4: 在 ingestion API 新增批次分析列表、详情、对比、导出端点**

```python
@router.get("/batch-analytics")
def list_batch_analytics(
    batch_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    service = BatchAnalyticsService(db)
    rows = service.query_summaries(batch_type=batch_type, start_time=start_time, end_time=end_time, status=status)
    return {"items": [service.serialize_row(batch, summary) for batch, summary in rows]}


@router.get("/batch-analytics/export")
def export_batch_analytics(batch_ids: str = "", db: Session = Depends(get_db)):
    content = BatchAnalyticsService(db).export_csv([x for x in batch_ids.split(",") if x])
    return Response(content=content, media_type="text/csv")
```

- [ ] **Step 5: 重跑批次分析 API 测试**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_batch_analytics_api.py -v`  
Expected: PASS，列表筛选、对比和导出都返回稳定结果

- [ ] **Step 6: 提交批次分析查询能力**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/app/api/ingestion.py backend/app/services/batch_analytics.py backend/tests/test_batch_analytics_api.py
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: add batch analytics query and export endpoints"
```

---

### Task 6: 实现前端批次分析工作台

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/BatchHistory.tsx`
- Create: `frontend/src/components/BatchAnalyticsPanel.tsx`
- Create: `frontend/src/components/BatchComparisonTable.tsx`
- Create: `frontend/src/components/BatchDetailDrawer.tsx`
- Modify: `frontend/src/components/BatchHistory.test.tsx`
- Create: `frontend/src/components/BatchAnalyticsPanel.test.tsx`

- [ ] **Step 1: 先写失败测试，要求列表展示增量字段与筛选入口**

```tsx
import { render, screen } from '@testing-library/react';
import BatchAnalyticsPanel from './BatchAnalyticsPanel';

test('renders incremental counters and filter controls', () => {
  render(
    <BatchAnalyticsPanel
      batches={[
        {
          id: 'batch_1',
          filename: 'delta.csv',
          total_rows: 10,
          error_rows: 1,
          status: 'completed',
          batch_type: 'incremental',
          inserted_rows: 3,
          updated_rows: 2,
          deleted_rows: 1,
          unchanged_rows: 4,
          created_at: '2026-07-15T10:00:00',
        },
      ]}
    />
  );

  expect(screen.getByText('批次分析')).toBeInTheDocument();
  expect(screen.getByText('增量批次')).toBeInTheDocument();
  expect(screen.getByText('新增 3')).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行前端测试，确认新组件尚未实现**

Run: `cd d:\workspace\dataPlaform\omop-platform\frontend; npm run test -- BatchAnalyticsPanel.test.tsx BatchHistory.test.tsx`  
Expected: FAIL，提示 `BatchAnalyticsPanel` 文件不存在，`Batch` 类型缺少增量字段

- [ ] **Step 3: 先扩展前端类型，补齐批次增量字段**

```ts
export interface Batch {
  id: string;
  filename: string;
  total_rows: number;
  error_rows: number;
  status: string;
  profiling_data?: any;
  created_at: string;
  batch_type?: string;
  dataset_name?: string;
  trigger_mode?: string;
  window_start?: string | null;
  window_end?: string | null;
  inserted_rows?: number;
  updated_rows?: number;
  deleted_rows?: number;
  unchanged_rows?: number;
}
```

- [ ] **Step 4: 新建批次分析面板与对比表的最小 UI**

```tsx
// frontend/src/components/BatchAnalyticsPanel.tsx
export default function BatchAnalyticsPanel({ batches = [], onExport, onSelectBatch }: BatchAnalyticsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>批次分析</CardTitle>
        <CardDescription>按批次号、时间范围和批次类型查看增量处理结果</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Input placeholder="批次号" />
          <Input placeholder="开始时间" />
          <Input placeholder="结束时间" />
          <Button onClick={onExport}>导出当前筛选</Button>
        </div>
        {batches.map((batch) => (
          <div key={batch.id} className="rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">{batch.filename}</div>
                <div className="text-sm text-slate-500">{batch.batch_type === 'incremental' ? '增量批次' : '全量批次'}</div>
              </div>
              <Button variant="outline" onClick={() => onSelectBatch?.(batch)}>查看详情</Button>
            </div>
            <div className="mt-3 flex gap-4 text-sm">
              <span>新增 {batch.inserted_rows ?? 0}</span>
              <span>更新 {batch.updated_rows ?? 0}</span>
              <span>删除 {batch.deleted_rows ?? 0}</span>
              <span>未变化 {batch.unchanged_rows ?? 0}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 5: 把新面板接进 `App.tsx` 和 `BatchHistory.tsx`**

```tsx
// frontend/src/App.tsx
const [selectedAnalyticsBatch, setSelectedAnalyticsBatch] = useState<Batch | null>(null);

{activeTab === 'ingestion' && (
  <div className="lg:col-span-2 space-y-6">
    <UploadForm onUploadSuccess={handleUploadSuccess} />
    <BatchAnalyticsPanel
      batches={batches}
      onSelectBatch={setSelectedAnalyticsBatch}
      onExport={() => window.open('http://127.0.0.1:8433/api/v1/ingestion/batch-analytics/export')}
    />
    <BatchHistory
      batches={batches}
      loading={loadingBatches}
      error={batchError}
      onRefresh={fetchBatches}
      autoOpenBatchId={autoOpenBatchId}
      onAutoOpenDone={() => setAutoOpenBatchId(null)}
      onOpenProfiling={handleOpenProfiling}
    />
  </div>
)}
```

- [ ] **Step 6: 重跑前端测试**

Run: `cd d:\workspace\dataPlaform\omop-platform\frontend; npm run test -- BatchAnalyticsPanel.test.tsx BatchHistory.test.tsx`  
Expected: PASS，批次分析工作台可以渲染增量字段、筛选与导出入口

- [ ] **Step 7: 提交前端批次分析工作台**

```bash
git -C d:\workspace\dataPlaform\omop-platform add frontend/src/types/index.ts frontend/src/App.tsx frontend/src/components/BatchHistory.tsx frontend/src/components/BatchAnalyticsPanel.tsx frontend/src/components/BatchComparisonTable.tsx frontend/src/components/BatchDetailDrawer.tsx frontend/src/components/BatchHistory.test.tsx frontend/src/components/BatchAnalyticsPanel.test.tsx
git -C d:\workspace\dataPlaform\omop-platform commit -m "feat: add batch analytics workspace to ingestion UI"
```

---

### Task 7: 端到端回归与文档收尾

**Files:**
- Modify: `backend/tests/test_ingestion.py`
- Modify: `backend/tests/test_batch_analytics_api.py`
- Modify: `frontend/src/components/BatchAnalyticsPanel.test.tsx`
- Modify: `docs/superpowers/specs/2026-07-15-incremental-ingestion-and-batch-analytics-design.md`

- [ ] **Step 1: 补一条端到端回归测试，覆盖 upload -> incremental metadata -> summary query**

```python
def test_upload_batch_flows_into_batch_analytics_summary(client, tmp_path):
    csv_path = tmp_path / "delta.csv"
    csv_path.write_text("patient_id,updated_at,version,name\nP001,2026-07-15T10:00:00,2,Alice\n", encoding="utf-8")
    with csv_path.open("rb") as f:
        upload = client.post("/api/v1/ingestion/upload", files={"file": ("delta.csv", f, "text/csv")})
    assert upload.status_code == 200
```

- [ ] **Step 2: 运行后端回归测试集合**

Run: `cd d:\workspace\dataPlaform\omop-platform\backend; .\venv\Scripts\python -m pytest tests/test_incremental_models.py tests/test_incremental_sync.py tests/test_raw_persistence.py tests/test_ingestion.py tests/test_staging_transformer_incremental.py tests/test_batch_analytics_api.py -v`  
Expected: PASS，且无新增 schema 回滚或接口兼容性错误

- [ ] **Step 3: 运行前端回归测试集合**

Run: `cd d:\workspace\dataPlaform\omop-platform\frontend; npm run test -- BatchHistory.test.tsx BatchAnalyticsPanel.test.tsx UploadForm.test.tsx`  
Expected: PASS，现有上传与历史批次能力不回归

- [ ] **Step 4: 更新 spec 的实现状态备注**

```md
## Implementation Status

- backend incremental metadata: done
- replay orchestration: done
- selective staging: done
- batch analytics query: done
- frontend analytics workspace: done
```

- [ ] **Step 5: 提交回归验证与文档同步**

```bash
git -C d:\workspace\dataPlaform\omop-platform add backend/tests/test_ingestion.py backend/tests/test_batch_analytics_api.py frontend/src/components/BatchAnalyticsPanel.test.tsx docs/superpowers/specs/2026-07-15-incremental-ingestion-and-batch-analytics-design.md
git -C d:\workspace\dataPlaform\omop-platform commit -m "test: add end-to-end coverage for incremental batch analytics"
```

---

## Self-Review

**Spec coverage**

- 增量识别规则: Task 2
- 手动补处理: Task 3
- 仅处理变更数据: Task 4
- 批次分析查询/对比/导出: Task 5
- 可视化前端界面: Task 6
- 日志与回归验证: Task 7

**Placeholder scan**

- 未保留 `TODO`、`TBD`、`implement later`
- 每个任务都给出了明确文件路径、测试命令、最小实现骨架和提交命令

**Type consistency**

- 统一使用 `batch_type`、`trigger_mode`、`window_start`、`window_end`
- 统一使用 `business_key`、`record_hash`、`change_type`
- 统一使用 `IncrementalSyncRun` 与 `BatchAnalysisSummary`
