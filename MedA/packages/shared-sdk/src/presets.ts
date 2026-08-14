export type DemoPresetKey =
  | "sglt2i_ckd"
  | "sglt2i_hfredef"
  | "met_cv_presto"
  | "glp1_mace_rws"
  | "sglt2i_dka_safety"
  | "met_lifestyle_predm";

export type DemoPreset = {
  key: DemoPresetKey;
  label: string;
  badge: string;
  expected_hits_hint: string;
  project_name: string;
  query_name: string;
  boolean_text: string;
  selected_sources: ["pubmed"];
  pico: { p: string; i: string; c: string; o: string };
  filters?: {
    study_type?: Array<"rct" | "sr" | "rct_and_sr">;
    pubmed_mindate?: string;
    pubmed_maxdate?: string;
  };
};

export const DEMO_PRESETS: DemoPreset[] = [
  {
    key: "sglt2i_ckd",
    label: "💧 糖尿病肾病 SGLT2i",
    badge: "经典适应症",
    expected_hits_hint: "预计 1.5k+ hits",
    project_name: "MedA-Demo-Diabetes-CKD-2026",
    query_name: "SGLT2i in CKD (PubMed real-data demo)",
    boolean_text:
      "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR canagliflozin[Title/Abstract]) AND (chronic kidney disease[Title/Abstract] OR CKD[Title/Abstract] OR diabetic nephropathies[MeSH Major Topic]) AND randomised controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "adult with type 2 diabetes mellitus and CKD stage 2-4 or macroalbuminuria",
      i: "SGLT2 inhibitor add-on to RAAS blockade",
      c: "placebo or standard of care without SGLT2i",
      o: "composite renal endpoint (eGFR decline ≥50% / ESRD / renal death) ; change in eGFR slope ; 3P-MACE ; AE of genital mycotic infection / DKA / hypovolemia",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "sglt2i_hfredef",
    label: "❤️ 达格列净 HFrEF DAPA-HF / DAPA-CKD",
    badge: "标杆研究",
    expected_hits_hint: "含 DAPA-HF、DAPA-CKD 原始 + follow-up",
    project_name: "MedA-Demo-HF-2026",
    query_name: "Dapagliflozin landmark HFrEF/CKD trials",
    boolean_text:
      "(DAPA-HF[Title/Abstract] OR DAPA-CKD[Title/Abstract] OR (dapagliflozin[Title/Abstract] AND (heart failure with reduced ejection fraction[Title/Abstract] OR HFrEF[Title/Abstract] OR chronic kidney disease[Title/Abstract]))) AND randomised controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "HFrEF LVEF ≤40% with/without T2DM; CKD eGFR 25-75 + uACR >200",
      i: "dapagliflozin 10 mg once daily",
      c: "matching placebo",
      o: "CV death or worsening HF composite; renal composite; change in NT-proBNP / KCCQ",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "met_cv_presto",
    label: "💊 二甲双胍 CV PRESTO",
    badge: "RCT 重分析",
    expected_hits_hint: "RCT + pooled subgroup",
    project_name: "MedA-Demo-Metformin-CV-2026",
    query_name: "Metformin PRESTO CV outcomes reanalysis",
    boolean_text:
      "(PRESTO[Title/Abstract] OR (metformin[Title/Abstract] AND cardiovascular[Title/Abstract] AND (prediabetes[Title/Abstract] OR insulin resistance[Title/Abstract]))) AND randomized controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "prediabetes / insulin resistance with CV risk factors but no established ASCVD",
      i: "metformin extended-release +/- lifestyle intervention",
      c: "placebo or lifestyle-only",
      o: "MACE (CV death / MI / stroke) ; change in LDL-C / SBP / Hba1c",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "glp1_mace_rws",
    label: "📈 GLP-1 RA MACE 真实世界",
    badge: "RCT vs RWS 对照",
    expected_hits_hint: "RCT + RWS 双队列",
    project_name: "MedA-Demo-GLP1-RA-2026",
    query_name: "GLP-1 RA MACE: RCT vs real-world comparison",
    boolean_text:
      "(glucagon-like peptide-1 receptor agonist[Title/Abstract] OR GLP-1 RA[Title/Abstract] OR liraglutide[Title/Abstract] OR semaglutide[Title/Abstract] OR dulaglutide[Title/Abstract] OR tirzepatide[Title/Abstract]) AND (major adverse cardiovascular events[Title/Abstract] OR MACE[Title/Abstract] OR cardiovascular outcomes[Title/Abstract]) AND ((randomized controlled trial[pt]) OR (real-world[Title/Abstract] OR retrospective[Title/Abstract] OR cohort[Title/Abstract]))",
    selected_sources: ["pubmed"],
    pico: {
      p: "T2DM with established ASCVD or high CV risk",
      i: "GLP-1 RA (injectable or oral) as add-on",
      c: "DPP-4 inhibitor / sulfonylurea / basal insulin / placebo",
      o: "3P-MACE (CV death, non-fatal MI, non-fatal stroke) ; all-cause mortality ; severe hypoglycaemia",
    },
    filters: { study_type: ["rct_and_sr"] },
  },
  {
    key: "sglt2i_dka_safety",
    label: "⚠️ SGLT2i 酮症酸中毒 Safety",
    badge: "风险点",
    expected_hits_hint: "RCT post-hoc + RWS + case series",
    project_name: "MedA-Demo-SGLT2i-Safety-2026",
    query_name: "SGLT2i DKA euglycemic safety signal",
    boolean_text:
      "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR ertugliflozin[Title/Abstract]) AND (diabetic ketoacidosis[Title/Abstract] OR DKA[Title/Abstract] OR euglycemic ketoacidosis[Title/Abstract] OR ketosis[Title/Abstract])",
    selected_sources: ["pubmed"],
    pico: {
      p: "T2DM or T1DM on SGLT2i around peri-operative / fasting / severe illness periods",
      i: "SGLT2i continued or paused peri-event window",
      c: "same population without SGLT2i exposure",
      o: "event rate of DKA / euglycemic DKA ; median bicarbonate / gap / anion gap at diagnosis",
    },
  },
  {
    key: "met_lifestyle_predm",
    label: "🏃 Metformin + Lifestyle Prediabetes",
    badge: "一级预防",
    expected_hits_hint: "DPP + follow-up + meta-analysis",
    project_name: "MedA-Demo-Prediabetes-Prevention-2026",
    query_name: "Metformin vs lifestyle in prediabetes: prevention of T2DM",
    boolean_text:
      "(diabetes prevention program[Title/Abstract] OR DPP[Title/Abstract] OR prediabetes[Title/Abstract]) AND (metformin[Title/Abstract] AND (lifestyle[Title/Abstract] OR diet AND exercise[Title/Abstract])) AND (progression to type 2 diabetes[Title/Abstract] OR incidence of type 2 diabetes[Title/Abstract])",
    selected_sources: ["pubmed"],
    pico: {
      p: "adult with prediabetes (IFG / IGT / elevated HbA1c 5.7-6.4%) without prior CV event",
      i: "metformin 850 mg BID + intensive lifestyle (≥7% weight loss, 150 min/wk exercise)",
      c: "placebo + standard lifestyle brochure",
      o: "time to T2DM diagnosis (primary) ; regression to normoglycaemia ; change in weight / Hba1c at 3y",
    },
    filters: { pubmed_mindate: "1996/01/01" },
  },
];

export const DEMO_PRESET_BY_KEY = Object.fromEntries(
  DEMO_PRESETS.map((p) => [p.key, p]),
) as Record<DemoPresetKey, DemoPreset>;
