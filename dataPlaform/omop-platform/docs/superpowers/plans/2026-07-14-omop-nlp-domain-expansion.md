# OMOP NLP Domain Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the current NLP-to-staging pipeline so that original notes, extracted procedures, and additional OMOP-style staging domains are persisted with note-level traceability.

**Architecture:** Keep the existing `regex -> NER -> LLM` extraction flow, expand the NLP result schema, and separate extraction from persistence. Original note text will be written to `stg_note`, mirrored entities will be written to `stg_note_nlp`, and each extracted domain will persist to its dedicated staging table.

**Tech Stack:** FastAPI, SQLAlchemy ORM, SQLite staging DB, pytest, Python regex, Transformers pipeline, local OpenAI-compatible LLM

---

### Task 1: Add New Staging Models

**Files:**
- Modify: `backend/app/models/staging.py`
- Test: `backend/tests/test_staging_models_expansion.py`

- [ ] **Step 1: Write the failing test**

```python
from app.models import staging


def test_staging_metadata_includes_new_omop_nlp_tables():
    expected_tables = {
        "stg_procedure_occurrence",
        "stg_note",
        "stg_note_nlp",
        "stg_specimen",
        "stg_device_exposure",
        "stg_death",
        "stg_provider",
        "stg_care_site",
    }
    metadata_tables = set(staging.Base.metadata.tables.keys())
    assert expected_tables.issubset(metadata_tables)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_models_expansion.py::test_staging_metadata_includes_new_omop_nlp_tables -v`
Expected: FAIL because the new staging tables are not defined yet.

- [ ] **Step 3: Write minimal implementation**

```python
class StagingProcedureOccurrence(Base):
    __tablename__ = "stg_procedure_occurrence"
    ...

class StagingNote(Base):
    __tablename__ = "stg_note"
    ...

class StagingNoteNlp(Base):
    __tablename__ = "stg_note_nlp"
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_models_expansion.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/staging.py backend/tests/test_staging_models_expansion.py
git commit -m "feat: add OMOP NLP staging models"
```

### Task 2: Expand NLP Output Schema

**Files:**
- Modify: `backend/app/services/transformers_ner.py`
- Test: `backend/tests/test_transformers_ner_schema_expansion.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.transformers_ner import TransformersNERMapper


def test_empty_result_contains_new_domain_buckets():
    mapper = object.__new__(TransformersNERMapper)
    result = mapper._empty_result()
    assert "devices" in result
    assert "specimens" in result
    assert "death" in result
    assert "providers" in result
    assert "care_sites" in result
    assert "note_nlp_items" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_transformers_ner_schema_expansion.py::test_empty_result_contains_new_domain_buckets -v`
Expected: FAIL because the extra buckets do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def _empty_result(...):
    return {
        ...
        "devices": [],
        "specimens": [],
        "death": [],
        "providers": [],
        "care_sites": [],
        "note_nlp_items": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_transformers_ner_schema_expansion.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/transformers_ner.py backend/tests/test_transformers_ner_schema_expansion.py
git commit -m "feat: expand NLP schema for OMOP domains"
```

### Task 3: Persist Notes and Procedures

**Files:**
- Modify: `backend/app/services/staging_transformer.py`
- Test: `backend/tests/test_staging_transformer_note_and_procedure.py`

- [ ] **Step 1: Write the failing test**

```python
def test_transformer_persists_note_and_procedure_entities(db_session):
    ...
    assert db_session.query(StagingNote).count() == 1
    assert db_session.query(StagingProcedureOccurrence).count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_transformer_note_and_procedure.py -v`
Expected: FAIL because notes and procedures are not persisted yet.

- [ ] **Step 3: Write minimal implementation**

```python
note = StagingNote(...)
staging_objects.append(note)

for proc_val in extracted_entities.get("procedures", []):
    proc = StagingProcedureOccurrence(...)
    staging_objects.append(proc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_transformer_note_and_procedure.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/staging_transformer.py backend/tests/test_staging_transformer_note_and_procedure.py
git commit -m "feat: persist notes and procedures to staging"
```

### Task 4: Persist Note NLP Mirrors and New Domains

**Files:**
- Modify: `backend/app/services/staging_transformer.py`
- Modify: `backend/app/services/transformers_ner.py`
- Test: `backend/tests/test_staging_transformer_note_nlp.py`

- [ ] **Step 1: Write the failing test**

```python
def test_transformer_persists_note_nlp_mirrors_for_new_domains(db_session):
    ...
    rows = db_session.query(StagingNoteNlp).all()
    assert any(row.nlp_domain == "device" for row in rows)
    assert any(row.nlp_domain == "specimen" for row in rows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_transformer_note_nlp.py -v`
Expected: FAIL because note_nlp mirroring and new domain persistence are missing.

- [ ] **Step 3: Write minimal implementation**

```python
note_nlp = StagingNoteNlp(
    ...,
    nlp_domain="device",
    lexical_variant=device_val,
    normalized_value=device_val,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_staging_transformer_note_nlp.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/staging_transformer.py backend/app/services/transformers_ner.py backend/tests/test_staging_transformer_note_nlp.py
git commit -m "feat: mirror NLP entities into note_nlp"
```

### Task 5: Run Regression and Real Validation

**Files:**
- Modify: `backend/test_specific_nlp.py`
- Test: existing backend tests

- [ ] **Step 1: Add representative domain samples to the NLP smoke script**

```python
samples = [
    "患者置入冠脉支架，标本为静脉血，心内科李主任会诊。",
    "抢救无效死亡，死亡原因为室颤。",
]
```

- [ ] **Step 2: Run focused test suite**

Run: `.\venv\Scripts\python.exe -m pytest tests\test_transformers_ner_batch.py tests\test_transformers_ner_metrics.py tests\test_staging_transformer.py tests\test_staging_transformer_note_and_procedure.py tests\test_staging_transformer_note_nlp.py -q`
Expected: PASS

- [ ] **Step 3: Run real NLP smoke script**

Run: `.\venv\Scripts\python.exe test_specific_nlp.py`
Expected: Structured JSON output including new domain buckets, with no runtime exception.

- [ ] **Step 4: Review timing logs**

Run: `Get-Content logs\data_operations.log -Tail 80`
Expected: `NLP_BATCH`, `STAGING_NLP`, and `STAGING_ORM` entries are present.

- [ ] **Step 5: Commit**

```bash
git add backend/test_specific_nlp.py
git commit -m "test: extend OMOP NLP domain validation"
```
