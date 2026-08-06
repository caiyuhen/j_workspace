const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  TabStopType, TabStopPosition, TableOfContents, HeadingLevel,
  BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber,
  PageBreak,
} = require("docx");

// ── Style constants ──
const FONT = "微软雅黑";
const FONT_EN = "Arial";
const COLOR_PRIMARY = "1F4E79";
const COLOR_ACCENT = "2E75B6";
const COLOR_LIGHT = "D6E4F0";
const COLOR_TEXT = "333333";
const COLOR_GRAY = "808080";
const COLOR_WHITE = "FFFFFF";

// ── Border helpers ──
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const thinBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const hdrBorder = { style: BorderStyle.SINGLE, size: 4, color: COLOR_PRIMARY };

// ── Paragraph helpers ──
function emptyPara(sp = 120) {
  return new Paragraph({ spacing: { before: sp, after: sp }, children: [new TextRun("")] });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60, line: 340 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: 22, color: COLOR_TEXT, ...(opts.run || {}) })],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: COLOR_PRIMARY })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, font: FONT, size: 26, bold: true, color: COLOR_ACCENT })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: FONT, size: 23, bold: true, color: COLOR_TEXT })],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "csrBullets", level },
    spacing: { before: 40, after: 40, line: 340 },
    children: [new TextRun({ text, font: FONT, size: 22, color: COLOR_TEXT })],
  });
}

function numItem(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "csrNumbers", level },
    spacing: { before: 40, after: 40, line: 340 },
    children: [new TextRun({ text, font: FONT, size: 22, color: COLOR_TEXT })],
  });
}

function ph(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60, line: 340 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text: `【${text}】`, font: FONT, size: 22, color: COLOR_GRAY, italics: true })],
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// ── Table helpers ──
function makeCell(text, opts = {}) {
  return new TableCell({
    borders: thinBorders,
    width: { size: opts.width || 2340, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      spacing: { before: 20, after: 20 },
      children: [new TextRun({ text, font: FONT, size: 20, color: COLOR_TEXT, bold: opts.bold || false })],
    })],
  });
}

function makeRow(cells, opts = {}) {
  return new TableRow({
    children: cells,
    tableHeader: opts.header || false,
  });
}

// ── COVER PAGE ──
function coverPage() {
  return [
    emptyPara(300), emptyPara(200), emptyPara(200),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 100 },
      children: [new TextRun({ text: "CONFIDENTIAL", font: FONT_EN, size: 22, color: "CC0000", bold: true })],
    }),
    emptyPara(200), emptyPara(200), emptyPara(200),
    // Title
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 100 },
      children: [new TextRun({ text: "临床试验报告", font: FONT, size: 56, bold: true, color: COLOR_PRIMARY })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 300 },
      children: [new TextRun({ text: "Clinical Study Report", font: FONT_EN, size: 32, color: COLOR_ACCENT, bold: true })],
    }),
    // Divider
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 100, after: 300 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: COLOR_ACCENT, space: 4 } },
      children: [new TextRun("")],
    }),
    emptyPara(200),
    // Study info
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80 },
      children: [new TextRun({ text: "【试验名称 / Study Title】", font: FONT, size: 28, color: COLOR_TEXT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 80 },
      children: [new TextRun({ text: "试验方案编号：【Protocol No.】", font: FONT, size: 22, color: COLOR_TEXT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 80 },
      children: [new TextRun({ text: "IND / CTA 编号：【IND/CTA No.】", font: FONT, size: 22, color: COLOR_TEXT })],
    }),
    emptyPara(200), emptyPara(200),
    // Sponsor
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 60 },
      children: [new TextRun({ text: "申办方：【Sponsor】", font: FONT, size: 24, color: COLOR_TEXT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 60 },
      children: [new TextRun({ text: "试验药物：【Investigational Product】", font: FONT, size: 24, color: COLOR_TEXT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 60 },
      children: [new TextRun({ text: "研究阶段：【Phase I / II / III / IV】", font: FONT, size: 24, color: COLOR_TEXT })],
    }),
    emptyPara(300),
    // Version
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 40 },
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: COLOR_ACCENT, space: 6 } },
      children: [new TextRun({ text: "报告版本：V【X.X】", font: FONT, size: 22, color: COLOR_ACCENT, bold: true })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 40 },
      children: [new TextRun({ text: "报告日期：【YYYY年MM月DD日】", font: FONT, size: 22, color: COLOR_ACCENT })],
    }),
    pageBreak(),
  ];
}

