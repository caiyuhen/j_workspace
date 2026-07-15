# Incremental Ingestion And Batch Analytics Design

## Background

The current ingestion flow is built around:

- `upload -> SourceBatch / RawRecord / ErrorRecord`
- background CSV parsing
- `StagingTransformer` persistence
- profiling and batch history display

This works for batch ingestion, but it does not yet support:

- incremental change detection
- selective recomputation for changed records only
- replay or backfill of incremental windows
- batch-scoped analytics query and comparison
- exportable batch analytics views

The current batch model is a good foundation, so the preferred direction is to extend the existing ingestion pipeline rather than introduce a parallel data-processing stack.

## Goal

Build an incremental processing and batch analytics capability on top of the existing ingestion pipeline so that the system can:

1. distinguish full runs, incremental runs, and replay runs
2. detect inserts, updates, deletes, and unchanged records
3. process only changed records through cleaning, staging, and analytics
4. support manual replay or backfill for abnormal scenarios
5. provide fast batch-scoped analytics query, comparison, and export
6. preserve traceability through structured run logs and error logs

## Scope

### In Scope

- extend the existing `SourceBatch` model into a richer synchronization batch entity
- extend `RawRecord` with incremental detection fields
- add a dedicated incremental run control model
- add a batch analytics summary model
- implement hybrid incremental detection based on:
  - time window
  - source version or operation flag
  - primary-key snapshot comparison
- support delete handling through downstream physical deletion
- support manual replay or backfill by time window, batch, or business key
- expose batch analytics query endpoints for:
  - batch id filter
  - processing time range filter
  - batch type and status filter
  - single-batch analytics view
  - cross-batch comparison
  - export
- update the frontend batch history area into a batch analytics entry and detail view

### Out of Scope for This Phase

- a full CDC streaming platform
- full user or RBAC subsystem redesign
- real-time event streaming analytics
- Excel-first export formatting
- full source-system adapter generalization for every possible dataset

The first implementation target is the current ingestion chain:

- `RawRecord -> Staging -> profiling / analytics`

## Confirmed Design Decisions

- incremental detection strategy: `1 + 2 + 3`
  - time window
  - version or operation flag
  - primary-key snapshot comparison
- first supported business path:
  - existing ingestion pipeline
- delete policy:
  - downstream physical deletion
- processing model:
  - only changed records proceed into staging and analytics recomputation

## Target Architecture

### 1. Ingestion Batch Layer

Each upload, scheduled incremental run, or manual replay creates one `SourceBatch`.

`SourceBatch` remains the business-facing batch object used by:

- ingestion history
- processing state display
- batch analytics filters
- replay entry points

### 2. Incremental Run Control Layer

A new incremental sync control record tracks the execution semantics of each run:

- detection window
- cursor range
- counts
- retries
- error details
- final state

This layer is operational and audit-oriented.

### 3. Raw Change Detection Layer

During parsing, each normalized input row produces:

- business key
- source updated timestamp
- source version
- operation flag
- normalized record hash

These fields allow the system to classify each row as:

- `insert`
- `update`
- `delete`
- `unchanged`

### 4. Selective Downstream Processing Layer

Only `insert`, `update`, and `delete` rows proceed to downstream actions.

- `insert`:
  create new downstream records
- `update`:
  remove prior downstream records for the business key, then recompute
- `delete`:
  physically delete related downstream staging and analytics detail records
- `unchanged`:
  record counts and logs only

### 5. Batch Analytics Summary Layer

Batch query endpoints should not scan all raw or staging tables on every request.

Instead, each completed batch writes a pre-aggregated analytics summary that powers:

- list filtering
- detail pages
- cross-batch comparison
- export

## Data Model Design

### Extend `SourceBatch`

Add fields:

- `batch_type`
  - `full`
  - `incremental`
  - `replay`
- `dataset_name`
- `window_start`
- `window_end`
- `trigger_mode`
  - `auto`
  - `manual`
