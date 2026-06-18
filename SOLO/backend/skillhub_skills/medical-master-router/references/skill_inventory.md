# Skill Inventory

Installed-skill catalog for `medical-master-router`. Use as a reference index when the routing table needs exact skill names.

This file is intentionally organized by **family and subdomain** instead of brittle exact counts, so it stays useful as the local `skills/` directory grows.

---

## Family Coverage Rules

### `tooluniverse-*`

Use when the task is retrieval-heavy, report-first, and evidence-based. Key members by subdomain:

| Subdomain | Skills |
|---|---|
| Disease & guidelines | `tooluniverse-disease-research`, `tooluniverse-clinical-guidelines`, `tooluniverse-rare-disease-diagnosis`, `tooluniverse-infectious-disease` |
| Drug & safety | `tooluniverse-drug-research`, `tooluniverse-drug-drug-interaction`, `tooluniverse-drug-repurposing`, `tooluniverse-drug-target-validation`, `tooluniverse-network-pharmacology`, `tooluniverse-pharmacovigilance`, `tooluniverse-adverse-event-detection`, `tooluniverse-chemical-compound-retrieval`, `tooluniverse-chemical-safety` |
| Oncology | `tooluniverse-precision-oncology`, `tooluniverse-precision-medicine-stratification`, `tooluniverse-cancer-variant-interpretation`, `tooluniverse-immunotherapy-response-prediction` |
| Trials | `tooluniverse-clinical-trial-matching`, `tooluniverse-clinical-trial-design` |
| Genomics & variants | `tooluniverse-variant-interpretation`, `tooluniverse-variant-analysis`, `tooluniverse-structural-variant-analysis`, `tooluniverse-polygenic-risk-score`, `tooluniverse-gwas-*` |
| Omics | `tooluniverse-single-cell`, `tooluniverse-spatial-transcriptomics`, `tooluniverse-spatial-omics-analysis`, `tooluniverse-rnaseq-deseq2`, `tooluniverse-expression-data-retrieval`, `tooluniverse-epigenomics`, `tooluniverse-metabolomics`, `tooluniverse-metabolomics-analysis`, `tooluniverse-proteomics-analysis`, `tooluniverse-multi-omics-integration`, `tooluniverse-multiomic-disease-characterization` |
| Protein & structure | `tooluniverse-protein-therapeutic-design`, `tooluniverse-protein-interactions`, `tooluniverse-protein-structure-retrieval`, `tooluniverse-antibody-engineering`, `tooluniverse-binder-discovery` |
| Other | `tooluniverse-crispr-screen-analysis`, `tooluniverse-systems-biology`, `tooluniverse-immune-repertoire-analysis`, `tooluniverse-phylogenetics`, `tooluniverse-image-analysis`, `tooluniverse-literature-deep-research`, `tooluniverse-sequence-retrieval`, `tooluniverse-gene-enrichment`, `tooluniverse-statistical-modeling`, `tooluniverse-target-research` |

### `bio-*`

Use when the task is about molecular biology, sequencing, omics data, or computational biology workflows. Route by subfamily prefix:

| Subfamily prefix | Domain |
|---|---|
| `bio-single-cell-*` | Single-cell workflows |
| `bio-spatial-transcriptomics-*` | Spatial omics |
| `bio-data-visualization-*` | Biomedical visualization |
| `bio-clinical-databases-*` | Clinical genomics databases |
| `bio-genome-assembly-*` | Genome assembly |
| `bio-crispr-screens-*` | CRISPR screen analysis |
| `bio-hi-c-*` | Hi-C / 3D genomics |
| `bio-flow-cytometry-*` | Flow cytometry |
| `bio-imaging-mass-*` | Imaging mass cytometry |
| `bio-machine-learning-*` | Biomedical ML |
| `bio-variant-calling-*` | Variant calling |
| `bio-genome-intervals-*` | Genome intervals |
| `bio-read-qc-*` | Read QC |
| `bio-atac-seq-*` | ATAC-seq |
| `bio-population-genetics-*` | Population genetics |
| `bio-clip-seq-*` | CLIP-seq |
| `bio-genome-engineering-*` | Genome engineering |
| `bio-systems-biology-*` | Systems biology |
| `bio-epidemiological-genomics-*` | Epidemiological genomics |
| `bio-comparative-genomics-*` | Comparative genomics |
| `bio-ribo-seq-*` | Ribo-seq |
| `bio-small-rna-*` | Small RNA-seq |
| `bio-tcr-bcr-*` | TCR/BCR analysis |
| `bio-causal-genomics-*` | Causal genomics |
| `bio-alignment-*`, `bio-read-*`, `bio-sam-bam-*`, `bio-fastq-*` | Alignment, QC, BAM/FASTQ |
| `bio-variant-*`, `bio-vcf-*`, `bio-copy-number-*`, `bio-longread-*` | Variant calling, VCF, CNV, SV |
| `bio-rna-*`, `bio-de-*`, `bio-differential-*`, `bio-splicing-*` | Bulk RNA-seq, DE, splicing |
| `bio-proteomics-*`, `bio-metabolomics-*`, `bio-microbiome-*`, `bio-metagenomics-*` | Omics-specific |
| `bio-structural-biology-*`, `bio-immunoinformatics-*` | Structure, immunology |
| `bio-workflow-management-*`, `bio-workflows-*` | Reproducible pipelines |

