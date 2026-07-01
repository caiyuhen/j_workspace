"""
MedAIagents Office 文档导入导出功能演示

本脚本演示如何将项目中的各类数据导出为 Word / Excel / PowerPoint 文件，
以及如何从 Office 文档中导入数据。
"""
import sys
import os
sys.path.insert(0, '../src')

OUTPUT_DIR = './export_outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

from medai.export import (
    PaperExporter, GrantProposalExporter, ResponseLetterExporter, ProtocolExporter,
    MetaAnalysisExporter, BudgetExporter, JournalDatabaseExporter, SurvivalDataExporter,
    ResearchPresentationExporter, ImagingTeachingExporter, BioinformaticsReportExporter,
    WordImporter, ExcelImporter,
)


def demo_word_export():
    """演示 Word 文档导出"""
    print("\n" + "=" * 60)
    print("📄 Word 文档导出演示")
    print("=" * 60)

    # 1. 导出论文
    print("\n1. 医学论文 (IMRaD 结构)")
    exporter = PaperExporter()
    paper = {
        "title": "基于深度学习的糖尿病视网膜病变筛查系统",
        "authors": "李明, 张伟, 王芳, 等",
        "abstract": "目的：开发一种基于深度学习的糖尿病视网膜病变自动筛查系统。方法：收集10,000张眼底图像...",
        "keywords": ["糖尿病视网膜病变", "深度学习", "人工智能", "筛查"],
        "introduction": "糖尿病视网膜病变(DR)是糖尿病最常见的微血管并发症...",
        "methods": "我们使用ResNet-50作为骨干网络，在10,000张标注眼底图像上进行训练...",
        "results": "模型在测试集上的AUC达到0.954，敏感性92.3%，特异性89.7%...",
        "discussion": "本研究开发的AI筛查系统性能优于既往报道的同类系统...",
        "conclusion": "基于深度学习的DR筛查系统具有较高的准确性和临床应用价值。",
        "references": [
            "Gulshan V, et al. Development and Validation of a Deep Learning Algorithm for Detection of Diabetic Retinopathy. JAMA. 2016;316(22):2402-2410.",
            "Ting DSW, et al. Deep Learning in Ophthalmology. Lancet Digital Health. 2019;1(1):e10-e11.",
        ]
    }
    path = os.path.join(OUTPUT_DIR, "demo_paper.docx")
    exporter.export_paper(paper, path)
    print(f"   ✅ 已导出: {path}")

    # 2. 导出基金申请书
    print("\n2. 国自然基金申请书")
    exporter2 = GrantProposalExporter()
    proposal = {
        "title": "基于多模态融合的肺癌早期诊断AI模型研究",
        "grant_type": "国家自然科学基金面上项目",
        "research_area": "医学人工智能",
        "applicant": "张教授",
        "institution": "某医科大学附属医院",
        "rationale": "肺癌是全球发病率和死亡率最高的恶性肿瘤之一。早期诊断是提高肺癌患者生存率的关键...",
        "research_content": "构建融合CT影像、临床指标和基因组学的多模态深度学习模型...",
        "objectives": "开发一款具有临床实用价值的肺癌早期诊断AI系统",
        "key_problems": "多模态数据对齐、小样本学习、模型可解释性",
        "methodology": "采用Transformer架构进行多模态特征融合...",
        "feasibility": "团队具备丰富的医学AI研究经验和充足的临床数据资源",
        "innovation": "首次将基因组学数据与影像组学进行深度融合",
        "timeline": "第一年：数据收集与预处理；第二年：模型开发；第三年：临床验证",
        "expected_outcomes": "发表SCI论文3-5篇，申请发明专利2项",
        "budget": {
            "items": [
                {"name": "设备费", "amount": 20.0, "notes": "高性能GPU工作站"},
                {"name": "材料费", "amount": 35.0, "notes": "试剂、耗材"},
                {"name": "测试化验加工费", "amount": 15.0, "notes": "基因检测外送"},
                {"name": "差旅费", "amount": 10.0, "notes": "学术会议、合作交流"},
                {"name": "会议费", "amount": 5.0, "notes": "项目研讨会"},
                {"name": "出版/文献/信息传播费", "amount": 3.0, "notes": "论文版面费"},
                {"name": "劳务费", "amount": 15.0, "notes": "研究生助研津贴"},
                {"name": "专家咨询费", "amount": 2.0, "notes": "临床专家咨询"},
            ],
            "total": 105.0
        }
    }
    path = os.path.join(OUTPUT_DIR, "demo_proposal.docx")
    exporter2.export_proposal(proposal, path)
    print(f"   ✅ 已导出: {path}")

    # 3. 导出 Response Letter
    print("\n3. 审稿回复信 (Response Letter)")
    exporter3 = ResponseLetterExporter()
    letter = {
        "manuscript_id": "JDI-2025-0842",
        "title": "Deep Learning-Based Screening for Diabetic Retinopathy",
        "authors": "Li M, Zhang W, Wang F, et al.",
        "responses": [
            {
                "comment": "Major concern: The sample size of 10,000 may not be sufficient. Please justify.",
                "response": "Thank you for this important comment. We have added a detailed power analysis...",
                "changes": "Added power analysis section (page 5, lines 120-135)."
            },
            {
                "comment": "Minor: Please update the reference list to include the latest 2024 guidelines.",
                "response": "Thank you for the suggestion. We have updated the references accordingly.",
                "changes": "Added 3 new references (Ref. 12, 15, 18)."
            },
        ]
    }
    path = os.path.join(OUTPUT_DIR, "demo_response_letter.docx")
    exporter3.export_response_letter(letter, path)
    print(f"   ✅ 已导出: {path}")

    # 4. 导出 RCT 方案
    print("\n4. RCT 临床试验方案")
    exporter4 = ProtocolExporter()
    protocol = {
        "study_info": {
            "title": "二甲双胍联合SGLT2抑制剂治疗2型糖尿病的多中心RCT",
            "study_type": "RCT",
            "phase": "III期",
            "indication": "2型糖尿病",
            "duration_months": 36
        },
        "study_objectives": {
            "primary": "评价二甲双胍联合SGLT2抑制剂治疗2型糖尿病的有效性和安全性",
            "secondary": "探索联合治疗对心血管结局的影响"
        },
        "endpoints": {
            "primary": "治疗24周后HbA1c较基线的变化",
            "secondary": ["空腹血糖", "体重变化", "血压", "血脂", "心血管事件"]
        },
        "inclusion_criteria": [
            "符合WHO 2型糖尿病诊断标准",
            "年龄18-75岁",
            "HbA1c 7.0%-10.5%",
            "签署知情同意书"
        ],
        "exclusion_criteria": [
            "1型糖尿病或其他类型糖尿病",
            "严重肝肾功能不全",
            "妊娠或哺乳期妇女",
            "对研究药物过敏"
        ],
        "sample_size": {"total": 500, "note": "基于power=0.90, alpha=0.05"},
        "statistical_analysis": {
            "primary": "协方差分析(ANCOVA)",
            "significance_level": "双侧α=0.05"
        },
        "ethical_considerations": {
            "irb_approval": "须经各研究中心伦理委员会批准",
            "informed_consent": "所有受试者须签署书面知情同意"
        }
    }
    path = os.path.join(OUTPUT_DIR, "demo_protocol.docx")
    exporter4.export_protocol(protocol, path)
    print(f"   ✅ 已导出: {path}")


