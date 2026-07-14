# OMOP NLP Domain Expansion Design

## Background

The current NLP pipeline is a three-stage extractor (`regex -> NER -> LLM`) that mainly supports:

- `condition_occurrence`
- `drug_exposure`
- `measurement`
- `observation`

This is useful for lightweight staging, but it is not yet aligned with a broader OMOP-style clinical text ingestion design. Key gaps include:

- `procedures` are extracted but not persisted
- original clinical text is not preserved in a dedicated note layer
- no `note_nlp` style traceability
- no domain coverage for `device`, `specimen`, `death`, `provider`, `care_site`
- limited concept standardization support

## Goal

Upgrade the current staging-oriented NLP flow into a broader OMOP-style staging pipeline that:

1. Preserves original clinical text
2. Persists extracted entities into the correct staging domains
3. Mirrors extracted entities into a `note_nlp`-like layer for traceability
4. Expands domain coverage beyond the current minimal set
5. Leaves room for later concept standardization without blocking this phase

## Scope

### In Scope

- Add new staging models:
  - `stg_procedure_occurrence`
  - `stg_note`
  - `stg_note_nlp`
  - `stg_specimen`
  - `stg_device_exposure`
  - `stg_death`
  - `stg_provider`
  - `stg_care_site`
- Extend NLP output schema
- Update staging persistence logic to support new domains
- Preserve all note-like source text in `stg_note`
- Mirror extracted entities into `stg_note_nlp`
- Add base dedupe behavior for repeated entities
- Keep current performance optimizations and timing logs intact

### Out of Scope for This Phase

- Full OMOP vocabulary platform or complete concept mapping workflow
- Precise character-level offsets for all extracted entities
- Complex cross-note or cross-visit relation inference
- Full longitudinal linking between provider/device/death and downstream standardized OMOP fact tables

## Target Architecture

### 1. Raw Text Layer

All narrative fields become note records:

- `lab_results`
- `chief_complaint`
- `history_of_present_illness`
- `imaging_reports`
- `admission_record`
- `daily_course_record`
- `discharge_summary`
- `treatment_plan`

Each populated field creates one `stg_note` record.

### 2. NLP Extraction Layer

The existing three-stage extractor remains:

- `regex`: deterministic structured values
- `NER`: short medical entities
- `LLM`: complex residual semantics

The output schema expands from the current minimal schema to:

```json
{
  "conditions": [],
  "medications": [],
  "procedures": [],
  "measurements": [],
  "symptoms_with_values": [],
  "times": [],
  "observations": [],
  "negations": [],
  "devices": [],
  "specimens": [],
  "death": [],
  "providers": [],
  "care_sites": [],
  "note_nlp_items": []
}
```

`note_nlp_items` is used as a trace/mirror structure for note-level NLP evidence. Initial item shape:

```json
{
  "domain": "procedure",
  "text": "冠脉CTA",
  "normalized_value": "冠脉CTA",
  "section": "daily_course_record",
  "negated": false,
  "confidence": 0.91
}
```

### 3. Staging Domain Layer

Domain persistence rules:

- `conditions` -> `stg_condition_occurrence`
- `medications` -> `stg_drug_exposure`
- `measurements` -> `stg_measurement`
- `procedures` -> `stg_procedure_occurrence`
- `devices` -> `stg_device_exposure`
- `specimens` -> `stg_specimen`
- `death` -> `stg_death`
- `providers` -> `stg_provider`
- `care_sites` -> `stg_care_site`
- all raw notes -> `stg_note`
- all extracted entities mirrored -> `stg_note_nlp`
- unclassified residual information -> `stg_observation`

### 4. Standardization Layer

This phase is source-value first:

- store `*_source_value`
- add `*_concept_id` fields where appropriate
- allow `0` or lightweight rule-based values for now

Full vocabulary expansion is deferred to a later phase.

## New Staging Models

### `stg_procedure_occurrence`