When a user gives a file without specifying the analysis goal, detect file type first, then choose the narrowest `bio-*` branch.

### `clinical-*`

Use for charting, reasoning, decision documents, and clinical NLP:

`clinical-decision-support`, `clinical-diagnostic-reasoning`, `clinical-nlp-extractor`, `clinical-note-summarization`, `clinical-reports`, `clinical-trial-protocol-skill`, `clinical-trials-search`

### `medical-*`

Use for broad medical extraction, research, imaging, and specialty briefs:

`medical-entity-extractor`, `medical-imaging-review`, `medical-research-toolkit`, `medical-specialty-briefs`, `medical-master-router`

### `drug-*` / `chem*` / `pharm*` cluster

Use for compounds, labels, safety, medicinal chemistry, screening:

`drug-interaction-checker`, `drug-labels-search`, `drug-photo`, `drugbank-database`, `fda-database`, `medchem`, `rdkit`, `deepchem`, `datamol`, `diffdock`, `pharmacogenomics-agent`, `clinpgx`, `clinpgx-database`, `pharmgx-reporter`, `chemical-property-lookup`, `chemistry-agent`

### `bulk-*`

Use for cohort-level bulk transcriptomics and downstream interpretation:

`bulk-deseq2-analysis`, `bulk-deg-analysis`, `bulk-wgcna-analysis`, `bulk-combat-correction`, `bulk-stringdb-ppi`, `bulk-to-single-deconvolution`, `bulk-trajblend-interpolation`

### Single-cell & spatial ecosystems

- **Single-cell**: `scrna-orchestrator`, `scanpy`, `scvelo`, `scvi-tools`, `anndata`, `cellagent-annotation`, `cellxgene-census`, `single-annotation`, `single-clustering`, `single-downstream-analysis`, `single-preprocessing`, `single-trajectory`, `single-multiomics`, `single-to-spatial-mapping`, `single-cellphone-db`, `single-cell-rna-qc`, `rna-velocity-agent`, `scfoundation-model-agent`
- **Spatial**: `spatial-agent`, `spatial-epigenomics-agent`, `spatial-transcriptomics-agent`, `spatial-transcriptomics-analysis`, `spatial-tutorials`, `nicheformer-spatial-agent`, `deep-visual-proteomics-agent`

### Oncology companions

Use as second-line routes when cancer subtype or assay context is explicit:

`precision-oncology-agent`, `autonomous-oncology-agent`, `pan-cancer-multiomics-agent`, `cancer-metabolism-agent`, `liquid-biopsy-analytics-agent`, `ctdna-dynamics-mrd-agent`, `myeloma-mrd-agent`, `mrd-edge-detection-agent`, `cellfree-rna-agent`, `tumor-clonal-evolution-agent`, `tumor-heterogeneity-agent`, `tumor-mutational-burden-agent`, `tme-immune-profiling-agent`, `immune-checkpoint-combination-agent`, `microbiome-cancer-agent`, `organoid-drug-response-agent`, `pdx-model-analysis-agent`, `chip-clonal-hematopoiesis-agent`, `chromosomal-instability-agent`, `hrd-analysis-agent`, `mpn-progression-monitor-agent`, `mpn-research-assistant`, `bone-marrow-ai-agent`, `cnv-caller-agent`, `cbioportal-database`, `exosome-ev-analysis-agent`

### Genomics & risk stratification

`gene-panel-design-agent`, `hemoglobinopathy-analysis-agent`, `popeve-variant-predictor-agent`, `multi-ancestry-prs-agent`, `prs-net-deep-learning-agent`, `variant-interpretation-acmg`, `tooluniverse-variant-interpretation`, `clinvar-database`, `gnomad-database`, `gwas-prs`, `gwas-lookup`