def demo_excel_export():
    """演示 Excel 文档导出"""
    print("\n" + "=" * 60)
    print("📊 Excel 文档导出演示")
    print("=" * 60)

    # 1. Meta 分析结果
    print("\n1. Meta 分析结果")
    exporter = MetaAnalysisExporter()
    meta = {
        "studies": [
            {"name": "Zhang 2020", "a_events": 45, "a_total": 150, "b_events": 30, "b_total": 150, "effect_size": 0.52},
            {"name": "Li 2021", "a_events": 38, "a_total": 120, "b_events": 22, "b_total": 120, "effect_size": 0.48},
            {"name": "Wang 2022", "a_events": 52, "a_total": 180, "b_events": 35, "b_total": 180, "effect_size": 0.55},
            {"name": "Chen 2023", "a_events": 28, "a_total": 100, "b_events": 18, "b_total": 100, "effect_size": 0.50},
        ],
        "pooled_effect": 0.51,
        "ci_lower": 0.35,
        "ci_upper": 0.68,
        "i_squared": 42.3,
        "q_statistic": 8.72,
        "p_value": 0.028,
        "model": "Random"
    }
    path = os.path.join(OUTPUT_DIR, "demo_meta_analysis.xlsx")
    exporter.export_meta_analysis(meta, path)
    print(f"   ✅ 已导出: {path}")

    # 2. 经费预算
    print("\n2. 科研经费预算表")
    exporter2 = BudgetExporter()
    budget = {
        "title": "国家自然科学基金面上项目经费预算",
        "items": [
            {"name": "设备费", "amount": 20.0, "notes": "GPU工作站"},
            {"name": "材料费", "amount": 35.0, "notes": "试剂耗材"},
            {"name": "测试化验加工费", "amount": 15.0, "notes": "基因检测"},
            {"name": "差旅费", "amount": 10.0, "notes": "学术会议"},
            {"name": "会议费", "amount": 5.0, "notes": "项目研讨"},
            {"name": "出版/文献/信息传播费", "amount": 3.0, "notes": "论文版面费"},
            {"name": "劳务费", "amount": 15.0, "notes": "研究生津贴"},
            {"name": "专家咨询费", "amount": 2.0, "notes": "临床专家"},
        ],
        "total": 105.0
    }
    path = os.path.join(OUTPUT_DIR, "demo_budget.xlsx")
    exporter2.export_budget(budget, path)
    print(f"   ✅ 已导出: {path}")

    # 3. 期刊数据库
    print("\n3. 医学期刊数据库")
    exporter3 = JournalDatabaseExporter()
    journals = [
        {"name": "Nature Medicine", "impact_factor": 58.7, "jcr_quartile": "Q1", "cas_quartile": "1区", "field": "综合医学", "oa_policy": "Hybrid", "review_period": "2-4周"},
        {"name": "Lancet Oncology", "impact_factor": 41.6, "jcr_quartile": "Q1", "cas_quartile": "1区", "field": "肿瘤学", "oa_policy": "Hybrid", "review_period": "3-6周"},
        {"name": "JAMA Internal Medicine", "impact_factor": 39.6, "jcr_quartile": "Q1", "cas_quartile": "1区", "field": "内科学", "oa_policy": "Hybrid", "review_period": "2-4周"},
        {"name": "Cell", "impact_factor": 64.5, "jcr_quartile": "Q1", "cas_quartile": "1区", "field": "细胞生物学", "oa_policy": "Hybrid", "review_period": "3-5周"},
    ]
    path = os.path.join(OUTPUT_DIR, "demo_journals.xlsx")
    exporter3.export_journals(journals, path)
    print(f"   ✅ 已导出: {path}")

    # 4. 生存分析数据
    print("\n4. 生存分析数据")
    exporter4 = SurvivalDataExporter()
    records = [
        {"patient_id": "P001", "time": 36, "event": 0, "group": "Immunotherapy", "age": 55, "stage": 2},
        {"patient_id": "P002", "time": 24, "event": 1, "group": "Immunotherapy", "age": 62, "stage": 3},
        {"patient_id": "P003", "time": 18, "event": 1, "group": "Chemotherapy", "age": 70, "stage": 4},
        {"patient_id": "P004", "time": 42, "event": 0, "group": "Immunotherapy", "age": 58, "stage": 2},
        {"patient_id": "P005", "time": 15, "event": 1, "group": "Chemotherapy", "age": 65, "stage": 3},
    ]
    path = os.path.join(OUTPUT_DIR, "demo_survival.xlsx")
    exporter4.export_survival_data(records, path)
    print(f"   ✅ 已导出: {path}")


