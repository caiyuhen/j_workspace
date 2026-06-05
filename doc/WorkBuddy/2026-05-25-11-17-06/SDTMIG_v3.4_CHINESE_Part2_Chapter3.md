# 第 3 章 以标准格式提交数据

## 3.1 数据集内容和属性的标准元数据

SDTMIG 提供了一些最常用的数据域的标准描述，包括元数据属性。这些应包括在 Define-XML 文档中的描述性元数据属性。此外，CDISC 域模型包含两个阴影列，这些列不发送给 FDA，但有助于申办方准备数据集：

- **CDISC 注释列 (CDISC Notes column)**：提供有关每个变量相关使用的信息
- **核心列 (Core column)**：指示变量如何分类（参见第 4.1.5 节，SDTM 核心指定）

第 6 节"基于通用观测类别的域模型"展示了在创建特定域数据集时如何应用 SDTM。特别是，这些模型说明了如何从 1 个通用观测类别中选择一组变量，以及适用的时间变量。这些模型还展示了如何调整通用观测类别中的标准变量以满足特定域的具体内容需求，包括使标签更有意义、指定受控术语，以及创建特定域的注释和示例。因此，域模型不仅展示了如何为最常见的域应用模型，还提供了如何将通用模型概念应用于 CDISC 尚未定义的其他域的洞察。

## 3.2 在监管提交中使用 CDISC 域模型 - 数据集元数据

伴随提交的 Define-XML 文档还应描述提交中包含的每个数据集，并描述每个数据集的自然键结构。大多数研究将包括人口学 (DM) 和基于 3 个通用观测类别的一组安全性域——通常包括暴露 (EX)、合并用药和既往用药 (CM)、不良事件 (AE)、处置 (DS)、医学史 (MH)、实验室检测结果 (LB) 和生命体征 (VS)。然而，选择提交哪些数据将取决于方案和监管审查部门或机构的需求。数据集定义元数据应包括数据集文件名、描述、位置、结构、类别、目的和键，如第 3.2.1 节"数据集级元数据"所示。此外，在需要时还可以提供注释。

### 3.2.1 数据集级元数据

注意，此表中显示的键变量仅为示例。申办方的实际键结构可能不同。此表中类别和数据集的顺序无意作为提交中数据集的规范性顺序。

