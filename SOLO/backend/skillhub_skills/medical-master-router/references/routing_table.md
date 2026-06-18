# Routing Table

Complete intent → skill mapping for `medical-master-router`. Organized by Level-1 domain.

When a skill appears in both a domain-specific row and a family fallback, **prefer the domain-specific row first**.

---

## Domain 1: Clinical Care

| Intent | Primary skills | Companion skills |
|---|---|---|
| Clinical notes / SOAP / chart abstraction | `clinical-note-summarization` | `medical-entity-extractor`, `clinical-nlp-extractor` |
| Conversational EHR copilot / longitudinal chart Q&A | `chatehr-clinician-assistant` | `clinical-note-summarization`, `medical-entity-extractor`, `ehr-fhir-integration` |
| Differential diagnosis / diagnostic reasoning | `clinical-diagnostic-reasoning` | `medical-entity-extractor`, `clinical-note-summarization` |
| Patient-specific treatment planning | `treatment-plans` | `tooluniverse-clinical-guidelines`, `clinical-diagnostic-reasoning` |
| Lab interpretation or workflow | `lab-results` | `clinical-note-summarization`, `medical-entity-extractor` |
| Prior authorization / utilization review | `prior-auth-coworker` | `prior-auth-review-skill`, `claims-appeals`, `tooluniverse-clinical-guidelines` |
| EHR / healthcare ML / structured patient modeling | `pyhealth` | `clinical-note-summarization`, `medical-entity-extractor`, `ehr-fhir-integration` |
| Digital twin / patient trajectory simulation | `digital-twin-clinical-agent` | `pyhealth`, `clinical-diagnostic-reasoning`, `tooluniverse-clinical-trial-design` |

## Domain 2: Disease & Guidelines

| Intent | Primary skills | Companion skills |
|---|---|---|
| Disease overview / mechanism / epidemiology | `tooluniverse-disease-research` | `medical-research-toolkit`, `medical-specialty-briefs`, `tooluniverse-literature-deep-research` |
| Guideline-based treatment / standard of care | `tooluniverse-clinical-guidelines` | `clinical-decision-support`, `treatment-plans`, `medical-research-toolkit` |
| Disease overview **plus** treatment | `tooluniverse-disease-research` + `tooluniverse-clinical-guidelines` | add `treatment-plans` if concrete care plan needed |
| Rare disease diagnosis | `tooluniverse-rare-disease-diagnosis` | `tooluniverse-disease-research`, `monarch-database`, `clinvar-database` |
| Infectious disease | `tooluniverse-infectious-disease` | `tooluniverse-disease-research`, `bio-epidemiological-genomics-*`, `claw-metagenomics` |
| Bone marrow / hematology | `bone-marrow-ai-agent` | `chip-clonal-hematopoiesis-agent`, `tooluniverse-disease-research`, `lab-results` |
| Hemoglobinopathy / thalassemia / sickle cell | `hemoglobinopathy-analysis-agent` | `lab-results`, `tooluniverse-disease-research`, `clinvar-database` |
| Coagulation / thrombosis / cytokine storm / senescence | `coagulation-thrombosis-agent`, `cytokine-storm-analysis-agent`, or `cellular-senescence-agent` | `tooluniverse-disease-research`, `medical-research-toolkit` |

## Domain 3: Medication & Safety

| Intent | Primary skills | Companion skills |
|---|---|---|
| Medication list / prescription reconciliation | `drug-interaction-checker` + `tooluniverse-drug-research` | `clinical-note-summarization`, `medical-entity-extractor`, `ehr-fhir-integration`, `patiently-ai` |
| Single-drug profile / label / dosing | `tooluniverse-drug-research` + `drug-labels-search` | `drugbank-database`, `fda-database`, `patiently-ai` |
| Drug-drug interactions / medication safety | `drug-interaction-checker` | `tooluniverse-drug-drug-interaction`, `tooluniverse-pharmacovigilance`, `tooluniverse-drug-research` |
| Pharmacovigilance / adverse events | `tooluniverse-pharmacovigilance` | `tooluniverse-adverse-event-detection`, `fda-database`, `tooluniverse-drug-research` |
| Drug photo / pill identification | `drug-photo` | `tooluniverse-drug-research`, `drug-labels-search`, `patiently-ai` |
| Comprehensive drug profile / clinical development | `tooluniverse-drug-research` | `drugbank-database`, `fda-database`, `drug-labels-search`, `medical-research-toolkit` |
| Drug repurposing / target discovery / network pharmacology | `tooluniverse-drug-repurposing` | `tooluniverse-drug-target-validation`, `tooluniverse-network-pharmacology`, `opentargets-database`, `chembl-database`, `bindingdb-database` |
| Early drug discovery / ADMET / docking | `agentd-drug-discovery` | `chematagent-drug-discovery`, `chemcrow-drug-discovery`, `chemistry-agent`, `medchem`, `deepchem`, `rdkit`, `bio-admet-prediction`, `diffdock` |
| Medicinal chemistry / scaffold optimization | `chemistry-agent` | `medchem`, `medea-therapeutic-discovery`, `molecule-evolution-agent`, `pubchem-database`, `chembl-database` |