### Drug discovery agents

`agentd-drug-discovery`, `chematagent-drug-discovery`, `chemcrow-drug-discovery`, `medea-therapeutic-discovery`, `drug-discovery-search`, `protac-design-agent`, `molecular-glue-discovery-agent`, `tpd-ternary-complex-agent`, `bio-admet-prediction`, `bio-virtual-screening`, `molecule-evolution-agent`

### Protein & therapeutic design

`antibody-design-agent`, `binder-design`, `bindcraft`, `protein-design-workflow`, `protein-structure-prediction`, `proteinmpnn`, `ligandmpnn`, `solublempnn`, `alphafold`, `alphafold-database`, `rfdiffusion`, `esm`, `pdb`, `pdb-database`, `boltz`, `boltzgen`, `chai`, `binding-characterization`, `protein-qc`, `adaptyv`, `cryoem-ai-drug-design-agent`, `time-resolved-cryoem-agent`

### Cell therapy & immune repertoire

`cart-design-optimizer-agent`, `armored-cart-design-agent`, `nk-cell-therapy-agent`, `aav-vector-design-agent`, `tcr-repertoire-analysis-agent`, `tcr-pmhc-prediction-agent`, `tcell-exhaustion-analysis-agent`, `tooluniverse-immune-repertoire-analysis`

### Clinical care add-ons

`chatehr-clinician-assistant`, `digital-twin-clinical-agent`, `pyhealth`, `ehr-fhir-integration`, `treatment-plans`, `patiently-ai`, `clinical-reports`, `lab-results`, `emergency-card`

### Imaging & pathology

`medical-imaging-review`, `multimodal-medical-imaging`, `multimodal-radpath-fusion-agent`, `computational-pathology-agent`, `radgpt-radiology-reporter`, `radiomics-pathomics-fusion-agent`, `pathml`, `histolab`, `pydicom`, `imaging-data-commons`

### Crisis & mental health

`crisis-detection-intervention-ai`, `crisis-response-protocol`, `mental-health-analyzer`

### Public health & wellness

`epidemiologist-analyst`, `travel-health-analyzer`, `family-health-analyzer`, `health-trend-analyzer`, `occupational-health-analyzer`, `rehabilitation-analyzer`, `speech-pathology-ai`, `weightloss-analyzer`, `nutrition-analyzer`, `sleep-analyzer`, `fitness-analyzer`, `wearable-analysis-agent`, `tcm-constitution-analyzer`, `modern-drug-rehab-computer`

### Regulatory & compliance

`regulatory-drafting`, `claims-appeals`, `prior-auth-coworker`, `prior-auth-review-skill`

### Generalist / orchestrator agents

`biomni-general-agent`, `biomni-research-agent`, `bio-orchestrator`, `scrna-orchestrator`, `medical-master-router`

### Secondary helpers (not primary medical routes)

- **Literature**: `arxiv-search`, `bgpt-paper-search`, `medrxiv-search`, `research-literature`, `research-lookup`, `literature-review`, `lit-synthesizer`, `pubmed-search`, `pubmed-database`
- **Databases**: `openalex-database`, `opentargets-database`, `chembl-database`, `drugbank-database`, `reactome-database`, `clinvar-database`, `gnomad-database`, `brenda-database`, `uniprot-database`, `bindingdb-database`, `cbioportal-database`, `cosmic-database`, `monarch-database`, `ena-database`, `ensembl-database`, `gene-database`, `geo-database`, `gtex-database`, `gwas-database`, `hmdb-database`, `interpro-database`, `jaspar-database`, `kegg-database`, `pubchem-database`, `string-database`, `zinc-database`, `biorxiv-database`, `uspto-database`, `metabolomics-workbench-database`, `depmap`
- **Output helpers**: `pdf`, `docx`, `pptx`, `xlsx`, `scientific-writing`, `scientific-slides`, `scientific-schematics`, `data-visualization-biomedical`
- **Browser/search**: `agent-browser`, `deep-research`, `perplexity-search`, `multi-search-engine`

---

## Audit Notes

- No bundled executable script is required for this router.
- Main behavior lives in markdown instructions only.
- No credential collection, shell execution, external downloads, or hidden side-effects.
- Lists are representative routing indices; the source of truth for installed names remains the local `skills/` directory.
- Risk level: **P2 / low risk**