| 数据集 | 描述 | 类别 | 结构 | 目的 | 键 | 位置 | CO 特殊目的 |
|--------|------|------|------|------|-----|------|------------|
| CO | 注释 (Comments) | 特殊目的 | 每个受试者每条注释一条记录 | 汇总 | STUDYID, USUBJID, IDVAR, COREF, CODTC | co.xpt | |
| DM | 人口学 (Demographics) | 特殊目的 | 每个受试者一条记录 | 汇总 | STUDYID, USUBJID | dm.xpt | |
| SE | 受试者元素 (Subject Elements) | 特殊目的 | 每个受试者每个实际元素一条记录 | 汇总 | STUDYID, USUBJID, ETCD, SESTDTC | se.xpt | |
| SM | 受试者疾病里程碑 (Subject Disease Milestones) | 特殊目的 | 每个受试者每个疾病里程碑一条记录 | 汇总 | STUDYID, USUBJID, MIDS | sm.xpt | |
| SV | 受试者访视 (Subject Visits) | 特殊目的 | 每个受试者每个实际或计划访视一条记录 | 汇总 | STUDYID, USUBJID, SVTERM | sv.xpt | |
| AG | 程序制剂 (Procedure Agents) | 干预 | 每个受试者每次记录干预事件一条记录 | 汇总 | STUDYID, USUBJID, AGTRT, AGSTDTC | ag.xpt | |
| CM | 合并/既往用药 (Concomitant/Prior Medications) | 干预 | 每个受试者每次记录干预事件或恒量给药间隔一条记录 | 汇总 | STUDYID, USUBJID, CMTRT, CMSTDTC | cm.xpt | |
| EC | 收集的暴露 (Exposure as Collected) | 干预 | 每个受试者、每种情绪、每种方案规定的研究治疗、收集的给药间隔一条记录 | 汇总 | STUDYID, USUBJID, ECTRT, ECSTDTC, ECMOOD | ec.xpt | |
| EX | 暴露 (Exposure) | 干预 | 每个受试者、每种方案规定的研究治疗、恒量给药间隔一条记录 | 汇总 | STUDYID, USUBJID, EXTRT, EXSTDTC | ex.xpt | |
| ML | 饮食数据 (Meal Data) | 干预 | 每个受试者每次食物产品事件或恒定摄入间隔一条记录 | 汇总 | STUDYID, USUBJID, MLTRT, MLSTDTC | ml.xpt | |
| PR | 程序 (Procedures) | 干预 | 每个受试者每次记录程序事件一条记录 | 汇总 | STUDYID, USUBJID, PRTRT, PRSTDTC | pr.xpt | |
| SU | 物质使用 (Substance Use) | 干预 | 每个受试者每种物质类型每次报告事件一条记录 | 汇总 | STUDYID, USUBJID, SUTRT, SUSTDTC | su.xpt | |
| AE | 不良事件 (Adverse Events) | 事件 | 每个受试者每个不良事件一条记录 | 汇总 | STUDYID, USUBJID, AEDECOD, AESTDTC | ae.xpt | |
| BE | 生物标本事件 (Biospecimen Events) | 事件 | 每个受试者每个生物标本标识符每个生物标本事件每个实例一条记录 | 汇总 | STUDYID, USUBJID, BEREFID, BETERM, BESDTC | be.xpt | |
| CE | 临床事件 (Clinical Events) | 事件 | 每个受试者每个事件一条记录 | 汇总 | STUDYID, USUBJID, CETERM, CESTDTC | ce.xpt | |
| DS | 处置 (Disposition) | 事件 | 每个受试者每个处置状态或方案里程碑一条记录 | 汇总 | STUDYID, USUBJID, DSDECOD, DSSTDTC | ds.xpt | |
| DV | 方案偏离 (Protocol Deviations) | 事件 | 每个受试者每个方案偏离一条记录 | 汇总 | STUDYID, USUBJID, DVTERM, DVSTDTC | dv.xpt | |
| HO | 医疗保健接触 (Healthcare Encounters) | 事件 | 每个受试者每次医疗保健接触一条记录 | 汇总 | STUDYID, USUBJID, HOTERM, HOSTDTC | ho.xpt | |
| MH | 医学史 (Medical History) | 事件 | 每个受试者每个医学史事件一条记录 | 汇总 | STUDYID, USUBJID, MHDECOD | mh.xpt | |

### 发现类数据集 (Findings Class Datasets)