## Domain 4: Pharmacogenomics

| Intent | Primary skills | Companion skills |
|---|---|---|
| PGx-guided medication decisions | `pharmacogenomics-agent` or `bio-clinical-databases-pharmacogenomics` | `clinpgx-database`, `clinpgx`, `pharmgx-reporter`, `tooluniverse-clinical-guidelines` |

## Domain 5: Oncology & Precision Medicine

| Intent | Primary skills | Companion skills |
|---|---|---|
| Precision oncology / tumor board / therapy ranking | `precision-oncology-agent` | `autonomous-oncology-agent`, `tooluniverse-precision-oncology`, `tooluniverse-cancer-variant-interpretation` |
| Cancer variants / resistance / actionable biomarkers | `tooluniverse-cancer-variant-interpretation` | `tooluniverse-precision-oncology`, `variant-interpretation-acmg`, `clinvar-database`, `gnomad-database`, `cosmic-database` |
| Liquid biopsy / ctDNA / MRD monitoring | `liquid-biopsy-analytics-agent` or `ctdna-dynamics-mrd-agent` | `myeloma-mrd-agent`, `mrd-edge-detection-agent`, `cellfree-rna-agent`, `precision-oncology-agent` |
| Pan-cancer multi-omics / pathway characterization | `pan-cancer-multiomics-agent` | `cancer-metabolism-agent`, `tooluniverse-multi-omics-integration`, `precision-oncology-agent` |
| Tumor evolution / clonality / heterogeneity | `tumor-clonal-evolution-agent` or `tumor-heterogeneity-agent` | `chromosomal-instability-agent`, `cnv-caller-agent`, `precision-oncology-agent` |
| TMB / HRD / genome-instability biomarkers | `tumor-mutational-burden-agent` or `hrd-analysis-agent` | `chromosomal-instability-agent`, `tooluniverse-cancer-variant-interpretation`, `precision-oncology-agent` |
| Tumor microenvironment / checkpoint / immunotherapy response | `tme-immune-profiling-agent` or `immune-checkpoint-combination-agent` | `tcell-exhaustion-analysis-agent`, `tooluniverse-immunotherapy-response-prediction`, `precision-oncology-agent` |
| Organoid / PDX / translational drug response | `organoid-drug-response-agent` or `pdx-model-analysis-agent` | `microbiome-cancer-agent`, `agentd-drug-discovery`, `precision-oncology-agent` |
| Exosome / EV biomarkers / liquid signal deconvolution | `exosome-ev-analysis-agent` | `liquid-biopsy-analytics-agent`, `cellfree-rna-agent`, `precision-oncology-agent` |
| MPN / hematologic malignancy progression | `mpn-progression-monitor-agent` | `mpn-research-assistant`, `bone-marrow-ai-agent`, `chip-clonal-hematopoiesis-agent` |

## Domain 6: Clinical Trials

| Intent | Primary skills | Companion skills |
|---|---|---|
| Trial search / precision matching | `tooluniverse-clinical-trial-matching` | `trial-eligibility-agent`, `trialgpt-matching`, `clinical-trials-search`, `clinicaltrials-database` |
| Trial protocol authoring / study design | `tooluniverse-clinical-trial-design` | `clinical-trial-protocol-skill`, `tooluniverse-clinical-trial-matching` |
| Virtual cohorts / trial simulation / synthetic control context | `digital-twin-clinical-agent` | `tooluniverse-clinical-trial-design`, `tooluniverse-clinical-trial-matching`, `pyhealth` |