Purpose:
- persist procedures already extracted by NLP

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `procedure_source_value`
- `procedure_source_concept_id`
- `procedure_date`
- `procedure_datetime`
- `note_id`
- `created_at`

### `stg_note`

Purpose:
- preserve original clinical text by source section

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `note_source_value`
- `note_text`
- `note_date`
- `note_datetime`
- `created_at`

### `stg_note_nlp`

Purpose:
- store note-linked NLP evidence

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `note_id`
- `section_source_value`
- `nlp_domain`
- `lexical_variant`
- `normalized_value`
- `term_exists`
- `offset_start`
- `offset_end`
- `note_nlp_concept_id`
- `created_at`

`offset_start` and `offset_end` may be nullable in this phase.

### `stg_specimen`

Purpose:
- persist specimen-like extractions such as blood, urine, tissue, sputum

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `specimen_source_value`
- `specimen_source_concept_id`
- `specimen_date`
- `specimen_datetime`
- `note_id`
- `created_at`

### `stg_device_exposure`

Purpose:
- persist support devices and implants such as stents, pacemakers, catheters

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `device_source_value`
- `device_source_concept_id`
- `device_exposure_start_date`
- `device_exposure_start_datetime`
- `note_id`
- `created_at`

### `stg_death`

Purpose:
- persist death-related signals

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `person_source_value`
- `death_date`
- `death_datetime`
- `death_type_source_value`
- `cause_source_value`
- `note_id`
- `created_at`

### `stg_provider`

Purpose:
- persist provider-like references found in notes

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `provider_source_value`
- `provider_name`
- `specialty_source_value`
- `created_at`

### `stg_care_site`

Purpose:
- persist care-site-like references found in notes

Suggested fields:
- `source_batch_id`
- `raw_record_id`
- `care_site_source_value`
- `place_of_service_source_value`
- `created_at`

## NLP Responsibility Split

### Regex

Primary responsibility:
- deterministic structured extraction

Targets:
- `measurements`
- `symptoms_with_values`
- `times`
- `negations`
- some `medications`
- some `specimens`
- some `care_sites`

### NER

Primary responsibility:
- short and medium medical phrases

Targets:
- `conditions`
- `procedures`
- `devices`
- `specimens`
- `observations`

### LLM

Primary responsibility:
- complex residual semantics

Targets:
- long-sentence `procedures`
- implicit `devices`
- `death`
- `providers`
- `care_sites`
- mixed-entity residual text
- harder negation and attribution cases

## Persistence Strategy

### Note Creation

For each populated note-like source column:

1. create one `stg_note`
2. run NLP on the note text
3. persist domain entities to their staging tables
4. mirror each extracted entity into `stg_note_nlp`

### Dedupe Rules

This phase includes lightweight dedupe only:

- within a note, duplicate entities should collapse
- within a batch, repeated `provider` names collapse
- within a batch, repeated `care_site` names collapse

No heavy longitudinal dedupe is introduced in this phase.

## Risk Areas

1. LLM output stability degrades as domains expand
2. `provider`, `care_site`, and `death` boundaries are semantically noisy in Chinese notes
3. Without a vocabulary layer, some domain assignments remain coarse
4. `note_nlp` without offsets is traceable but not fully text-anchored

## Implementation Plan Boundary

Implementation should proceed in this order:

1. Add new staging models
2. Extend NLP schema and extraction flow
3. Add staging persistence for new domains
4. Add `note` and `note_nlp` persistence
5. Add tests for each domain and note traceability

## Validation Requirements

At minimum, tests should cover:

- procedure persistence
- note creation from text sections
- note_nlp mirror generation
- one representative extraction for:
  - `devices`
  - `specimens`
  - `death`
  - `providers`
  - `care_sites`
- dedupe behavior for repeated entities

## Self Review

- No placeholder sections remain
- Scope is still large but decomposed into one implementation stream
- Architecture, schema, and persistence strategy are aligned
- The design intentionally separates extraction from OMOP persistence to reduce coupling
