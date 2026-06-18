from app.services.artifact_content_cleaner import clean_artifact_content


def test_clean_artifact_content_removes_reasoning_and_execution_noise():
    raw = """<think>
我需要先搜索文献，再规划结构。
</think>
# 执行任务内容
- 搜索 PubMed
- 生成 PPT

# 用户要求
帮我检查一下关于糖尿病GLP-1治疗的最新研究成果，做一个解读的PPT

# GLP-1 治疗糖尿病最新研究解读

## 核心结论
GLP-1 受体激动剂在降糖、减重和心肾保护方面均有持续证据支持。

## 下一步计划 (Next Steps)
后续将继续生成PPT。
"""

    cleaned = clean_artifact_content(raw)

    assert "<think>" not in cleaned
    assert "我需要先搜索文献" not in cleaned
    assert "执行任务内容" not in cleaned
    assert "搜索 PubMed" not in cleaned
    assert "用户要求" not in cleaned
    assert "帮我检查一下" not in cleaned
    assert "下一步计划" not in cleaned
    assert "Next Steps" not in cleaned
    assert "GLP-1 治疗糖尿病最新研究解读" in cleaned
    assert "心肾保护" in cleaned


def test_rejects_low_quality_tool_output_with_missing_inputs_and_placeholders():
    from app.services.artifact_content_cleaner import is_low_quality_tool_output

    raw = """# REDCap 数据字典生成 - 草案

⚠️ 注意：未提供实际CRF/方案文档，以下为基于研究名称的草案

## 待确认项
研究类型：是否为RCT、单臂、观察性研究？
请上传CRF/方案Word/Excel/PDF文档以生成准确数据字典。
"""

    assert is_low_quality_tool_output(raw) is True


def test_keeps_substantive_clinical_content_even_with_limited_uncertainty():
    from app.services.artifact_content_cleaner import is_low_quality_tool_output

    raw = """# 研究方向建议

建议优先设计真实世界研究，比较乌帕替尼与度普利尤单抗在EASI-75、瘙痒NRS和DLQI改善方面的差异。
需要在讨论中说明适应证、样本来源和混杂控制限制。
"""

    assert is_low_quality_tool_output(raw) is False


def test_clean_artifact_content_keeps_real_next_step_when_not_noise_heading():
    raw = """# 研究建议

临床实践中下一步应结合患者 BMI、ASCVD 风险和肾功能进行个体化用药。
"""

    cleaned = clean_artifact_content(raw)

    assert "下一步应结合患者 BMI" in cleaned