## Domain 7: Genomics & Variants

| Intent | Primary skills | Companion skills |
|---|---|---|
| Variant interpretation / ACMG / clinical genomics | `variant-interpretation-acmg` | `tooluniverse-variant-interpretation`, `bio-variant-calling-clinical-interpretation`, `clinvar-database`, `gnomad-database` |
| GWAS / PRS | `tooluniverse-gwas-*` or `tooluniverse-polygenic-risk-score` | `gwas-lookup`, `gwas-prs`, `pharmacogenomics-agent`, `clinpgx`, `pharmgx-reporter` |
| Gene panel design / targeted assay design | `gene-panel-design-agent` | `bio-clinical-databases-variant-prioritization`, `tooluniverse-variant-interpretation`, `clinvar-database` |
| Variant effect prediction / pathogenicity scoring | `popeve-variant-predictor-agent` | `variant-interpretation-acmg`, `clinvar-database`, `gnomad-database` |
| Multi-ancestry PRS / deep-learning risk modeling | `multi-ancestry-prs-agent` or `prs-net-deep-learning-agent` | `tooluniverse-polygenic-risk-score`, `tooluniverse-gwas-*`, `gwas-prs`, `gwas-database` |

## Domain 8: Bulk Omics

| Intent | Primary skills | Companion skills |
|---|---|---|
| Bulk RNA-seq / DEG / WGCNA / deconvolution | `bulk-deseq2-analysis` or `bulk-deg-analysis` | `bulk-wgcna-analysis`, `bulk-combat-correction`, `bulk-stringdb-ppi`, `bulk-to-single-deconvolution`, `bulk-trajblend-interpolation`, `bio-rna-*` |
| Epigenomics / DNA methylation / chromatin state | `epigenomics-methylgpt-agent` or `tooluniverse-epigenomics` | `bio-atac-seq-*`, `tooluniverse-multi-omics-integration`, `bio-causal-genomics-*` |
| Cohort-scale multi-omics integration | `simo-multiomics-integration-agent` or `tooluniverse-multi-omics-integration` | `tooluniverse-multiomic-disease-characterization`, `pan-cancer-multiomics-agent`, `tooluniverse-proteomics-analysis` |

## Domain 9: Single-cell & Spatial

| Intent | Primary skills | Companion skills |
|---|---|---|
| Single-cell atlas annotation / census | `cellagent-annotation` or `cellxgene-census` | `tooluniverse-single-cell`, `scrna-orchestrator`, `scanpy`, `anndata`, `bio-single-cell-*` |
| Single-cell RNA-seq / AnnData | `tooluniverse-single-cell` or `scrna-orchestrator` | `scanpy`, `anndata`, `scvelo`, `scvi-tools`, `bio-single-cell-*` |
| Spatial transcriptomics / spatial omics | `tooluniverse-spatial-transcriptomics` or `tooluniverse-spatial-omics-analysis` | `spatial-transcriptomics-agent`, `spatial-transcriptomics-analysis`, `bio-spatial-transcriptomics-*` |
| RNA velocity / lineage trajectory | `rna-velocity-agent` | `scvelo`, `single-trajectory`, `scrna-orchestrator`, `bio-single-cell-*` |
| Foundation-model single-cell analysis | `scfoundation-model-agent` | `cellagent-annotation`, `scanpy`, `scvi-tools`, `tooluniverse-single-cell` |
| Spatial niche / microenvironment modeling | `nicheformer-spatial-agent` | `tooluniverse-spatial-omics-analysis`, `spatial-agent`, `tme-immune-profiling-agent` |
| Deep visual proteomics / imaging-mass integration | `deep-visual-proteomics-agent` | `bio-imaging-mass-*`, `tooluniverse-proteomics-analysis`, `pathml` |

## Domain 10: Bioinformatics Pipeline

| Intent | Primary skills | Companion skills |
|---|---|---|
| Bulk omics / pipeline troubleshooting | `bio-orchestrator` | relevant `bio-*` family, `ngs-analysis`, `fastq-analysis`, `nextflow-development` |
| CNV calling / copy-number workflows | `cnv-caller-agent` | `bio-copy-number-*`, `bio-variant-calling-*`, `tooluniverse-structural-variant-analysis` |
| Long-read sequencing / isoform / SV workflows | `long-read-sequencing-agent` | `bio-longread-*`, `bio-basecalling`, `tooluniverse-structural-variant-analysis`, `bio-workflow-management-*` |

