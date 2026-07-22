"""
Model + Harness 驱动的医学工具集成测试
Medical Tool Integration Tests (Model + Harness Pattern)

本测试文件使用 MedicalToolHarness 作为测试夹具，对 ToolRegistry 中注册的
所有医学工具进行端到端验证。

测试覆盖：
- 参数 Schema 校验
- 正常场景功能验证
- 边界/异常场景处理
- 返回结果结构断言
- 性能基准计时
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from harness import MedicalToolHarness, HarnessTestStatus


# ============================================================
# pytest Fixture: Harness 初始化
# ============================================================

@pytest.fixture(scope="module")
def harness():
    """模块级 Harness 夹具，所有测试共享同一个工具注册表"""
    h = MedicalToolHarness()
    h.load_tools()
    return h


# ============================================================
# 1. 工具注册与加载测试
# ============================================================

class TestToolLoading:
    """验证 Harness 正确加载所有医学工具"""

    def test_all_tools_loaded(self, harness):
        tools = harness.list_tools()
        expected = {
            "diagnose", "analyze_imaging", "search_literature",
            "calculate_sample_size", "generate_medical_note",
            "check_medication_safety", "export_document"
        }
        assert set(tools) == expected, f"期望工具: {expected}, 实际: {set(tools)}"

    def test_tool_count(self, harness):
        assert len(harness.list_tools()) == 7


# ============================================================
# 2. diagnose 工具测试
# ============================================================

class TestDiagnoseTool:
    """诊断工具 Model + Harness 测试"""

    def test_normal_adult_male(self, harness):
        results = harness.run_tool("diagnose")
        r = next((x for x in results if x.test_name == "正常成人男性"), None)
        assert r is not None
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_normal_adult_female(self, harness):
        results = harness.run_tool("diagnose")
        r = next((x for x in results if x.test_name == "正常成人女性"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_elderly_patient(self, harness):
        results = harness.run_tool("diagnose")
        r = next((x for x in results if x.test_name == "老年患者"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_missing_age_rejected(self, harness):
        results = harness.run_tool("diagnose")
        r = next((x for x in results if x.test_name == "参数缺失_age"), None)
        assert r.status == HarnessTestStatus.PASSED, f"期望参数缺失被拦截: {r.message}"


# ============================================================
# 3. analyze_imaging 工具测试
# ============================================================

class TestAnalyzeImagingTool:
    """影像解析工具 Model + Harness 测试"""

    def test_lung_ct_report(self, harness):
        results = harness.run_tool("analyze_imaging")
        r = next((x for x in results if x.test_name == "肺部CT报告"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_empty_report(self, harness):
        results = harness.run_tool("analyze_imaging")
        r = next((x for x in results if x.test_name == "空报告文本"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_missing_param_rejected(self, harness):
        results = harness.run_tool("analyze_imaging")
        r = next((x for x in results if x.test_name == "参数缺失"), None)
        assert r.status == HarnessTestStatus.PASSED, f"期望参数缺失被拦截: {r.message}"


# ============================================================
# 4. search_literature 工具测试
# ============================================================

class TestSearchLiteratureTool:
    """文献搜索工具 Model + Harness 测试"""

    def test_lung_cancer_query(self, harness):
        results = harness.run_tool("search_literature")
        r = next((x for x in results if x.test_name == "肺癌免疫治疗"), None)
        assert r.status in (HarnessTestStatus.PASSED, HarnessTestStatus.SKIPPED), r.message

    def test_empty_query(self, harness):
        results = harness.run_tool("search_literature")
        r = next((x for x in results if x.test_name == "空查询"), None)
        assert r.status in (HarnessTestStatus.PASSED, HarnessTestStatus.SKIPPED), r.message


# ============================================================
# 5. calculate_sample_size 工具测试
# ============================================================

class TestCalculateSampleSizeTool:
    """样本量计算工具 Model + Harness 测试"""

    def test_proportion(self, harness):
        results = harness.run_tool("calculate_sample_size")
        r = next((x for x in results if x.test_name == "率比较"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_mean(self, harness):
        results = harness.run_tool("calculate_sample_size")
        r = next((x for x in results if x.test_name == "均数比较"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_survival(self, harness):
        results = harness.run_tool("calculate_sample_size")
        r = next((x for x in results if x.test_name == "生存分析"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_unsupported_type(self, harness):
        results = harness.run_tool("calculate_sample_size")
        r = next((x for x in results if x.test_name == "不支持的研究类型"), None)
        assert r.status == HarnessTestStatus.PASSED, f"期望不支持的类型被拦截: {r.message}"


# ============================================================
# 6. generate_medical_note 工具测试
# ============================================================

class TestGenerateMedicalNoteTool:
    """病历生成工具 Model + Harness 测试"""

    def test_admission_note(self, harness):
        results = harness.run_tool("generate_medical_note")
        r = next((x for x in results if x.test_name == "入院记录"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_progress_note(self, harness):
        results = harness.run_tool("generate_medical_note")
        r = next((x for x in results if x.test_name == "病程记录"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_discharge_note(self, harness):
        results = harness.run_tool("generate_medical_note")
        r = next((x for x in results if x.test_name == "出院记录"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message


# ============================================================
# 7. check_medication_safety 工具测试
# ============================================================

class TestCheckMedicationSafetyTool:
    """用药安全检查工具 Model + Harness 测试"""

    def test_routine_check(self, harness):
        results = harness.run_tool("check_medication_safety")
        r = next((x for x in results if x.test_name == "常规用药检查"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message

    def test_empty_medications(self, harness):
        results = harness.run_tool("check_medication_safety")
        r = next((x for x in results if x.test_name == "空药物列表"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message


# ============================================================
# 8. export_document 工具测试
# ============================================================

class TestExportDocumentTool:
    """文档导出工具 Model + Harness 测试"""

    def test_export_paper(self, harness):
        results = harness.run_tool("export_document")
        r = next((x for x in results if x.test_name == "导出论文"), None)
        assert r.status == HarnessTestStatus.PASSED, r.message


# ============================================================
# 9. 全量测试与报告
# ============================================================

class TestFullHarnessRun:
    """全量 Harness 运行测试"""

    def test_all_tools_pass(self, harness):
        """所有工具至少有一个测试用例通过"""
        all_results = harness.run_all_tests()
        summary = harness.get_summary(all_results)

        # 打印报告到测试输出
        harness.print_report(all_results)

        assert summary["total"] > 0, "没有执行任何测试"
        assert summary["errors"] == 0, f"存在 {summary['errors']} 个错误"

        # 通过率 >= 80%（部分工具可能因外部依赖被跳过）
        assert summary["pass_rate"] >= 80, (
            f"通过率 {summary['pass_rate']:.1f}% 低于 80%，"
            f"失败: {summary['failed']}, 跳过: {summary['skipped']}"
        )

    def test_performance_under_threshold(self, harness):
        """单个测试用例执行时间不超过 30 秒"""
        all_results = harness.run_all_tests()
        for tool_name, results in all_results.items():
            for r in results:
                assert r.duration_ms < 30000, (
                    f"{tool_name}/{r.test_name} 耗时 {r.duration_ms:.0f}ms 超过阈值"
                )
