"""
MedAIagents v0.4.0 功能演示脚本
展示多语言支持与同行评审辅助模块
"""
import sys
sys.path.insert(0, '../src')

from medai import (
    Language, I18nManager, MedicalTerminology, ChineseJournalDatabase,
    MultilingualAssistant,
    ReviewCommentType, ResponseStrategy, ReviewComment,
    ReviewCommentParser, ResponseGenerator, ResponseLetterWriter,
    RevisionTracker, PeerReviewAssistant,
)


def demo_multilingual():
    """演示多语言支持功能"""
    print("\n" + "=" * 60)
    print("🌐 多语言支持模块演示")
    print("=" * 60)

    # 1. 界面国际化
    print("\n📱 1. 界面文本双语切换")
    i18n = I18nManager()
    keys = ["app_title", "menu_diagnosis", "menu_writing", "button_submit"]
    for lang in [Language.ZH_CN, Language.EN_US]:
        i18n.set_language(lang)
        print(f"\n  [{lang.value}]")
        for key in keys:
            print(f"    {key}: {i18n.translate_ui(key)}")

    # 2. 医学术语对照
    print("\n📚 2. 医学术语标准化对照")
    term_db = MedicalTerminology()
    terms_to_lookup = ["diabetes mellitus", "hypertension", "myocardial infarction"]
    for query in terms_to_lookup:
        term = term_db.lookup(query)
        if term:
            print(f"\n  {term.english} / {term.chinese}")
            print(f"    缩写: {term.abbreviation}")
            print(f"    ICD-10: {term.icd10_code}")
            print(f"    MeSH: {term.mesh_term}")
            print(f"    SNOMED-CT: {term.snomed_id}")

    # 3. 术语批量翻译
    print("\n🔄 3. 论文片段术语翻译")
    sample_text = "Patients with diabetes mellitus and hypertension were enrolled."
    translated = term_db.translate_text(sample_text, Language.ZH_CN)
    print(f"  原文: {sample_text}")
    print(f"  译文: {translated}")

    # 4. 中文核心期刊查询
    print("\n📰 4. 中文核心期刊数据库")
    cj_db = ChineseJournalDatabase()
    stats = cj_db.get_statistics()
    print(f"  收录期刊: {stats['total_journals']} 本")
    print(f"  覆盖领域: {stats['fields_covered']} 个")
    print(f"  平均影响因子: {stats['avg_if']}")

    print("\n  外科领域期刊:")
    for journal in cj_db.get_by_field("外科")[:3]:
        print(f"    • {journal['name']} (IF: {journal['impact_factor_2023']})")


def demo_peer_review():
    """演示同行评审辅助功能"""
    print("\n" + "=" * 60)
    print("📝 同行评审辅助模块演示")
    print("=" * 60)

    # 模拟审稿意见
    reviewer_comments = {
        "Reviewer #1": """
        1. Major concern: The sample size calculation is not clearly described. 
           Please provide the power analysis and effect size assumptions.
        2. The primary endpoint choice may not be appropriate for this study design.
        3. Minor: There are some grammatical errors in the Introduction.
        4. The statistical methods should include subgroup analysis by age and gender.
        """,
        "Reviewer #2": """
        1. The methodology section is well-written, but I suggest adding more 
           details on the randomization procedure.
        2. The discussion should compare results with the latest 2024 guidelines.
        3. Figure 2 is unclear — please improve the labeling.
        """
    }

    # 1. 审稿意见解析
    print("\n🔍 1. 审稿意见自动分类")
    parser = ReviewCommentParser()
    for reviewer_id, text in reviewer_comments.items():
        comments = parser.parse_comments(text, reviewer_id)
        summary = parser.summarize_review(comments)
        print(f"\n  {reviewer_id}:")
        print(f"    总意见数: {summary['total_comments']}")
        print(f"    重大问题: {summary['major_concerns']}")
        print(f"    次要意见: {summary['minor_comments']}")
        print(f"    平均严重度: {summary['average_severity']}")
        print(f"    类型分布: {summary['type_distribution']}")
        for c in comments[:2]:
            print(f"    - [{c.comment_type.name}] {c.original_text[:50]}...")

    # 2. 回复生成
    print("\n💬 2. 智能回复生成")
    generator = ResponseGenerator()
    sample_comment = ReviewComment(
        reviewer_id="R1",
        comment_id="R1-1",
        original_text="Please provide power analysis details.",
        comment_type=ReviewCommentType.METHODOLOGY,
        severity=4
    )
    for strategy in [ResponseStrategy.ACCEPT, ResponseStrategy.PARTIAL]:
        response = generator.generate_response(
            comment=sample_comment,
            strategy=strategy,
            changes="补充了基于G*Power软件的样本量计算，设定效应量d=0.5，α=0.05，Power=0.90。",
            location="3"
        )
        print(f"\n  策略: {strategy.value}")
        print(f"  回复: {response.response_text[:120]}...")

    # 3. Response Letter 生成
    print("\n📄 3. Response Letter 结构化撰写")
    writer = ResponseLetterWriter()
    letter = writer.write_response_letter(
        reviewer_comments=reviewer_comments,
        manuscript_id="MANUSCRIPT-2025-042",
        title="Novel Biomarkers for Early Detection of Diabetic Nephropathy",
        authors="Wang L, Zhang H, Chen X, et al."
    )
    print(f"\n  生成字数: {len(letter)} 字符")
    print(f"  开头片段: {letter[:200].strip()}...")

    # 4. 修改痕迹追踪
    print("\n📊 4. 修改痕迹追踪")
    tracker = RevisionTracker()
    revisions = [
        ("R1-1", "Methods, page 3", "n=100", "n=150 (power analysis)", "补充样本量计算"),
        ("R1-2", "Methods, page 4", "primary endpoint: HR", "primary endpoint: OR", "修正终点指标"),
        ("R2-1", "Methods, page 3", "randomized by software", "randomized by block randomization (block size 4) via SAS", "细化随机化方案"),
    ]
    for cid, loc, orig, rev, reason in revisions:
        tracker.add_revision(cid, loc, orig, rev, reason)

    summary_text = tracker.generate_revision_summary()
    print(f"\n  {summary_text[:400]}...")


def main():
    print("🏥 MedAIagents v0.4.0 功能演示")
    print("=" * 60)

    demo_multilingual()
    demo_peer_review()

    print("\n" + "=" * 60)
    print("✅ v0.4.0 演示完成！")
    print("=" * 60)
    print("""
v0.4.0 新增核心能力:
  • 中英双语界面切换 (I18nManager)
  • 医学术语标准化对照 ICD-10/MeSH/SNOMED (MedicalTerminology)
  • 中文核心期刊数据库 (ChineseJournalDatabase, 25本)
  • 审稿意见智能分类解析 (ReviewCommentParser, 9种类型)
  • Response Letter 自动生成 (ResponseLetterWriter)
  • 修改痕迹对比追踪 (RevisionTracker)
    """)


if __name__ == "__main__":
    main()