- `source_snapshot_at`
- `processed_rows`
- `inserted_rows`
- `updated_rows`
- `deleted_rows`
- `unchanged_rows`
- `retry_count`
- `error_message`
- `finished_at`

Purpose:

- represent synchronization semantics at the batch level
- support frontend filtering and display without reconstructing counts from detail tables

### Extend `RawRecord`

Add fields:

- `dataset_name`
- `business_key`
- `record_hash`
- `source_updated_at`
- `source_version`
- `op_flag`
  - `insert`
  - `update`
  - `delete`
  - `snapshot`
- `change_type`
  - `insert`
  - `update`
  - `delete`
  - `unchanged`
- `is_processed`
- `processed_at`

Purpose:

- store the minimum incremental detection state alongside the raw payload
- allow selective downstream processing without re-deriving row semantics later

### Add `incremental_sync_run`

Suggested fields:

- `id`
- `dataset_name`
- `batch_id`
- `window_start`
- `window_end`
- `cursor_start`
- `cursor_end`
- `status`
  - `running`
  - `success`
  - `failed`
  - `partial_success`
- `scan_count`
- `change_count`
- `insert_count`
- `update_count`
- `delete_count`
- `retry_count`
- `started_at`
- `finished_at`
- `error_log`

Purpose:

- track operational execution of each incremental run
- support audit, replay, and debugging

### Add `batch_analysis_summary`

Suggested fields:

- `id`
- `batch_id`
- `dataset_name`
- `processed_at`
- `total_rows`
- `error_rows`
- `inserted_rows`
- `updated_rows`
- `deleted_rows`
- `success_rate`
- `processing_duration_ms`
- `core_metrics`
- `detail_stats`

Purpose:

- support fast batch query and comparison
- avoid expensive on-demand aggregation over raw or staging data

## Incremental Detection Rules

Each run starts by building or retrieving the current incremental window:

- automatic run:
  use the last successful `cursor_end` as the next `window_start`
- manual replay or backfill:
  allow explicit window override or targeted replay parameters

### Detection Pipeline

For each input row:

1. normalize the business payload
2. derive `business_key`
3. derive `source_updated_at`
4. derive `source_version`
5. derive `op_flag`
6. compute `record_hash` over normalized business fields

### Classification Order

Classification should be deterministic and applied in this order:

1. if `op_flag == delete`, classify as `delete`
2. else if incoming `source_version` is newer than the current snapshot, classify as `update`
3. else if `source_updated_at` falls in the active window and no current snapshot exists for the `business_key`, classify as `insert`
4. else if `source_updated_at` falls in the active window and a snapshot exists but `record_hash` differs, classify as `update`
5. else if a prior snapshot exists but the current input implies removal under the delete detection rules, classify as `delete`
6. else classify as `unchanged`

This ordering prioritizes:

- explicit source intent first
- time-window narrowing second
- snapshot and hash comparison as the final guardrail

## Delete Handling

The confirmed delete policy is downstream physical deletion.

That means:

- the delete event itself should remain traceable in raw or sync-run level records
- current downstream staging or analytics records for the business key should be physically deleted
- batch summaries should still record delete counts and delete-related logs

This preserves operational traceability while honoring the requested deletion behavior in processed outputs.

## Processing Flow

### Automatic Incremental Run

1. create a new `SourceBatch`
2. create a new `incremental_sync_run`
3. compute the active window
4. parse CSV rows and persist enriched `RawRecord` rows
5. classify changes
6. process only changed rows
7. update batch and run counters
8. write `batch_analysis_summary`
9. mark batch and run status

### Manual Replay or Backfill

Supported replay modes:

- replay by time window
- replay by batch id
- targeted replay by `business_key`

Replay should use the same orchestration path as automatic incremental processing, with only the trigger parameters changed.

## Batch Analytics Query Design

### Query Dimensions

Support filters for:

- `batch_id`
- `created_at` or processed time range
- `batch_type`
- `status`
- `dataset_name`