def demo_ppt_export():
    """演示 PowerPoint 导出"""
    print("\n" + "=" * 60)
    print("🎯 PowerPoint 文档导出演示")
    print("=" * 60)

    # 1. 科研汇报
    print("\n1. 科研汇报幻灯片")
    exporter = ResearchPresentationExporter()
    report = {
        "title": "基于AI的糖尿病肾病早期诊断研究",
        "subtitle": "国家自然科学基金面上项目中期汇报",
        "background": [
            "糖尿病肾病(DN)是糖尿病最严重的微血管并发症",
            "早期诊断可显著延缓疾病进展",
            "现有生物标志物敏感性和特异性不足"
        ],
        "methods": [
            "多中心前瞻性队列研究 (n=500)",
            "基于Transformer的多模态融合模型",
            "5折交叉验证 + 外部验证"
        ],
        "results": [
            "模型AUC = 0.92 (95% CI: 0.89-0.95)",
            "敏感性 = 85%, 特异性 = 90%",
            "显著优于传统生物标志物 (p<0.001)"
        ],
        "discussion": [
            "结果与既往文献报道一致",
            "模型可解释性仍需改进",
            "建议开展前瞻性临床验证"
        ],
        "conclusions": [
            "AI模型可用于DN的早期筛查",
            "多模态融合策略显著提升了诊断性能",
            "计划开展III期临床试验进一步验证"
        ],
    }
    path = os.path.join(OUTPUT_DIR, "demo_research_report.pptx")
    exporter.export_research_report(report, path)
    print(f"   ✅ 已导出: {path}")

    # 2. 影像征象教学
    print("\n2. 影像征象教学幻灯片")
    exporter2 = ImagingTeachingExporter()
    signs = [
        {
            "name": "磨玻璃影 (Ground Glass Opacity)",
            "description": "肺内局灶性密度增高影，但不掩盖肺纹理",
            "modalities": ["HRCT"],
            "anatomy": ["肺部"],
            "diseases": ["早期肺腺癌", "非典型腺瘤样增生", "局灶性纤维化", "肺泡出血"],
            "severity": "性质待定"
        },
        {
            "name": "树芽征 (Tree-in-Bud Sign)",
            "description": "细支气管及其周围炎症，呈树芽状分布",
            "modalities": ["CT"],
            "anatomy": ["肺部"],
            "diseases": ["肺结核", "支气管肺炎", "囊性纤维化", "弥漫性泛细支气管炎"],
            "severity": "感染/炎症"
        },
        {
            "name": "空气新月征 (Air Crescent Sign)",
            "description": "坏死病灶内出现新月形气体影",
            "modalities": ["CT", "X-Ray"],
            "anatomy": ["肺部"],
            "diseases": ["曲霉菌感染", "肺脓肿", "肺结核"],
            "severity": "可疑感染"
        },
    ]
    path = os.path.join(OUTPUT_DIR, "demo_imaging_teaching.pptx")
    exporter2.export_teaching(signs, path)
    print(f"   ✅ 已导出: {path}")

    # 3. 生物信息学汇报
    print("\n3. 生物信息学分析汇报")
    exporter3 = BioinformaticsReportExporter()
    bio = {
        "title": "肺癌基因组学分析报告",
        "subtitle": "NGS Panel (520基因) 测序结果",
        "sample_info": [
            "样本数: 50例 (30例腺癌, 20例鳞癌)",
            "测序平台: Illumina NovaSeq 6000",
            "测序深度: 平均500x",
            "质量控制: Q30 > 85%"
        ],
        "mutation_summary": [
            "TP53突变率: 45% (22/50)",
            "KRAS突变率: 32% (16/50)",
            "EGFR突变率: 28% (14/50)",
            "ALK融合: 8% (4/50)",
            "ROS1融合: 4% (2/50)"
        ],
        "pathways": [
            "PI3K-AKT通路显著富集 (p<0.001, FDR=0.02)",
            "MAPK通路富集 (p<0.01)",
            "DNA修复通路 (p<0.05)",
            "细胞周期调控 (p<0.05)"
        ],
        "survival": [
            "TP53突变患者PFS显著缩短 (HR=2.3, p=0.008)",
            "EGFR突变患者对TKI治疗反应良好 (ORR=78%)",
            "KRAS突变与免疫治疗抵抗相关"
        ],
        "conclusions": [
            "TP53和KRAS是肺癌中最主要的驱动基因",
            "EGFR突变患者可从靶向治疗中显著获益",
            "建议基于突变谱进行个体化治疗策略制定"
        ],
    }
    path = os.path.join(OUTPUT_DIR, "demo_bioinformatics.pptx")
    exporter3.export_bioinformatics_report(bio, path)
    print(f"   ✅ 已导出: {path}")