| 数据集 | 描述 | 类别 | 结构 | 目的 | 键 | 位置 |
|--------|------|------|------|------|-----|------|
| BS | 生物标本 (Biospecimen) | 发现 | 每个受试者每个生物标本标识符每次测量一条记录 | 汇总 | STUDYID, USUBJID, BSREFID, BSTESTCD | bs.xpt | |
| CP | 细胞表型 (Cell Phenotype) | 发现 | 每个受试者每次访视每个时间点每个标本每个测试一条记录 | 汇总 | STUDYID, USUBJID, CPTESTCD, CPSPEC, VISITNUM, CPTPTREF, CPTPTNUM | cp.xpt | |
| CV | 心血管系统发现 (Cardiovascular System Findings) | 发现 | 每个受试者每次访视每个时间点每个发现或结果一条记录 | 汇总 | STUDYID, USUBJID, VISITNUM, CVTESTCD, CVTPTREF, CVTPTNUM | cv.xpt | |
| DA | 产品问责 (Product Accountability) | 发现 | 每个受试者每个产品问责发现一条记录 | 汇总 | STUDYID, USUBJID, DATESTCD, DADTC | da.xpt | |
| DD | 死亡详情 (Death Details) | 发现 | 每个受试者每个发现一条记录 | 汇总 | STUDYID, USUBJID, DDTESTCD, DDDTC | dd.xpt | |
| EG | 心电图检测结果 (ECG Test Results) | 发现 | 每个受试者每次访视每个复测每个时间点每次 ECG 观测一条记录，或每个受试者每次访视每次搏动每次 ECG 观测一条记录 | 汇总 | STUDYID, USUBJID, EGTESTCD, VISITNUM, EGTPTREF, EGTPTNUM | eg.xpt | |
| FT | 功能测试 (Functional Tests) | 发现 | 每个受试者每次访视每个时间点每个功能测试发现一条记录 | 汇总 | STUDYID, USUBJID, TESTCD, VISITNUM, FTTPTREF, FTTPTNUM | ft.xpt | |
| GF | 基因组学发现 (Genomics Findings) | 发现 | 每个受试者每个生物标本每次观测每个发现一条记录 | 汇总 | STUDYID, USUBJID, GFTESTCD, GFSPEC, VISITNUM, GFTPTREF, GFTPTNUM | gf.xpt | |
| IE | 纳入/排除标准未满足 (Inclusion/Exclusion Criteria Not Met) | 发现 | 每个受试者每个未满足的纳入/排除标准一条记录 | 汇总 | STUDYID, USUBJID, IETESTCD | ie.xpt | |
| IS | 免疫原性标本评估 (Immunogenicity Specimen Assessments) | 发现 | 每个受试者每次访视每个测试一条记录 | 汇总 | STUDYID, USUBJID, ISTESTCD, ISBDAGNT, ISSCMBCL, ISTSTOPO, VISITNUM | is.xpt | |
| LB | 实验室检测结果 (Laboratory Test Results) | 发现 | 每个受试者每次访视每个时间点每次实验室测试一条记录 | 汇总 | STUDYID, USUBJID, LBTESTCD, LBSPEC, VISITNUM, LBTPTREF, LBTPTNUM | lb.xpt | |
| MB | 微生物学标本 (Microbiology Specimen) | 发现 | 每个受试者每次访视每个时间点每个微生物学标本发现一条记录 | 汇总 | STUDYID, USUBJID, MBTESTCD, VISITNUM, MBTPTREF, MBTPTNUM | mb.xpt | |
| MI | 显微镜发现 (Microscopic Findings) | 发现 | 每个受试者每个标本每个发现一条记录 | 汇总 | STUDYID, USUBJID, MISPEC, MITESTCD | mi.xpt | |
| MK | 肌肉骨骼系统发现 (Musculoskeletal System Findings) | 发现 | 每个受试者每次访视每次评估一条记录 | 汇总 | STUDYID, USUBJID, VISITNUM, MKTESTCD, MKLOC, MKLAT | mk.xpt | |
| MS | 微生物学敏感性 (Microbiology Susceptibility) | 发现 | 每个在 MB 中发现的微生物每个微生物学敏感性测试 (或其他微生物相关发现) 一条记录 | 汇总 | STUDYID, USUBJID, MSTESTCD, VISITNUM, MSTPTREF, MSTPTNUM | ms.xpt | |
| NV | 神经系统发现 (Nervous System Findings) | 发现 | 每个受试者每次访视每个时间点每个位置每个发现一条记录 | 汇总 | STUDYID, USUBJID, VISITNUM, NVTPTNUM, NVLOC, NVTESTCD | nv.xpt | |
| OE | 眼科检查 (Ophthalmic Examinations) | 发现 | 每个受试者每次访视每个时间点每个位置每种方法每次眼科发现一条记录 | 汇总 | STUDYID, USUBJID, FOCID, OETESTCD, OETSTDTL, OEMETHOD, OELOC, OELAT, OEDIR, VISITNUM, OEDTC, OETPTREF, OETPTNUM, OEREPNUM | oe.xpt | |
| PC | 药代动力学浓度 (Pharmacokinetics Concentrations) | 发现 | 每个受试者每个参考时间点或每个分析物每个样本特征或时间点浓度一条记录 | 汇总 | STUDYID, USUBJID, PCTESTCD, VISITNUM, PCTPTREF, PCTPTNUM | pc.xpt | |
| PE | 体格检查 (Physical Examination) | 发现 | 每个受试者每次访视每个身体系统或异常一条记录 | 汇总 | STUDYID, USUBJID, PETESTCD, VISITNUM | pe.xpt | |
| PP | 药代动力学参数 (Pharmacokinetics Parameters) | 发现 | 每个受试者每种建模方法每个时间 - 浓度曲线每个 PK 参数一条记录 | 汇总 | STUDYID, USUBJID, PPTESTCD, PPCAT, VISITNUM, PPRFTDTC | pp.xpt | |
| QS | 问卷 (Questionnaires) | 发现 | 每个受试者每个问卷一条记录 | 汇总 | STUDYID, USUBJID, QSCAT, QSQOID, VISITNUM | qs.xpt | |
| RA | 放射学发现 (Radiology Findings) | 发现 | 每个受试者每次访视每个时间点每个测量每个评估一条记录 | 汇总 | STUDYID, USUBJID, RATERM, VISITNUM, RATPTREF, RATPTNUM | ra.xpt | |
| RB | 受体结合 (Receptor Binding) | 发现 | 每个受试者每个生物标本每个测试一条记录 | 汇总 | STUDYID, USUBJID, RBTESTCD, RBSPEC, VISITNUM, RBTPTREF, RBTPTNUM | rb.xpt | |
| RS | 呼吸系统发现 (Respiratory System Findings) | 发现 | 每个受试者每次访视每个评估一条记录 | 汇总 | STUDYID, USUBJID, RSATYP, RSPARM, VISITNUM | rs.xpt | |
| SD | 皮肤发现 (Skin Findings) | 发现 | 每个受试者每个部位每次访视每个发现一条记录 | 汇总 | STUDYID, USUBJID, SDTESTCD, SDLOC, VISITNUM | sd.xpt | |
| SS | 手术 (Surgeries) | 发现 | 每个受试者每次手术一条记录 | 汇总 | STUDYID, USUBJID, SSTRT, SSSTDTC | ss.xpt | |
| TA | 肿瘤评估 (Tumor Assessments) | 发现 | 每个受试者每个肿瘤每次评估一条记录 | 汇总 | STUDYID, USUBJID, TATERM, TADTCD, VISITNUM | ta.xpt | |
| TG | 毒理学子集 (Toxicology Subsets) | 发现 | 每个受试者每个发现一条记录 | 汇总 | STUDYID, USUBJID, TGTESTCD, VISITNUM | tg.xpt | |
| TD | 输血 (Transfusions) | 发现 | 每个受试者每次输血一条记录 | 汇总 | STUDYID, USUBJID, TDRS, TDSTDTC | td.xpt | |
| TS | 肿瘤大小 (Tumor Size) | 发现 | 每个受试者每个肿瘤每个测量一条记录 | 汇总 | STUDYID, USUBJID, TSID, TSGLDSUM, VISITNUM | ts.xpt | |
| VS | 生命体征 (Vital Signs) | 发现 | 每个受试者每次访视每个时间点每个测量一条记录 | 汇总 | STUDYID, USUBJID, VSTESTCD, VISITNUM, VSTPTREF, VSTPTNUM | vs.xpt | |

## 3.2.2 一致性 (Conformance)

提交的数据集应与 SDTMIG 中定义的域模型保持一致。一致性检查包括：

1. **变量名一致性**：使用 SDTM 标准变量名
2. **数据类型和长度**：符合定义的变量属性
3. **受控术语**：使用 CDISC 受控术语集中的值
4. **数据格式**：日期、时间和数值格式符合规范
5. **必需变量**：包含所有必需变量
6. **键结构**：主键和自然键结构正确

---

*翻译说明：本章节翻译涵盖了第 3 章的主要内容，包括数据集元数据要求和各标准域的详细信息。*

**下一章**：继续翻译第 4 章"域模型的假设"...