## Domain 11: CRISPR & Genome Engineering

| Intent | Primary skills | Companion skills |
|---|---|---|
| Guide design / off-target / screen interpretation | `crispr-guide-design` or `crispr-offtarget-predictor` or `tooluniverse-crispr-screen-analysis` | `bio-crispr-screens-*`, `bio-genome-engineering-*` |

## Domain 12: Systems Biology

| Intent | Primary skills | Companion skills |
|---|---|---|
| Metabolic modeling / FBA / GRN inference | `tooluniverse-systems-biology` or `cobrapy` | `bio-systems-biology-*`, `arboreto`, `tooluniverse-multi-omics-integration` |
| Mechanistic multi-omics integration / network modeling | `simo-multiomics-integration-agent` or `tooluniverse-multi-omics-integration` | `arboreto`, `tooluniverse-gene-enrichment`, `string-database` |

## Domain 13: Protein & Therapeutic Design

| Intent | Primary skills | Companion skills |
|---|---|---|
| Antibody / binder / therapeutic design | `antibody-design-agent`, `tooluniverse-protein-therapeutic-design`, or `binder-design` | `alphafold`, `rfdiffusion`, `protein-design-workflow`, `bindcraft`, `tooluniverse-antibody-engineering` |
| Structure prediction / developability / binding / QC | `boltz` or `chai` or `protein-qc` | `boltzgen`, `binding-characterization`, `adaptyv`, `alphafold`, `pdb-database` |
| Cell therapy: CAR-T / NK / AAV | `cart-design-optimizer-agent` or `armored-cart-design-agent` or `nk-cell-therapy-agent` | `aav-vector-design-agent`, `tooluniverse-immunotherapy-response-prediction`, `antibody-design-agent` |
| Cryo-EM guided therapeutic design | `cryoem-ai-drug-design-agent` or `time-resolved-cryoem-agent` | `tooluniverse-protein-structure-retrieval`, `diffdock`, `molecular-dynamics` |
| Molecular evolution / sequence optimization | `molecule-evolution-agent` | `medea-therapeutic-discovery`, `proteinmpnn`, `ligandmpnn`, `solublempnn` |

## Domain 14: Medical Imaging & Pathology

| Intent | Primary skills | Companion skills |
|---|---|---|
| Medical imaging / radiology / pathology | `medical-imaging-review` | `computational-pathology-agent`, `radgpt-radiology-reporter`, `multimodal-medical-imaging`, `pydicom` |

## Domain 15: Report Interpretation

Route by detected report type:

| Report type | Primary skills | Companion skills |
|---|---|---|
| General patient-friendly explanation | `patiently-ai` + `clinical-reports` | — |
| Health checkup / lab / blood / urine | `patiently-ai` + `lab-results` | `medical-entity-extractor` if OCR noisy |
| Radiology report text | `radgpt-radiology-reporter` + `patiently-ai` | — |
| Raw medical images (no report) | `multimodal-medical-imaging` | `patiently-ai` for lay explanation |
| Pathology / IHC / tumor pathology | `patiently-ai` + `clinical-reports` | `precision-oncology-agent` if cancer treatment context |
| Genetic / variant / PGx report | `tooluniverse-variant-interpretation` or `variant-interpretation-acmg` | `tooluniverse-cancer-variant-interpretation` (somatic), `pharmacogenomics-agent` / `clinpgx-database` (PGx) |
| Discharge summary / clinical note / SOAP | `clinical-note-summarization` + `patiently-ai` | `medical-entity-extractor` for structured extraction |
| Medication list / prescription / discharge meds | `drug-interaction-checker` + `patiently-ai` | `tooluniverse-drug-research`, `medical-entity-extractor` |
| Drug box / pill photo / label | `drug-photo` + `tooluniverse-drug-research` | `drug-labels-search`, `fda-database` |
| Trial eligibility / oncology summary doc | `trial-eligibility-agent` + `tooluniverse-clinical-trial-matching` | — |
| Emergency card / travel-ready medical summary | `emergency-card` + `patiently-ai` | `drug-interaction-checker`, `travel-health-analyzer` |

For all report tasks: extract key findings, abnormal items, qualifiers, and missing context before interpretation.