// ── TABLE OF CONTENTS ──
function tocPage() {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 400 },
      children: [new TextRun({ text: "目  录", font: FONT, size: 36, bold: true, color: COLOR_PRIMARY })],
    }),
    new TableOfContents("Table of Contents", {
      hyperlink: true,
      headingStyleRange: "1-3",
    }),
    pageBreak(),
  ];
}

// ── CHAPTER 1: Synopsis ──
function chapter1Synopsis() {
  return [
    h1("1. 概要（Synopsis）"),
    body("本章为临床试验报告的概要部分，应简明扼要地总结试验的关键信息，篇幅一般不超过 2-3 页。"),
    h2("1.1 试验名称与编号"),
    bullet("试验名称：【填写试验完整名称】"),
    bullet("试验方案编号：【填写编号】"),
    bullet("申办方内部试验编号：【填写编号】"),
    bullet("EudraCT / ClinicalTrials.gov 注册号：【填写注册号】"),
    h2("1.2 申办方信息"),
    bullet("申办方名称：【Sponsor Name】"),
    bullet("法定代表人 / 联系人：【姓名】"),
    bullet("地址 / 电话 / 邮箱：【联系信息】"),
    h2("1.3 试验药物信息"),
    bullet("试验药物通用名：【Generic Name】"),
    bullet("试验药物商品名（如适用）：【Trade Name】"),
    bullet("药物代码 / 研究代号：【Code】"),
    bullet("剂型与规格：【Dosage Form & Strength】"),
    bullet("给药途径：【Route of Administration】"),
    bullet("适应症：【Indication】"),
    h2("1.4 试验设计与目标"),
    h3("1.4.1 试验目的"),
    bullet("主要目的：【Primary Objective】"),
    bullet("次要目的：【Secondary Objectives】"),
    h3("1.4.2 试验设计"),
    bullet("试验类型：对照 / 非对照；随机 / 非随机；盲法类型；多中心 / 单中心"),
    bullet("对照类型：安慰剂对照 / 阳性对照 / 剂量对照 / 无对照"),
    bullet("分组设计：【描述分组方案】"),
    bullet("试验分期：【Phase】"),
    h3("1.4.3 受试者人群"),
    bullet("目标入组人数：【N】"),
    bullet("实际入组人数：【N】"),
    bullet("入组标准概述：【关键入组标准】"),
    h2("1.5 主要结果概述"),
    h3("1.5.1 有效性结果"),
    ph("请概述主要有效性终点结果，包括统计显著性（p值）、效应量及置信区间"),
    h3("1.5.2 安全性结果"),
    ph("请概述安全性结果，包括不良事件发生率、严重不良事件、导致停药的不良事件等"),
    h3("1.5.3 药代动力学结果（如适用）"),
    ph("请概述关键PK参数及结果"),
    h2("1.6 结论"),
    ph("请简述试验的主要结论，包括有效性、安全性及对后续研发的意义"),
    pageBreak(),
  ];
}