def demo_import():
    """演示文档导入"""
    print("\n" + "=" * 60)
    print("📥 文档导入演示")
    print("=" * 60)

    # 1. Word 文本导入
    print("\n1. Word 文本提取")
    word_path = os.path.join(OUTPUT_DIR, "demo_paper.docx")
    importer = WordImporter()
    text = importer.extract_text(word_path)
    print(f"   文本长度: {len(text)} 字符")
    print(f"   前100字: {text[:100]}...")

    # 2. Word 结构化导入
    print("\n2. Word 结构化提取")
    structure = importer.extract_structure(word_path)
    print(f"   段落数: {len(structure['paragraphs'])}")
    print(f"   标题数: {len(structure['headings'])}")
    print(f"   表格数: {len(structure['tables'])}")
    for h in structure['headings'][:3]:
        print(f"   - {h}")

    # 3. Excel 导入
    print("\n3. Excel 数据读取")
    excel_path = os.path.join(OUTPUT_DIR, "demo_journals.xlsx")
    importer2 = ExcelImporter()
    data = importer2.read_sheet(excel_path)
    print(f"   记录数: {len(data)}")
    for row in data[:3]:
        print(f"   - {row.get('Journal Name', 'N/A')} (IF: {row.get('Impact Factor', 'N/A')})")

    # 4. Excel 全部工作表
    print("\n4. Excel 全部工作表")
    all_sheets = importer2.read_all_sheets(excel_path)
    print(f"   工作表: {list(all_sheets.keys())}")