If the user also asks "下一步怎么办", add `tooluniverse-clinical-guidelines` for standard follow-up thresholds.

## Domain 16: Mental Health & Crisis

| Intent | Primary skills | Companion skills |
|---|---|---|
| Mental health crisis / urgent intervention | `crisis-detection-intervention-ai` + `crisis-response-protocol` | `mental-health-analyzer` (non-acute only) |

**Always put urgency, safety steps, and escalation resources before deeper analysis.**

## Domain 17: Literature & Databases

| Intent | Primary skills | Companion skills |
|---|---|---|
| Biomedical literature / evidence synthesis | `medical-research-toolkit` | `pubmed-search`, `medrxiv-search`, `lit-synthesizer`, `literature-review`, `bgpt-paper-search` |
| Biomedical knowledge-base lookup | `uniprot-database` or `brenda-database` or `cbioportal-database` | `drugbank-database`, `chembl-database`, `clinvar-database`, `medical-research-toolkit` |
| Omics archive / reference database lookup | `ena-database` or `geo-database` or `gtex-database` or `gwas-database` | `ensembl-database`, `gene-database`, `kegg-database`, `jaspar-database`, `interpro-database`, `metabolomics-workbench-database` |
| Compound / metabolite / network resources | `pubchem-database` or `hmdb-database` | `string-database`, `zinc-database`, `bindingdb-database`, `drugbank-database` |
| Preprint / patent / translational landscape | `biorxiv-database` or `uspto-database` | `medical-research-toolkit`, `tooluniverse-literature-deep-research` |
| Functional dependency / target context | `depmap` | `cbioportal-database`, `opentargets-database`, `string-database` |

## Domain 18: Public Health & Wellness

| Intent | Primary skills | Companion skills |
|---|---|---|
| Population trends / public-health framing / outbreak context | `epidemiologist-analyst` | `health-trend-analyzer`, `tooluniverse-disease-research`, `wearable-analysis-agent` |
| Travel / family / occupational health | `travel-health-analyzer` or `family-health-analyzer` or `occupational-health-analyzer` | `tooluniverse-clinical-guidelines`, `patiently-ai` |
| Lifestyle optimization / weight / sleep / fitness / nutrition | `nutrition-analyzer` or `sleep-analyzer` or `fitness-analyzer` or `weightloss-analyzer` | `wearable-analysis-agent`, `health-trend-analyzer` |
| Rehabilitation / speech / recovery support | `rehabilitation-analyzer` or `speech-pathology-ai` | `family-health-analyzer`, `wearable-analysis-agent` |
| TCM constitution / wellness interpretation | `tcm-constitution-analyzer` | `nutrition-analyzer`, `sleep-analyzer`, `fitness-analyzer` |

## Domain 19: Regulatory & Compliance

| Intent | Primary skills | Companion skills |
|---|---|---|
| Regulatory drafting / submission narrative / compliance writing | `regulatory-drafting` | `clinical-trial-protocol-skill`, `tooluniverse-clinical-trial-design`, `medical-research-toolkit` |
| Medical necessity / claims appeal / coverage documentation | `claims-appeals` | `prior-auth-review-skill`, `tooluniverse-clinical-guidelines`, `regulatory-drafting` |

## Domain 20: Immune Repertoire & Cellular Immunotherapy

| Intent | Primary skills | Companion skills |
|---|---|---|
| TCR / BCR repertoire profiling | `tcr-repertoire-analysis-agent` or `tooluniverse-immune-repertoire-analysis` | `bio-tcr-bcr-*`, `tcell-exhaustion-analysis-agent` |
| TCR-pMHC / neoantigen recognition | `tcr-pmhc-prediction-agent` | `bio-immunoinformatics-*`, `tcr-repertoire-analysis-agent`, `tooluniverse-immunotherapy-response-prediction` |
| T-cell exhaustion / checkpoint response | `tcell-exhaustion-analysis-agent` | `tme-immune-profiling-agent`, `immune-checkpoint-combination-agent`, `tooluniverse-immunotherapy-response-prediction` |
| Immune repertoire plus cell-therapy design | `tcr-repertoire-analysis-agent` + `cart-design-optimizer-agent` | add `aav-vector-design-agent` or `nk-cell-therapy-agent` if construct context is explicit |

---

## Composite Patterns

For common multi-domain questions, use these default combinations:

