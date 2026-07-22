"""
Medical Tool Test Harness
医学工具测试框架

基于 Model + Harness 模式，为 MedAIagents 的医学工具提供统一的测试基础设施：
- Model: 被测的医学工具（diagnose, analyze_imaging 等）
- Harness: 测试夹具，负责参数验证、Mock 数据生成、结果断言、性能计时

Usage:
    harness = MedicalToolHarness()
    harness.load_tools()
    results = harness.run_tool("diagnose")
    harness.print_report(results)
"""

import time
import json
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum


class HarnessTestStatus(str, Enum):
    """测试状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """单个测试结果"""
    tool_name: str
    test_name: str
    status: HarnessTestStatus
    duration_ms: float = 0.0
    message: str = ""
    expected: Any = None
    actual: Any = None
    exception: Optional[str] = None


@dataclass
class ToolTestCase:
    """工具测试用例定义"""
    name: str
    arguments: Dict[str, Any]
    expected_type: type = dict
    required_keys: List[str] = field(default_factory=list)
    validator: Optional[Callable[[Any], Tuple[bool, str]]] = None
    should_error: bool = False
    error_contains: str = ""


class MedicalToolHarness:
    """医学工具测试框架（Harness）

    负责：
    1. 加载 ToolRegistry 中注册的所有医学工具
    2. 验证工具参数符合 JSON Schema
    3. 提供 Mock 数据工厂
    4. 执行测试用例并收集结果
    5. 生成测试报告
    """

    def __init__(self):
        self.registry = None
        self.executor = None
        self._tools_loaded = False
        self._test_cases: Dict[str, List[ToolTestCase]] = {}

    # ========== 工具加载 ==========

    def load_tools(self):
        """从 medai.tools 加载所有医学工具到 Harness"""
        from medai.tools import ToolRegistry, ToolExecutor, register_medical_tools

        self.registry = ToolRegistry()
        register_medical_tools(self.registry)
        self.executor = ToolExecutor(self.registry)
        self._tools_loaded = True
        self._register_default_test_cases()
        return self

    def list_tools(self) -> List[str]:
        """列出已加载的工具名称"""
        if not self._tools_loaded:
            return []
        return self.registry.tool_names

    # ========== 参数验证 ==========

    def validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """验证参数是否符合工具定义的 JSON Schema"""
        if not self._tools_loaded:
            return False, "Tools not loaded"
        return self.executor.validate_arguments(tool_name, arguments)

    # ========== Mock 数据工厂 ==========

    @staticmethod
    def mock_diagnose_args(
        symptoms: Optional[List[str]] = None,
        age: int = 45,
        gender: str = "男"
    ) -> Dict[str, Any]:
        """生成诊断工具的 Mock 参数"""
        return {
            "symptoms": symptoms or ["头痛", "发热", "咳嗽"],
            "age": age,
            "gender": gender
        }

    @staticmethod
    def mock_imaging_args(report_text: Optional[str] = None) -> Dict[str, Any]:
        """生成影像解析工具的 Mock 参数"""
        return {
            "report_text": report_text or (
                "胸部CT平扫：右肺上叶见一结节状高密度影，直径约15mm，边缘毛糙，"
                "可见分叶征及短毛刺征。纵隔未见明显肿大淋巴结。"
            )
        }

    @staticmethod
    def mock_literature_args(query: str = "lung cancer immunotherapy") -> Dict[str, Any]:
        """生成文献搜索工具的 Mock 参数"""
        return {"query": query, "max_results": 3}

    @staticmethod
    def mock_sample_size_args(study_type: str = "proportion") -> Dict[str, Any]:
        """生成样本量计算工具的 Mock 参数"""
        if study_type == "proportion":
            return {"study_type": "proportion", "p1": 0.3, "p2": 0.5, "alpha": 0.05, "power": 0.8}
        elif study_type == "mean":
            return {"study_type": "mean", "mean1": 50, "mean2": 60, "std_dev": 15, "alpha": 0.05, "power": 0.8}
        elif study_type == "survival":
            return {
                "study_type": "survival",
                "median_survival_control": 12,
                "median_survival_treatment": 18,
                "hazard_ratio": 0.75,
                "alpha": 0.05,
                "power": 0.8
            }
        return {"study_type": study_type, "alpha": 0.05, "power": 0.8}

    @staticmethod
    def mock_note_args(note_type: str = "admission_note") -> Dict[str, Any]:
        """生成病历生成工具的 Mock 参数"""
        if note_type == "admission_note":
            patient_info = {
                "patient_name": "张三",
                "gender": "男",
                "age": 65,
                "chief_complaint": "胸痛3天",
                "diagnosis": "冠心病"
            }
        elif note_type == "progress_note":
            patient_info = {
                "subjective": "今日胸痛减轻",
                "temperature": 36.8,
                "pulse": 78,
                "respiration": 20,
                "blood_pressure": "130/85"
            }
        elif note_type == "discharge_note":
            patient_info = {
                "patient_name": "张三",
                "gender": "男",
                "age": 65,
                "admission_diagnosis": "冠心病",
                "discharge_diagnosis": "冠心病 稳定型心绞痛",
                "discharge_orders": "继续服用阿司匹林100mg qd"
            }
        else:
            patient_info = {}
        return {"note_type": note_type, "patient_info": patient_info}

    @staticmethod
    def mock_medication_args() -> Dict[str, Any]:
        """生成用药安全检查工具的 Mock 参数"""
        return {
            "medications": ["阿司匹林", "二甲双胍"],
            "patient_conditions": {
                "allergies": ["青霉素"],
                "doses": {"阿司匹林": 100, "二甲双胍": 500}
            }
        }

    @staticmethod
    def mock_export_args(doc_type: str = "paper") -> Dict[str, Any]:
        """生成文档导出工具的 Mock 参数"""
        import tempfile
        return {
            "doc_type": doc_type,
            "data": {"title": "测试文档", "content": "这是测试内容"},
            "file_path": tempfile.mktemp(suffix=".docx")
        }

    # ========== 测试用例注册 ==========

    def _register_default_test_cases(self):
        """注册所有医学工具的默认测试用例"""
        self._test_cases = {
            "diagnose": [
                ToolTestCase(
                    name="正常成人男性",
                    arguments=self.mock_diagnose_args(),
                    required_keys=["primary_diagnosis", "patient_info"]
                ),
                ToolTestCase(
                    name="正常成人女性",
                    arguments=self.mock_diagnose_args(gender="女"),
                    required_keys=["primary_diagnosis", "patient_info"]
                ),
                ToolTestCase(
                    name="老年患者",
                    arguments=self.mock_diagnose_args(age=78),
                    required_keys=["primary_diagnosis"]
                ),
                ToolTestCase(
                    name="参数缺失_age",
                    arguments={"symptoms": ["头痛"], "gender": "男"},
                    should_error=True,
                    error_contains="missing 1 required positional argument: 'age'"
                ),
            ],
            "analyze_imaging": [
                ToolTestCase(
                    name="肺部CT报告",
                    arguments=self.mock_imaging_args(),
                    required_keys=["report_id", "exam_type", "findings", "impression"]
                ),
                ToolTestCase(
                    name="空报告文本",
                    arguments={"report_text": ""},
                    required_keys=["report_id"]
                ),
                ToolTestCase(
                    name="参数缺失",
                    arguments={},
                    should_error=True,
                    error_contains="missing 1 required positional argument: 'report_text'"
                ),
            ],
            "search_literature": [
                ToolTestCase(
                    name="肺癌免疫治疗",
                    arguments=self.mock_literature_args(),
                    expected_type=list
                ),
                ToolTestCase(
                    name="空查询",
                    arguments={"query": ""},
                    expected_type=list
                ),
            ],
            "calculate_sample_size": [
                ToolTestCase(
                    name="率比较",
                    arguments=self.mock_sample_size_args("proportion"),
                    required_keys=["sample_size"]
                ),
                ToolTestCase(
                    name="均数比较",
                    arguments=self.mock_sample_size_args("mean"),
                    required_keys=["sample_size"]
                ),
                ToolTestCase(
                    name="生存分析",
                    arguments=self.mock_sample_size_args("survival"),
                    required_keys=["required_events"]
                ),
                ToolTestCase(
                    name="不支持的研究类型",
                    arguments={"study_type": "unknown", "alpha": 0.05, "power": 0.8},
                    should_error=True,
                    error_contains="不支持"
                ),
            ],
            "generate_medical_note": [
                ToolTestCase(
                    name="入院记录",
                    arguments=self.mock_note_args("admission_note"),
                    expected_type=str,
                    validator=lambda x: ("张三" in x and "冠心病" in x, "应包含患者姓名和诊断")
                ),
                ToolTestCase(
                    name="病程记录",
                    arguments=self.mock_note_args("progress_note"),
                    expected_type=str,
                ),
                ToolTestCase(
                    name="出院记录",
                    arguments=self.mock_note_args("discharge_note"),
                    expected_type=str,
                    validator=lambda x: ("出院" in x or "discharge" in x.lower(), "应包含出院相关描述")
                ),
            ],
            "check_medication_safety": [
                ToolTestCase(
                    name="常规用药检查",
                    arguments=self.mock_medication_args(),
                    required_keys=["warnings", "is_safe", "medications_checked"]
                ),
                ToolTestCase(
                    name="空药物列表",
                    arguments={"medications": [], "patient_conditions": {}},
                    required_keys=[]
                ),
            ],
            "export_document": [
                ToolTestCase(
                    name="导出论文",
                    arguments=self.mock_export_args("paper"),
                    required_keys=["success", "file_path"]
                ),
            ],
        }

    # ========== 测试执行 ==========

    def run_tool(self, tool_name: str) -> List[TestResult]:
        """运行指定工具的所有测试用例"""
        results = []
        cases = self._test_cases.get(tool_name, [])

        if not cases:
            return [TestResult(
                tool_name=tool_name,
                test_name="_no_cases_",
                status=HarnessTestStatus.SKIPPED,
                message="No test cases registered"
            )]

        for case in cases:
            result = self._run_single_test(tool_name, case)
            results.append(result)

        return results

    def _run_single_test(self, tool_name: str, case: ToolTestCase) -> TestResult:
        """执行单个测试用例"""
        start = time.perf_counter()

        try:
            # 1. 参数 Schema 验证
            valid, error_msg = self.validate_arguments(tool_name, case.arguments)
            if not valid and not case.should_error:
                duration = (time.perf_counter() - start) * 1000
                return TestResult(
                    tool_name=tool_name,
                    test_name=case.name,
                    status=HarnessTestStatus.FAILED,
                    duration_ms=duration,
                    message=f"参数验证失败: {error_msg}",
                    actual=error_msg
                )

            # 2. 执行工具
            tool_def = self.registry.get(tool_name)
            if tool_def.func is not None:
                actual = tool_def.func(**case.arguments)
            else:
                duration = (time.perf_counter() - start) * 1000
                return TestResult(
                    tool_name=tool_name,
                    test_name=case.name,
                    status=HarnessTestStatus.SKIPPED,
                    duration_ms=duration,
                    message="Tool has no executable function"
                )

            duration = (time.perf_counter() - start) * 1000

            # 3. 异常用例断言
            if case.should_error:
                return TestResult(
                    tool_name=tool_name,
                    test_name=case.name,
                    status=HarnessTestStatus.FAILED,
                    duration_ms=duration,
                    message="预期抛出异常，但工具正常返回",
                    actual=str(actual)[:500]
                )

            # 4. 返回类型断言
            if not isinstance(actual, case.expected_type):
                return TestResult(
                    tool_name=tool_name,
                    test_name=case.name,
                    status=HarnessTestStatus.FAILED,
                    duration_ms=duration,
                    message=f"返回类型不匹配: 期望 {case.expected_type.__name__}, 实际 {type(actual).__name__}",
                    expected=case.expected_type.__name__,
                    actual=type(actual).__name__
                )

            # 5. 必要字段断言
            if case.required_keys and isinstance(actual, dict):
                missing = [k for k in case.required_keys if k not in actual]
                if missing:
                    return TestResult(
                        tool_name=tool_name,
                        test_name=case.name,
                        status=HarnessTestStatus.FAILED,
                        duration_ms=duration,
                        message=f"返回结果缺少必要字段: {missing}",
                        expected=case.required_keys,
                        actual=list(actual.keys())
                    )

            # 6. 自定义验证器
            if case.validator is not None:
                ok, msg = case.validator(actual)
                if not ok:
                    return TestResult(
                        tool_name=tool_name,
                        test_name=case.name,
                        status=HarnessTestStatus.FAILED,
                        duration_ms=duration,
                        message=f"自定义验证失败: {msg}",
                        actual=str(actual)[:500]
                    )

            # 全部通过
            return TestResult(
                tool_name=tool_name,
                test_name=case.name,
                status=HarnessTestStatus.PASSED,
                duration_ms=duration,
                message="通过"
            )

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            if case.should_error:
                if case.error_contains and case.error_contains in str(e):
                    return TestResult(
                        tool_name=tool_name,
                        test_name=case.name,
                        status=HarnessTestStatus.PASSED,
                        duration_ms=duration,
                        message=f"如期抛出异常: {str(e)[:200]}"
                    )
                else:
                    return TestResult(
                        tool_name=tool_name,
                        test_name=case.name,
                        status=HarnessTestStatus.FAILED,
                        duration_ms=duration,
                        message=f"抛出异常但不符合预期: {str(e)[:200]}",
                        exception=traceback.format_exc()
                    )
            return TestResult(
                tool_name=tool_name,
                test_name=case.name,
                status=HarnessTestStatus.ERROR,
                duration_ms=duration,
                message=f"执行异常: {str(e)[:200]}",
                exception=traceback.format_exc()
            )

    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """运行所有已注册工具的测试用例"""
        if not self._tools_loaded:
            raise RuntimeError("请先调用 load_tools()")

        all_results = {}
        for tool_name in self.registry.tool_names:
            all_results[tool_name] = self.run_tool(tool_name)
        return all_results

    # ========== 报告生成 ==========

    @staticmethod
    def print_report(results: Dict[str, List[TestResult]]) -> str:
        """打印测试报告到控制台，并返回报告文本"""
        lines = []
        lines.append("=" * 70)
        lines.append("Medical Tool Test Harness Report")
        lines.append("医学工具测试框架报告")
        lines.append("=" * 70)

        total = 0
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        total_duration = 0.0

        for tool_name, tool_results in results.items():
            lines.append("")
            lines.append(f"[{tool_name}]")
            for r in tool_results:
                total += 1
                total_duration += r.duration_ms
                icon = "?"
                if r.status == HarnessTestStatus.PASSED:
                    passed += 1
                    icon = "PASS"
                elif r.status == HarnessTestStatus.FAILED:
                    failed += 1
                    icon = "FAIL"
                elif r.status == HarnessTestStatus.ERROR:
                    errors += 1
                    icon = "ERR "
                elif r.status == HarnessTestStatus.SKIPPED:
                    skipped += 1
                    icon = "SKIP"

                lines.append(
                    f"  [{icon}] {r.test_name:20s}  {r.duration_ms:8.2f}ms  {r.message[:60]}"
                )

        lines.append("")
        lines.append("-" * 70)
        lines.append(f"总计: {total}  |  通过: {passed}  |  失败: {failed}  |  错误: {errors}  |  跳过: {skipped}")
        lines.append(f"总耗时: {total_duration:.2f}ms  |  平均: {total_duration/max(total,1):.2f}ms")
        lines.append("=" * 70)

        report = "\n".join(lines)
        print(report)
        return report

    def get_summary(self, results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """获取测试摘要（可用于断言或上报）"""
        summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "tools_tested": list(results.keys()),
            "all_passed": True,
        }
        for tool_results in results.values():
            for r in tool_results:
                summary["total"] += 1
                if r.status == HarnessTestStatus.PASSED:
                    summary["passed"] += 1
                elif r.status == HarnessTestStatus.FAILED:
                    summary["failed"] += 1
                    summary["all_passed"] = False
                elif r.status == HarnessTestStatus.ERROR:
                    summary["errors"] += 1
                    summary["all_passed"] = False
                elif r.status == HarnessTestStatus.SKIPPED:
                    summary["skipped"] += 1

        summary["pass_rate"] = (
            summary["passed"] / max(summary["total"] - summary["skipped"], 1) * 100
        )
        return summary
