"""
工具调用框架单元测试
Tool Framework Unit Tests
"""

import pytest
import asyncio

from medai.tools import ToolRegistry, ToolExecutor, register_medical_tools
from medai.tools.registry import ToolDefinition


# ============================================================
# ToolRegistry Tests
# ============================================================

class TestToolRegistry:
    
    def test_register_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            func=lambda: "hello"
        )
        assert "test_tool" in registry
        assert len(registry) == 1
    
    def test_register_duplicate_raises(self):
        registry = ToolRegistry()
        registry.register("tool1", "desc", {})
        with pytest.raises(ValueError, match="already registered"):
            registry.register("tool1", "desc", {})
    
    def test_get_tool(self):
        registry = ToolRegistry()
        registry.register("tool1", "desc", {}, func=lambda x: x)
        tool = registry.get("tool1")
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "tool1"
    
    def test_get_nonexistent_raises(self):
        registry = ToolRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")
    
    def test_unregister(self):
        registry = ToolRegistry()
        registry.register("tool1", "desc", {})
        assert registry.unregister("tool1") is True
        assert "tool1" not in registry
        assert registry.unregister("tool1") is False
    
    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register("tool1", "First tool", {"type": "object"})
        registry.register("tool2", "Second tool", {"type": "object"})
        tools = registry.list_tools()
        assert len(tools) == 2
        assert tools[0]["type"] == "function"
        assert "function" in tools[0]
        assert tools[0]["function"]["name"] == "tool1"
    
    def test_has_tool(self):
        registry = ToolRegistry()
        registry.register("tool1", "desc", {})
        assert registry.has_tool("tool1") is True
        assert registry.has_tool("tool2") is False
    
    def test_tool_names(self):
        registry = ToolRegistry()
        registry.register("a", "desc", {})
        registry.register("b", "desc", {})
        assert set(registry.tool_names) == {"a", "b"}


# ============================================================
# ToolExecutor Tests
# ============================================================

class TestToolExecutor:
    
    def test_validate_arguments_success(self):
        registry = ToolRegistry()
        registry.register(
            "add",
            "Add two numbers",
            {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            },
            func=lambda a, b: a + b
        )
        executor = ToolExecutor(registry)
        valid, error = executor.validate_arguments("add", {"a": 1, "b": 2})
        assert valid is True
        assert error == ""
    
    def test_validate_arguments_missing_required(self):
        registry = ToolRegistry()
        registry.register(
            "add",
            "Add two numbers",
            {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
        )
        executor = ToolExecutor(registry)
        valid, error = executor.validate_arguments("add", {"a": 1})
        assert valid is False
        assert "Missing required argument" in error
    
    def test_validate_arguments_type_error(self):
        registry = ToolRegistry()
        registry.register(
            "add",
            "Add two numbers",
            {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                }
            }
        )
        executor = ToolExecutor(registry)
        valid, error = executor.validate_arguments("add", {"a": "not_int", "b": 2})
        assert valid is False
        assert "expected integer" in error
    
    def test_validate_arguments_enum_error(self):
        registry = ToolRegistry()
        registry.register(
            "choose",
            "Choose option",
            {
                "type": "object",
                "properties": {
                    "option": {"type": "string", "enum": ["A", "B"]}
                }
            }
        )
        executor = ToolExecutor(registry)
        valid, error = executor.validate_arguments("choose", {"option": "C"})
        assert valid is False
        assert "must be one of" in error
    
    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        registry = ToolRegistry()
        registry.register(
            "multiply",
            "Multiply two numbers",
            {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                },
                "required": ["x", "y"]
            },
            func=lambda x, y: x * y
        )
        executor = ToolExecutor(registry)
        result = await executor.execute("multiply", {"x": 3, "y": 4})
        assert result == 12
    
    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        async def async_add(a, b):
            return a + b
        
        registry = ToolRegistry()
        registry.register(
            "async_add",
            "Async add",
            {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            },
            func=async_add
        )
        executor = ToolExecutor(registry)
        result = await executor.execute("async_add", {"a": 1, "b": 2})
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_execute_no_func_raises(self):
        registry = ToolRegistry()
        registry.register("no_func", "No function", {})
        executor = ToolExecutor(registry)
        with pytest.raises(RuntimeError, match="no executable function"):
            await executor.execute("no_func", {})
    
    @pytest.mark.asyncio
    async def test_execute_batch(self):
        registry = ToolRegistry()
        registry.register(
            "add",
            "Add",
            {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]},
            func=lambda a, b: a + b
        )
        registry.register(
            "bad",
            "Bad tool",
            {},
            func=lambda: (_ for _ in ()).throw(Exception("error"))
        )
        executor = ToolExecutor(registry)
        results = await executor.execute_batch([
            {"tool_name": "add", "arguments": {"a": 1, "b": 2}},
            {"tool_name": "bad", "arguments": {}}
        ])
        assert results[0]["success"] is True
        assert results[0]["result"] == 3
        assert results[1]["success"] is False
        assert "error" in results[1]["error"]


# ============================================================
# Medical Tools Tests
# ============================================================