| Pattern | Description | Skill combination |
|---|---|---|
| Disease + Treatment | "X 是什么，怎么治疗？" | `tooluniverse-disease-research` + `tooluniverse-clinical-guidelines`; add `treatment-plans` for concrete plan |
| Clinical Notes + Diagnosis | "帮我看病历，做鉴别诊断" | `clinical-note-summarization` + `medical-entity-extractor` + `clinical-diagnostic-reasoning`; add `treatment-plans` if plan needed |
| Drug Profile + Safety | "某药怎么样 / 安不安全" | `tooluniverse-drug-research` + `drug-labels-search`; add `drug-interaction-checker` if multiple drugs; add `tooluniverse-pharmacovigilance` for safety-heavy |
| Cancer + Mutation + Trials | "癌症 + 突变 + 下一步" | `precision-oncology-agent` + `tooluniverse-clinical-trial-matching`; add `tooluniverse-cancer-variant-interpretation` for actionability |
| Oncology Multi-omics + Therapy | "肿瘤多组学 + 可用治疗方向" | `pan-cancer-multiomics-agent` + `precision-oncology-agent`; add `cancer-metabolism-agent` or `tooluniverse-cancer-variant-interpretation` |
| Disease Panorama + Drug/Trial | "全景综述 + 药物/试验方向" | `tooluniverse-disease-research` + `tooluniverse-drug-research` or `tooluniverse-drug-repurposing`; add `tooluniverse-clinical-trial-matching` |
| Report + Next Steps | "解读报告 + 下一步怎么办" | Report-first route + `tooluniverse-clinical-guidelines` for follow-up thresholds |
| Prescription Review | "帮我看处方 / 用药单 / 多药联用" | `drug-interaction-checker` + `tooluniverse-drug-research`; add `medical-entity-extractor` for OCR |
| PGx + Medication | "基因结果影响用药吗" | `pharmacogenomics-agent` + `clinpgx-database`; add `tooluniverse-clinical-guidelines` for dose adjustment |
| Liquid Biopsy + Treatment | "ctDNA/MRD 解读 + 治疗意义" | `liquid-biopsy-analytics-agent` + `precision-oncology-agent` |
| Bulk RNA-seq Analysis | "差异分析 / WGCNA / 去卷积" | `bulk-deseq2-analysis`; add `bulk-wgcna-analysis`, `bulk-combat-correction`, `bulk-stringdb-ppi` as needed |
| Single-cell Trajectory | "细胞轨迹 / velocity / fate" | `rna-velocity-agent` + `scvelo`; add `scrna-orchestrator` for upstream QC |
| TCR / Immune Repertoire | "TCR组库 / neoantigen / 免疫耗竭" | `tcr-repertoire-analysis-agent` + `tcr-pmhc-prediction-agent` or `tcell-exhaustion-analysis-agent` |
| CRISPR Workflow | "sgRNA 设计 / off-target / screen" | `crispr-guide-design`; add `tooluniverse-crispr-screen-analysis` for pooled screen |
| Cell Therapy Design | "CAR-T / NK / AAV 方案" | `cart-design-optimizer-agent`; add `aav-vector-design-agent` for vector |
| Systems Biology | "代谢建模 / FBA / 调控网络" | `tooluniverse-systems-biology` or `cobrapy`; add `arboreto` for GRN |
| Public Health Snapshot | "睡眠 / 运动 / 营养 / 趋势评估" | route to the narrowest analyzer; add `wearable-analysis-agent` or `health-trend-analyzer` for longitudinal context |
| Emergency Card / Travel Summary | "帮我整理紧急医疗卡 / 出行用药摘要" | `emergency-card` + `patiently-ai`; add `drug-interaction-checker` for medication safety |
| Digital Twin Trial | "虚拟患者 / 数字孪生 + 试验设计" | `digital-twin-clinical-agent` + `tooluniverse-clinical-trial-design` |
| Regulatory Submission | "申报文书 / 医学必要性 / appeal" | `regulatory-drafting` + `claims-appeals` or `clinical-trial-protocol-skill` depending on deliverable |
| Crisis Triage | "精神危机 / 紧急干预" | `crisis-detection-intervention-ai` + `crisis-response-protocol` |
| Omics File + Clinical | "VCF/BAM/h5ad + 临床意义" | Detect modality → narrowest `bio-*` skill + disease/oncology companion |