### Batch Detail View

Each batch detail view should show:

- batch metadata
- processing window
- trigger mode
- duration
- retry count
- scan count
- change count
- insert or update or delete or unchanged counts
- error count
- core analytics metrics

### Cross-Batch Comparison

Allow the user to compare multiple selected batches using:

- volume changes
- error-rate changes
- insert or update or delete proportions
- core metric deltas
- processing duration changes

### Export

Support two export modes:

- batch detail export
  - raw, error, and change detail for operational troubleshooting
- batch analytics export
  - summary and comparison views for business review

CSV is sufficient for the first phase.

## Frontend Design

The current `BatchHistory` area should evolve into the batch analytics entry point.

Recommended UI structure:

1. filter panel
   - batch id
   - time range
   - batch type
   - status
   - dataset name
2. batch result table
   - key counts
   - processing state
   - entry to batch detail
3. batch detail page
   - metadata
   - incremental counters
   - analytics summary
4. comparison mode
   - multi-select batches
   - side-by-side comparison table and compact charts

The preferred interaction is a full-page batch analytics workspace rather than modal-driven inspection.

## Performance Design

The design target is business-acceptable response time under large-scale data.

To support that:

- batch list and filter queries should read from `SourceBatch` plus `batch_analysis_summary`
- key filters should be indexed:
  - `batch_id`
  - `created_at`
  - `dataset_name`
  - `status`
- heavy exports should be generated asynchronously
- analytics metrics should be pre-aggregated, not recomputed for every UI request

The first implementation can optimize for SQLite-compatible indexing patterns while keeping model boundaries portable for later migration.

## Consistency And Failure Handling

### Error Categories

1. input errors
   - missing timestamp
   - invalid business key
   - malformed version or operation flag
2. incremental detection errors
   - broken cursor state
   - snapshot collision
   - replay conflict
3. downstream processing errors
   - staging failure
   - profiling failure
   - analytics summary write failure
4. query or export errors
   - invalid filters
   - oversized export
   - timeout

### Handling Strategy

- input errors:
  persist in `ErrorRecord` and continue where possible
- detection errors:
  persist in `incremental_sync_run.error_log`, fail the run or mark partial success
- downstream errors:
  retain batch and run context, allow replay
- query or export errors:
  fail fast with explicit API responses, avoid hanging the UI

### Logging Requirements

Every meaningful log should carry as much context as available:

- `batch_id`
- `dataset_name`
- `sync_run_id`
- `business_key`
- `change_type`
- `window_start`
- `window_end`

## Testing Requirements

At minimum, tests should cover:

- time-window insert detection
- version-driven update detection
- hash-difference update detection
- explicit delete detection through `op_flag`
- unchanged classification
- replay by time window
- replay by batch id
- targeted replay by `business_key`
- selective downstream processing for changed rows only
- update replacement behavior
- delete-driven downstream physical deletion
- batch summary aggregation
- batch query filters
- cross-batch comparison responses
- export responses
- frontend filter and detail rendering

## Implementation Boundary

Implementation should proceed in this order:

1. extend backend models and schema compatibility routines
2. implement incremental detection and replay orchestration
3. integrate selective downstream processing into the existing ingestion path
4. add batch analytics summary generation and query APIs
5. implement frontend batch analytics filters, detail, comparison, and export entry points

## Risks

1. current CSV ingestion may not always contain stable business keys, timestamps, versions, and delete flags
2. physical delete behavior increases the importance of accurate change classification
3. SQLite is acceptable for functional delivery, but very large-scale performance expectations may later require a stronger analytical store
4. replay scope must be tightly validated to avoid accidental duplicate processing

## Self Review

- no placeholder sections remain
- the scope stays focused on the current ingestion path instead of all future datasets
- the incremental detection rules, delete policy, replay support, and batch query design are consistent with the confirmed user choices
- the design intentionally favors batch-level pre-aggregation and selective downstream processing to avoid unnecessary full recomputation