def main():
    print("=" * 60)
    print("🏥 MedAIagents Office 文档导入导出功能演示")
    print("=" * 60)
    print(f"\n输出目录: {os.path.abspath(OUTPUT_DIR)}")

    demo_word_export()
    demo_excel_export()
    demo_ppt_export()
    demo_import()

    print("\n" + "=" * 60)
    print("✅ 演示完成！所有文件已导出至:")
    print(f"   {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)
    print("""
导出功能清单:
  📄 Word (.docx)
     • PaperExporter - 医学论文 (IMRaD结构)
     • GrantProposalExporter - 基金申请书
     • ResponseLetterExporter - 审稿回复信
     • ProtocolExporter - RCT试验方案

  📊 Excel (.xlsx)
     • MetaAnalysisExporter - Meta分析结果
     • BudgetExporter - 经费预算表
     • JournalDatabaseExporter - 期刊数据库
     • SurvivalDataExporter - 生存分析数据

  🎯 PowerPoint (.pptx)
     • ResearchPresentationExporter - 科研汇报
     • ImagingTeachingExporter - 影像征象教学
     • BioinformaticsReportExporter - 生物信息学汇报

导入功能清单:
  📥 WordImporter - 文本提取 / 结构化提取 / IMRaD解析
  📥 ExcelImporter - 工作表读取 / 生存数据导入 / 期刊数据库导入
    """)


if __name__ == "__main__":
    main()