class TestMedicalTools:
    
    def test_register_medical_tools(self):
        registry = ToolRegistry()
        register_medical_tools(registry)
        
        expected_tools = [
            "diagnose", "analyze_imaging", "search_literature",
            "calculate_sample_size", "generate_medical_note",
            "check_medication_safety", "export_document"
        ]
        
        for tool_name in expected_tools:
            assert registry.has_tool(tool_name), f"Tool '{tool_name}' not registered"
        
        tools = registry.list_tools()
        assert len(tools) == len(expected_tools)
    
    def test_diagnose_tool(self):
        from medai.tools.medical_tools import diagnose
        result = diagnose(symptoms=["多饮", "多食", "多尿"], age=55, gender="男")
        
        assert "differential_diagnoses" in result
        assert "primary_diagnosis" in result
        assert result["patient_info"]["age"] == 55
        assert result["patient_info"]["gender"] == "男"
        
        # 应匹配到糖尿病
        diagnoses = [d["disease"] for d in result["differential_diagnoses"]]
        assert "2型糖尿病" in diagnoses
    
    def test_analyze_imaging_tool(self):
        from medai.tools.medical_tools import analyze_imaging
        report = "胸部CT平扫：右肺上叶见磨玻璃影，大小约8mm。诊断意见：右肺上叶磨玻璃结节，建议随访。"
        result = analyze_imaging(report_text=report)
        
        assert result["body_part"] == "右肺"
        assert result["modality"] == "CT"
        assert len(result["findings"]) > 0
    
    def test_check_medication_safety_tool(self):
        from medai.tools.medical_tools import check_medication_safety
        result = check_medication_safety(
            medications=["华法林", "阿司匹林"],
            patient_conditions={
                "allergies": [],
                "doses": {}
            }
        )
        
        assert result["total_warnings"] > 0
        assert result["is_safe"] is False  # 华法林+阿司匹林有高风险相互作用
    
    def test_generate_medical_note_admission(self):
        from medai.tools.medical_tools import generate_medical_note
        note = generate_medical_note(
            note_type="admission_note",
            patient_info={
                "patient_name": "张三",
                "gender": "男",
                "age": 45,
                "chief_complaint": "胸痛1小时",
                "diagnosis": "冠心病"
            }
        )
        assert "入院记录" in note
        assert "张三" in note
        assert "冠心病" in note
    
    def test_generate_medical_note_progress(self):
        from medai.tools.medical_tools import generate_medical_note
        note = generate_medical_note(
            note_type="progress_note",
            patient_info={
                "subjective": "患者诉胸痛缓解",
                "temperature": 36.8
            }
        )
        assert "病程记录" in note
        assert "胸痛缓解" in note
    
    def test_generate_medical_note_discharge(self):
        from medai.tools.medical_tools import generate_medical_note
        note = generate_medical_note(
            note_type="discharge_note",
            patient_info={
                "patient_name": "张三",
                "gender": "男",
                "age": 45,
                "admission_diagnosis": "冠心病",
                "discharge_diagnosis": "冠心病 稳定型心绞痛",
                "discharge_orders": "1. 阿司匹林 100mg qd"
            }
        )
        assert "出院记录" in note
        assert "稳定型心绞痛" in note
    
    def test_calculate_sample_size_proportion(self):
        from medai.tools.medical_tools import calculate_sample_size
        result = calculate_sample_size(
            study_type="proportion",
            alpha=0.05,
            power=0.8,
            p1=0.3,
            p2=0.5
        )
        assert "sample_size" in result
        assert result["sample_size"]["total"] > 0
    
    def test_calculate_sample_size_mean(self):
        from medai.tools.medical_tools import calculate_sample_size
        result = calculate_sample_size(
            study_type="mean",
            alpha=0.05,
            power=0.8,
            mean1=50,
            mean2=60,
            std_dev=15
        )
        assert "sample_size" in result
        assert result["sample_size"]["total"] > 0
    
    def test_calculate_sample_size_invalid_type(self):
        from medai.tools.medical_tools import calculate_sample_size
        with pytest.raises(ValueError, match="不支持的研究类型"):
            calculate_sample_size(study_type="invalid", alpha=0.05, power=0.8)
    
    @pytest.mark.skip(reason="Requires network access")
    def test_search_literature(self):
        from medai.tools.medical_tools import search_literature
        result = search_literature(query="diabetes treatment", max_results=3)
        assert isinstance(result, list)
    
    def test_export_document_paper(self, tmp_path):
        from medai.tools.medical_tools import export_document
        file_path = str(tmp_path / "test_paper.docx")
        result = export_document(
            doc_type="paper",
            data={
                "title": "Test Paper",
                "authors": "Test Author",
                "abstract": "This is a test abstract.",
                "introduction": "Introduction text.",
                "methods": "Methods text.",
                "results": "Results text.",
                "discussion": "Discussion text.",
                "conclusion": "Conclusion text.",
                "references": ["Ref 1", "Ref 2"]
            },
            file_path=file_path
        )
        assert result["success"] is True
        assert result["file_path"] == file_path
        import os
        assert os.path.exists(file_path)