// ── CHAPTER 2: List of Abbreviations ──
function chapter2Abbrev() {
  const abbrevData = [
    ["AE", "Adverse Event / 不良事件"],
    ["SAE", "Serious Adverse Event / 严重不良事件"],
    ["AESI", "Adverse Event of Special Interest / 特别关注不良事件"],
    ["AR", "Adverse Reaction / 不良反应"],
    ["SUSAR", "Suspected Unexpected Serious Adverse Reaction / 可疑非预期严重不良反应"],
    ["CI", "Confidence Interval / 置信区间"],
    ["CRF", "Case Report Form / 病例报告表"],
    ["CRO", "Contract Research Organization / 合同研究组织"],
    ["DSMB", "Data Safety Monitoring Board / 数据安全监查委员会"],
    ["EC", "Ethics Committee / 伦理委员会"],
    ["GCP", "Good Clinical Practice / 药物临床试验质量管理规范"],
    ["IB", "Investigator's Brochure / 研究者手册"],
    ["ICH", "International Council for Harmonisation / 国际人用药品注册技术协调会"],
    ["ICF", "Informed Consent Form / 知情同意书"],
    ["IEC", "Independent Ethics Committee / 独立伦理委员会"],
    ["IND", "Investigational New Drug / 新药临床试验申请"],
    ["IRB", "Institutional Review Board / 机构审查委员会"],
    ["MedDRA", "Medical Dictionary for Regulatory Activities / 国际医学用语词典"],
    ["PK", "Pharmacokinetics / 药代动力学"],
    ["PD", "Pharmacodynamics / 药效学"],
    ["PP", "Per Protocol / 符合方案集"],
    ["SAE", "Serious Adverse Event / 严重不良事件"],
    ["SDV", "Source Data Verification / 源数据核查"],
    ["SOP", "Standard Operating Procedure / 标准操作规程"],
    ["TEAE", "Treatment-Emergent Adverse Event / 治疗期出现的不良事件"],
    ["FAS", "Full Analysis Set / 全分析集"],
    ["SS", "Safety Set / 安全性分析集"],
  ];

  const rows = [
    makeRow([
      makeCell("缩写 / Abbreviation", { width: 2200, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("全称与定义 / Definition", { width: 7160, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
    ], { header: true }),
  ];
  abbrevData.forEach(([abbr, def]) => {
    rows.push(makeRow([
      makeCell(abbr, { width: 2200, bold: true }),
      makeCell(def, { width: 7160 }),
    ]));
  });

  return [
    h1("2. 缩略语与术语定义"),
    body("本报告中所使用的主要缩略语及术语定义如下表所示："),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [2200, 7160],
      rows,
    }),
    pageBreak(),
  ];
}

// ── CHAPTER 3: Ethics ──
function chapter3Ethics() {
  return [
    h1("3. 伦理（Ethics）"),
    h2("3.1 伦理委员会审查"),
    bullet("各试验中心伦理委员会名称及审查日期"),
    bullet("伦理批准文件编号"),
    bullet("伦理跟踪审查及方案修正的审批记录"),
    ph("请列出所有参与中心的伦理委员会名称、批准日期及批件编号"),
    h2("3.2 受试者知情同意"),
    bullet("知情同意书（ICF）的版本及修订日期"),
    bullet("知情同意签署流程说明"),
    bullet("特殊人群（如未成年人、认知障碍者）知情同意的处理"),
    h2("3.3 受试者隐私与数据保密"),
    bullet("受试者身份信息保护措施"),
    bullet("数据脱敏与匿名化处理方法"),
    bullet("电子数据系统的访问权限控制"),
    h2("3.4 试验注册与结果公开"),
    bullet("临床试验注册平台及注册号"),
    bullet("结果公开计划与时间安排"),
    pageBreak(),
  ];
}

// ── CHAPTER 4: Investigators ──
function chapter4Investigators() {
  const invRows = [
    makeRow([
      makeCell("中心编号", { width: 1000, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("主要研究者", { width: 1800, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("试验机构", { width: 2800, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("科室", { width: 1860, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("入组人数", { width: 1900, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
    ], { header: true }),
  ];

  return [
    h1("4. 研究者与试验管理结构"),
    h2("4.1 主要研究者（PI）列表"),
    body("以下为参与本试验的各中心主要研究者信息："),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [1000, 1800, 2800, 1860, 1900],
      rows: invRows,
    }),
    ph("请在表格中填写各中心PI姓名、机构名称、科室及入组人数"),
    h2("4.2 申办方试验管理团队"),
    bullet("医学负责人：【姓名、职务】"),
    bullet("项目经理：【姓名、职务】"),
    bullet("数据管理员：【姓名、职务】"),
    bullet("生物统计师：【姓名、职务】"),
    bullet("安全性监测负责人：【姓名、职务】"),
    h2("4.3 合同研究组织（CRO）"),
    bullet("CRO名称：【如适用】"),
    bullet("委托范围：【数据管理 / 统计分析 / 监查 / 等】"),
    bullet("CRO联系人及联系方式：【填写】"),
    h2("4.4 数据安全监查委员会（DSMB/DMC）"),
    bullet("委员会成员：【姓名、单位、专业领域】"),
    bullet("章程与运作方式：【描述】"),
    bullet("会议频率及审查记录：【描述】"),
    pageBreak(),
  ];
}

// ── CHAPTER 5: Introduction ──
function chapter5Intro() {
  return [
    h1("5. 引言"),
    h2("5.1 试验药物背景"),
    ph("请描述试验药物的药学、非临床药理毒理、既往临床研究信息，包括药物作用机制、适应症开发依据等"),
    h2("5.2 适应症与临床需求"),
    ph("请阐述目标适应症的流行病学、现有治疗手段的局限性及未满足的临床需求"),
    h2("5.3 试验依据与合理性"),
    bullet("基于非临床研究数据的剂量选择依据"),
    bullet("基于既往临床研究（如I期数据）的设计依据"),
    bullet("试验设计的科学性论证"),
    h2("5.4 研究者手册（IB）版本"),
    bullet("IB版本号：【Version X.X】"),
    bullet("IB日期：【YYYY-MM-DD】"),
    pageBreak(),
  ];
}

// ── CHAPTER 6: Objectives ──
function chapter6Objectives() {
  return [
    h1("6. 试验目的"),
    h2("6.1 主要目的"),
    ph("请明确列出试验的主要目的，通常与主要终点对应"),
    h2("6.2 次要目的"),
    ph("请列出试验的次要目的，通常与次要终点对应"),
    h2("6.3 探索性目的（如适用）"),
    ph("请列出探索性目的，如生物标志物、PK/PD关联分析等"),
    h2("6.4 终点指标"),
    h3("6.4.1 主要终点"),
    bullet("终点指标名称：【Primary Endpoint】"),
    bullet("评价时间点：【Time Point】"),
    bullet("评价方法：【Assessment Method】"),
    h3("6.4.2 次要终点"),
    bullet("有效性次要终点：【列出】"),
    bullet("安全性次要终点：【列出】"),
    h3("6.4.3 探索性终点（如适用）"),
    ph("请列出探索性终点指标"),
    pageBreak(),
  ];
}

// ── CHAPTER 7: Investigational Plan ──
function chapter7Plan() {
  return [
    h1("7. 试验方案"),
    h2("7.1 总体设计"),
    bullet("设计类型：【随机 / 开放 / 对照 / 双盲 / 多中心 等】"),
    bullet("试验分期：【Phase】"),
    bullet("预计持续时间：【受试者参与时长、试验总周期】"),
    bullet("中期分析计划：【如适用，描述中期分析的设计与决策规则】"),
    h2("7.2 试验设计图"),
    ph("请插入试验流程图（Schema），展示受试者从筛选到结束试验的完整流程"),
    h2("7.3 受试者选择标准"),
    h3("7.3.1 纳入标准"),
    numItem("年龄：【如18-65岁】"),
    numItem("性别：【男女不限 / 仅男性 / 仅女性】"),
    numItem("疾病诊断标准：【根据XX指南/标准确诊】"),
    numItem("疾病严重程度：【如适用】"),
    numItem("知情同意：签署书面ICF"),
    ph("请补充完整的纳入标准列表"),
    h3("7.3.2 排除标准"),
    numItem("对试验药物或辅料过敏者"),
    numItem("合并严重心血管、肝肾功能不全者"),
    numItem("妊娠或哺乳期女性（如适用）"),
    numItem("入组前X天内参加过其他临床试验"),
    numItem("研究者认为不适合入组的其他情况"),
    ph("请补充完整的排除标准列表"),
    h3("7.3.3 中止与退出标准"),
    numItem("受试者主动退出"),
    numItem("出现SAE或不可耐受的AE"),
    numItem("严重方案违背"),
    numItem("妊娠"),
    numItem("失访"),
    h2("7.4 治疗方案"),
    h3("7.4.1 试验药物"),
    bullet("药物名称 / 代码：【填写】"),
    bullet("剂型与规格：【填写】"),
    bullet("给药途径：【口服 / 静脉注射 / 皮下注射 等】"),
    bullet("给药剂量与频率：【填写】"),
    bullet("给药周期：【填写】"),
    h3("7.4.2 对照药物（如适用）"),
    bullet("对照药物名称：【填写】"),
    bullet("剂型与规格：【填写】"),
    bullet("给药方案：【填写】"),
    bullet("盲法实施：【描述随机化与盲法操作流程】"),
    h3("7.4.3 合并用药限制"),
    bullet("禁止使用的合并药物：【列出】"),
    bullet("允许使用的合并药物：【列出】"),
    h2("7.5 评价方法与时间安排"),
    ph("请插入评价时间表（Schedule of Assessments），列出各访视点的检查项目"),
    h2("7.6 统计分析计划"),
    h3("7.6.1 分析集定义"),
    bullet("全分析集（FAS）：所有随机化并接受至少一次治疗的受试者"),
    bullet("符合方案集（PP）：完成试验且无重大方案违背的受试者"),
    bullet("安全性分析集（SS）：接受至少一次治疗并有安全性数据的受试者"),
    h3("7.6.2 样本量估算"),
    ph("请描述样本量计算的方法、假设参数（如效应量、alpha、power等）及计算结果"),
    h3("7.6.3 统计分析方法"),
    bullet("主要终点分析方法：【描述统计模型与方法】"),
    bullet("次要终点分析方法：【描述】"),
    bullet("安全性分析方法：【描述】"),
    bullet("缺失数据处理方法：【描述】"),
    pageBreak(),
  ];
}

// ── CHAPTER 8: Disposition ──
function chapter8Disposition() {
  const dispRows = [
    makeRow([
      makeCell("项目", { width: 4680, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("试验组", { width: 2340, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("对照组", { width: 2340, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
    ], { header: true }),
  ];
  const dispItems = [
    "随机化人数", "入组人数", "完成试验人数", "退出人数",
    "退出原因 - 不良事件", "退出原因 - 缺乏疗效", "退出原因 - 失访",
    "退出原因 - 撤回知情同意", "退出原因 - 其他",
  ];
  dispItems.forEach(item => {
    dispRows.push(makeRow([
      makeCell(item, { width: 4680 }),
      makeCell("【N】", { width: 2340, align: AlignmentType.CENTER }),
      makeCell("【N】", { width: 2340, align: AlignmentType.CENTER }),
    ]));
  });

  return [
    h1("8. 受试者处置"),
    h2("8.1 受试者流转概览"),
    body("以下表格展示受试者在试验各阶段的处置情况："),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [4680, 2340, 2340],
      rows: dispRows,
    }),
    h2("8.2 方案违背"),
    bullet("重大方案违背人数：【N】"),
    bullet("其他方案违背人数：【N】"),
    bullet("方案违背对试验结果的影响评估：【描述】"),
    h2("8.3 数据集划分"),
    bullet("FAS人数：试验组【N】 / 对照组【N】"),
    bullet("PPS人数：试验组【N】 / 对照组【N】"),
    bullet("SS人数：试验组【N】 / 对照组【N】"),
    pageBreak(),
  ];
}

// ── CHAPTER 9: Efficacy ──
function chapter9Efficacy() {
  return [
    h1("9. 有效性评价"),
    h2("9.1 分析数据集"),
    body("本章有效性分析基于全分析集（FAS）和符合方案集（PPS）进行。"),
    h2("9.2 基线特征"),
    h3("9.2.1 人口学特征"),
    ph("请插入人口学特征表，包括年龄、性别、种族、BMI等基线比较"),
    h3("9.2.2 疾病基线特征"),
    ph("请插入疾病相关基线特征表，如病程、疾病严重程度、既往治疗等"),
    h2("9.3 主要有效性结果"),
    h3("9.3.1 主要终点结果"),
    ph("请描述主要终点的分析结果，包括各组疗效指标、组间差异、统计检验结果（p值、效应量、95%CI）"),
    h3("9.3.2 主要终点亚组分析"),
    ph("请描述按预设亚组（如年龄、性别、基线严重程度等）的亚组分析结果"),
    h2("9.4 次要有效性结果"),
    ph("请逐一描述各次要终点的结果及统计分析"),
    h2("9.5 探索性分析结果（如适用）"),
    ph("请描述探索性分析的结果，如PK/PD关联、生物标志物分析等"),
    h2("9.6 有效性结果小结"),
    ph("请对有效性结果进行综合小结，评价试验药物的有效性"),
    pageBreak(),
  ];
}

// ── CHAPTER 10: Safety ──
function chapter10Safety() {
  const aeRows = [
    makeRow([
      makeCell("不良事件类别", { width: 3120, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("试验组 n(%)", { width: 3120, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
      makeCell("对照组 n(%)", { width: 3120, shading: COLOR_PRIMARY, bold: true, align: AlignmentType.CENTER }),
    ], { header: true }),
  ];
  const aeItems = [
    "任何TEAE", "药物相关TEAE", "严重不良事件（SAE）",
    "导致停药的TEAE", "导致死亡的TEAE", "特别关注不良事件（AESI）",
  ];
  aeItems.forEach(item => {
    aeRows.push(makeRow([
      makeCell(item, { width: 3120 }),
      makeCell("【n (X.X%)】", { width: 3120, align: AlignmentType.CENTER }),
      makeCell("【n (X.X%)】", { width: 3120, align: AlignmentType.CENTER }),
    ]));
  });

  return [
    h1("10. 安全性评价"),
    h2("10.1 暴露情况"),
    bullet("暴露人数：试验组【N】 / 对照组【N】"),
    bullet("暴露时长（中位数）：试验组【X天】 / 对照组【X天】"),
    bullet("总暴露量：【X 患者·天】"),
    h2("10.2 不良事件（AE）概览"),
    body("以下表格汇总各组治疗期出现的不良事件（TEAE）发生情况："),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3120, 3120, 3120],
      rows: aeRows,
    }),
    h2("10.3 常见不良事件"),
    ph("请插入按系统器官分类（SOC）和首选语（PT）排列的常见TEAE表格（发生率≥X%），按发生率降序排列"),
    h2("10.4 严重不良事件（SAE）"),
    bullet("SAE总数：试验组【N例】 / 对照组【N例】"),
    bullet("死亡事件：【N例】"),
    ph("请逐一列出所有SAE的详细信息，包括受试者编号、事件名称、发生时间、严重程度、因果关系判断、转归等"),
    h2("10.5 导致停药的不良事件"),
    ph("请列出导致永久停药的TEAE详细信息"),
    h2("10.6 特别关注不良事件（AESI）"),
    ph("请描述预设的AESI及其发生情况"),
    h2("10.7 实验室检查异常"),
    h3("10.7.1 血液学检查"),
    ph("请描述有临床意义的实验室异常及发生率"),
    h3("10.7.2 血生化检查"),
    ph("请描述有临床意义的实验室异常及发生率"),
    h3("10.7.3 尿常规检查"),
    ph("请描述有临床意义的实验室异常及发生率"),
    h2("10.8 生命体征与心电图"),
    bullet("有临床意义生命体征异常：【描述】"),
    bullet("有临床意义心电图异常：【描述】"),
    h2("10.9 安全性结果小结"),
    ph("请对安全性数据进行综合分析与小结，评估试验药物的安全性特征"),
    pageBreak(),
  ];
}

// ── CHAPTER 11: PK/PD (if applicable) ──
function chapter11PK() {
  return [
    h1("11. 药代动力学评价（如适用）"),
    h2("11.1 分析方法"),
    bullet("生物样本分析方法：【LC-MS/MS 等】"),
    bullet("方法验证概况：【描述】"),
    h2("11.2 PK参数"),
    bullet("Cmax：【填写】"),
    bullet("Tmax：【填写】"),
    bullet("AUC0-t：【填写】"),
    bullet("AUC0-∞：【填写】"),
    bullet("t1/2：【填写】"),
    bullet("CL/F：【填写】"),
    bullet("Vd/F：【填写】"),
    h2("11.3 PK分析结果"),
    ph("请描述PK参数的统计分析结果，包括均值、SD、CV%等"),
    h2("11.4 PK/PD关联分析（如适用）"),
    ph("请描述PK与PD指标之间的关联分析结果"),
    pageBreak(),
  ];
}

// ── CHAPTER 12: Discussion ──
function chapter12Discussion() {
  return [
    h1("12. 讨论与总体结论"),
    h2("12.1 有效性讨论"),
    ph("请结合试验结果与已有文献，对试验药物的有效性进行讨论，包括与预期结果的比较、与同类药物的横向比较等"),
    h2("12.2 安全性讨论"),
    ph("请对安全性数据进行综合讨论，包括安全性的总体特征、特别关注的安全性问题、风险管理建议等"),
    h2("12.3 试验局限性"),
    ph("请客观分析本试验存在的局限性，如样本量、试验设计、执行偏差等"),
    h2("12.4 总体结论"),
    ph("请给出试验的总体结论，包括有效性、安全性的综合评价以及对后续开发的建议"),
    pageBreak(),
  ];
}

// ── CHAPTER 13: References ──
function chapter13References() {
  return [
    h1("13. 参考文献"),
    body("以下为本报告引用的主要参考文献："),
    numItem("ICH E3: Structure and Content of Clinical Study Reports"),
    numItem("ICH E6(R2): Guideline for Good Clinical Practice"),
    numItem("ICH E8(R1): General Considerations for Clinical Studies"),
    numItem("ICH E9: Statistical Principles for Clinical Trials"),
    numItem("ICH M4(R4): Common Technical Document"),
    numItem("国家药品监督管理局《药物临床试验质量管理规范》（2020年修订）"),
    ph("请补充其他参考文献，按照引用顺序排列"),
    pageBreak(),
  ];
}

// ── CHAPTER 14: Appendices ──
function chapter14Appendices() {
  return [
    h1("14. 附录"),
    h2("14.1 试验方案及修正记录"),
    bullet("原版方案版本号及日期"),
    bullet("方案修正历史记录（版本号、日期、修正内容概述）"),
    h2("14.2 病例报告表（CRF）样表"),
    ph("请附上CRF样表"),
    h2("14.3 统计分析计划（SAP）"),
    ph("请附上正式版本的SAP文件"),
    h2("14.4 数据管理计划与报告"),
    bullet("数据管理计划（DMP）"),
    bullet("数据管理报告"),
    h2("14.5 知情同意书（ICF）"),
    ph("请附上各版本ICF"),
    h2("14.6 伦理委员会批件"),
    ph("请附上各中心伦理委员会批准文件"),
    h2("14.7 研究者履历"),
    ph("请附上各PI的CV及GCP培训证书"),
    h2("14.8 安全性报告列表"),
    bullet("SAE列表（完整详情）"),
    bullet("SUSAR报告"),
    bullet("年度安全性报告（DSUR）"),
    h2("14.9 受试者列表"),
    ph("请附上受试者入组/完成/退出汇总表"),
    h2("14.10 术语表"),
    ph("如有其他需定义的特定术语，请在此列出"),
  ];
}

// ── Build Document ──
const doc = new Document({
  creator: "WorkBuddy",
  title: "临床试验报告（CSR）模板",
  description: "Clinical Study Report Template following ICH E3 guideline",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22, color: COLOR_TEXT } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: COLOR_ACCENT },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT, color: COLOR_TEXT },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "csrBullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ],
      },
      {
        reference: "csrNumbers",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.LOWER_LETTER, text: "%2)", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 }, // A4
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: COLOR_ACCENT, space: 4 } },
            children: [new TextRun({ text: "临床试验报告（CSR）  |  CONFIDENTIAL", font: FONT, size: 18, color: COLOR_GRAY })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "第 ", font: FONT, size: 18, color: COLOR_GRAY }),
              new TextRun({ children: [PageNumber.CURRENT], font: FONT_EN, size: 18, color: COLOR_GRAY }),
              new TextRun({ text: " 页 / 共 ", font: FONT, size: 18, color: COLOR_GRAY }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT_EN, size: 18, color: COLOR_GRAY }),
              new TextRun({ text: " 页", font: FONT, size: 18, color: COLOR_GRAY }),
            ],
          })],
        }),
      },
      children: [
        ...coverPage(),
        ...tocPage(),
        ...chapter1Synopsis(),
        ...chapter2Abbrev(),
        ...chapter3Ethics(),
        ...chapter4Investigators(),
        ...chapter5Intro(),
        ...chapter6Objectives(),
        ...chapter7Plan(),
        ...chapter8Disposition(),
        ...chapter9Efficacy(),
        ...chapter10Safety(),
        ...chapter11PK(),
        ...chapter12Discussion(),
        ...chapter13References(),
        ...chapter14Appendices(),
      ],
    },
  ],
});

const outputPath = "D:\\workspace\\doc\\2026-08-06-15-43-36\\临床试验报告_CSR模板.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log("CSR template generated: " + outputPath);
});
