"""
Skill 系统测试
"""

import pytest
import os
import tempfile
from medai.skills.models import Skill, SkillStep, SkillParameter, StepType, SkillExecutionResult
from medai.skills.registry import SkillRegistry
from medai.skills.executor import SkillExecutor
from medai.skills.learner import SkillLearner
from medai.skills.builtin import register_builtin_skills, _build_lung_cancer_diagnosis_skill


# === Models Tests ===

class TestSkillModels:
    """测试 Skill 数据模型"""
    
    def test_skill_parameter_creation(self):
        """测试参数创建"""
        param = SkillParameter(
            name="symptoms",
            description="患者症状",
            type="string",
            required=True
        )
        assert param.name == "symptoms"
        assert param.type == "string"
        assert param.required is True
    
    def test_skill_step_creation(self):
        """测试步骤创建"""
        step = SkillStep(
            name="test_step",
            step_type=StepType.LLM_CALL,
            config={"prompt_template": "Hello ${name}"},
            output_var="result"
        )
        assert step.name == "test_step"
        assert step.step_type == StepType.LLM_CALL
        assert step.output_var == "result"
        assert step.id.startswith("step_")
    
    def test_skill_creation(self):
        """测试 Skill 创建"""
        skill = Skill(
            name="test_skill",
            description="测试技能",
            parameters=[
                SkillParameter(name="input", description="输入", type="string", required=True)
            ],
            steps=[
                SkillStep(name="step1", step_type=StepType.OUTPUT, config={"output_template": "${input}"})
            ],
            tags=["test"]
        )
        assert skill.name == "test_skill"
        assert len(skill.parameters) == 1
        assert len(skill.steps) == 1
        assert skill.id.startswith("skill_")
    
    def test_skill_parameter_validation(self):
        """测试参数验证"""
        skill = Skill(
            name="test_skill",
            description="测试",
            parameters=[
                SkillParameter(name="required_param", description="必需", type="string", required=True),
                SkillParameter(name="optional_param", description="可选", type="string", required=False, default="default_value")
            ],
            steps=[]
        )
        
        # 缺少必需参数
        valid, errors = skill.validate_parameters({})
        assert valid is False
        assert any("required_param" in e for e in errors)
        
        # 完整参数
        valid, errors = skill.validate_parameters({"required_param": "value"})
        assert valid is True
        assert len(errors) == 0
        
        # 枚举参数
        skill2 = Skill(
            name="enum_test",
            description="测试",
            parameters=[
                SkillParameter(name="choice", description="选择", type="string", required=True, enum=["A", "B", "C"])
            ],
            steps=[]
        )
        valid, errors = skill2.validate_parameters({"choice": "D"})
        assert valid is False
    
    def test_skill_to_openai_function(self):
        """测试转换为 OpenAI Function 格式"""
        skill = Skill(
            name="diagnose",
            description="诊断疾病",
            parameters=[
                SkillParameter(name="symptoms", description="症状", type="string", required=True),
                SkillParameter(name="age", description="年龄", type="number", required=False, default=30)
            ],
            steps=[]
        )
        
        func = skill.to_openai_function()
        assert func["type"] == "function"
        assert func["function"]["name"] == "diagnose"
        assert "symptoms" in func["function"]["parameters"]["properties"]
        assert "age" in func["function"]["parameters"]["properties"]
        assert "symptoms" in func["function"]["parameters"]["required"]


# === Registry Tests ===

class TestSkillRegistry:
    """测试 Skill 注册表"""
    
    @pytest.fixture
    def temp_registry(self):
        """创建临时注册表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)
            yield registry
    
    def test_register_and_get(self, temp_registry):
        """测试注册和获取"""
        skill = Skill(name="test_skill", description="测试")
        temp_registry.register(skill)
        
        retrieved = temp_registry.get("test_skill")
        assert retrieved is not None
        assert retrieved.name == "test_skill"
    
    def test_unregister(self, temp_registry):
        """测试注销"""
        skill = Skill(name="removable", description="可删除")
        temp_registry.register(skill)
        assert temp_registry.has("removable")
        
        temp_registry.unregister("removable")
        assert not temp_registry.has("removable")
    
    def test_search(self, temp_registry):
        """测试搜索"""
        temp_registry.register(Skill(name="lung_diagnosis", description="肺部诊断", tags=["clinical"]))
        temp_registry.register(Skill(name="meta_analysis", description="Meta分析", tags=["research"]))
        
        results = temp_registry.search("肺部")
        assert len(results) == 1
        assert results[0].name == "lung_diagnosis"
        
        results = temp_registry.search("分析")
        assert len(results) == 1
    
    def test_list_and_filter(self, temp_registry):
        """测试列表和过滤"""
        temp_registry.register(Skill(name="builtin1", description="内置1", is_builtin=True))
        temp_registry.register(Skill(name="custom1", description="自定义1", is_builtin=False, tags=["test"]))
        
        all_skills = temp_registry.list_skills()
        assert len(all_skills) == 2
        
        builtin_skills = temp_registry.list_skills(builtin_only=True)
        assert len(builtin_skills) == 1
        
        tagged_skills = temp_registry.list_skills(tag="test")
        assert len(tagged_skills) == 1
    
    def test_persistence(self, temp_registry):
        """测试持久化"""
        skill = Skill(name="persistent", description="持久化测试")
        temp_registry.register(skill)
        
        # 创建新注册表实例，应该能加载已保存的 skill
        new_registry = SkillRegistry(storage_path=temp_registry.storage_path)
        assert new_registry.has("persistent")
    
    def test_to_openai_functions(self, temp_registry):
        """测试转换为 OpenAI functions"""
        temp_registry.register(_build_lung_cancer_diagnosis_skill())
        functions = temp_registry.to_openai_functions()
        assert len(functions) == 1
        assert functions[0]["function"]["name"] == "lung_cancer_diagnosis_workflow"
    
    def test_usage_stats(self, temp_registry):
        """测试使用统计更新"""
        skill = Skill(name="stats_test", description="统计测试")
        temp_registry.register(skill)
        
        temp_registry.update_usage_stats("stats_test", True)
        skill = temp_registry.get("stats_test")
        assert skill.usage_count == 1
        assert skill.success_rate == 1.0
        
        temp_registry.update_usage_stats("stats_test", False)
        skill = temp_registry.get("stats_test")
        assert skill.usage_count == 2
        assert skill.success_rate == 0.5
    
    def test_import_export(self, temp_registry):
        """测试导入导出"""
        skill = Skill(name="exportable", description="可导出")
        temp_registry.register(skill)
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = f.name
        
        try:
            assert temp_registry.export_skill("exportable", export_path) is True
            
            new_registry = SkillRegistry(storage_path=tempfile.mkdtemp())
            imported = new_registry.import_skill(export_path)
            assert imported is not None
            assert imported.name == "exportable"
        finally:
            os.unlink(export_path)


# === Executor Tests ===

class TestSkillExecutor:
    """测试 Skill 执行器"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器"""
        registry = SkillRegistry(storage_path=tempfile.mkdtemp())
        return SkillExecutor(registry)
    
    @pytest.mark.asyncio
    async def test_execute_simple_skill(self, executor):
        """测试执行简单 Skill"""
        skill = Skill(
            name="echo",
            description="回显",
            parameters=[SkillParameter(name="message", description="消息", type="string", required=True)],
            steps=[
                SkillStep(
                    name="echo",
                    step_type=StepType.OUTPUT,
                    config={"output_template": "Echo: ${message}"},
                    output_var="output"
                )
            ]
        )
        executor.skill_registry.register(skill)
        
        result = await executor.execute("echo", {"message": "hello"})
        assert result.success is True
        assert "Echo: hello" in str(result.output)
    
    @pytest.mark.asyncio
    async def test_execute_skill_not_found(self, executor):
        """测试执行不存在的 Skill"""
        result = await executor.execute("nonexistent", {})
        assert result.success is False
        assert "未找到" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_parameter_validation(self, executor):
        """测试参数验证失败"""
        skill = Skill(
            name="required_params",
            description="需要参数",
            parameters=[SkillParameter(name="name", description="名称", type="string", required=True)],
            steps=[]
        )
        executor.skill_registry.register(skill)
        
        result = await executor.execute("required_params", {})
        assert result.success is False
        assert "参数验证失败" in result.error
    
    @pytest.mark.asyncio
    async def test_condition_step(self, executor):
        """测试条件步骤"""
        skill = Skill(
            name="conditional",
            description="条件测试",
            parameters=[SkillParameter(name="flag", description="标志", type="boolean", required=True)],
            steps=[
                SkillStep(
                    name="check",
                    step_type=StepType.CONDITION,
                    config={"condition_expression": "${flag} == True"},
                    output_var="condition_result"
                ),
                SkillStep(
                    name="output",
                    step_type=StepType.OUTPUT,
                    config={"output_template": "Result: ${flag}"},
                    output_var="output"
                )
            ]
        )
        executor.skill_registry.register(skill)
        
        result = await executor.execute("conditional", {"flag": True})
        assert result.success is True
    
    def test_render_template(self, executor):
        """测试模板渲染"""
        template = "Hello ${name}, you are ${age} years old."
        variables = {"name": "Alice", "age": 30}
        result = executor._render_template(template, variables)
        assert result == "Hello Alice, you are 30 years old."
    
    def test_evaluate_condition(self, executor):
        """测试条件评估"""
        variables = {"age": 25, "name": "test"}
        
        assert executor._evaluate_condition("${age} > 18", variables) is True
        assert executor._evaluate_condition("${age} < 18", variables) is False
        assert executor._evaluate_condition("${name} == 'test'", variables) is True
        assert executor._evaluate_condition("true", variables) is True
        assert executor._evaluate_condition("false", variables) is False
    
    def test_evaluate_condition_security(self, executor):
        """测试条件表达式安全性"""
        # 危险字符应该被阻止
        assert executor._evaluate_condition("__import__('os').system('ls')", {}) is False
        assert executor._evaluate_condition("exec('print(1)')", {}) is False


# === Learner Tests ===

class TestSkillLearner:
    """测试 Skill 学习器"""
    
    @pytest.fixture
    def learner(self):
        return SkillLearner()
    
    def test_contains_workflow(self, learner):
        """测试工作流检测"""
        assert learner._contains_workflow("第一步：收集数据。第二步：分析数据。") is True
        assert learner._contains_workflow("Step 1: Collect data. Step 2: Analyze.") is True
        assert learner._contains_workflow("首先打开文件，然后读取内容。") is True
        assert learner._contains_workflow("这是一个普通的回答。") is False
    
    def test_extract_steps(self, learner):
        """测试步骤提取"""
        text = "第一步：收集患者症状。第二步：进行体格检查。第三步：开具检查单。"
        steps = learner._extract_steps(text)
        assert len(steps) == 3
        assert steps[0].step_type == StepType.LLM_CALL
    
    def test_extract_steps_english(self, learner):
        """测试英文步骤提取"""
        text = "Step 1: Collect symptoms. Step 2: Physical exam. Step 3: Order tests."
        steps = learner._extract_steps(text)
        assert len(steps) == 3
    
    def test_detect_step_type(self, learner):
        """测试步骤类型检测"""
        assert learner._detect_step_type("如果患者发烧，则进行血常规检查") == StepType.CONDITION
        assert learner._detect_step_type("查询数据库获取结果") == StepType.TOOL_CALL
        assert learner._detect_step_type("输出最终报告") == StepType.OUTPUT
        assert learner._detect_step_type("分析患者症状") == StepType.LLM_CALL
    
    def test_learn_from_conversation(self, learner):
        """测试从对话学习"""
        conversation = [
            {"role": "user", "content": "请告诉我肺癌的诊断流程"},
            {"role": "assistant", "content": """肺癌诊断流程如下：
第一步：评估患者症状（咳嗽、咯血、胸痛等）和吸烟史。
第二步：进行胸部CT检查，观察肺部结节或肿块。
第三步：根据CT结果，决定是否进行支气管镜或穿刺活检。
第四步：病理确诊后，进行分期检查（PET-CT、脑MRI等）。
第五步：制定治疗方案。"""}
        ]
        
        skill = learner.learn_from_conversation(conversation, skill_name="lung_cancer_flow")
        assert skill is not None
        assert skill.name == "lung_cancer_flow"
        assert len(skill.steps) >= 3
        assert "auto_learned" in skill.tags
    
    def test_learn_from_conversation_no_workflow(self, learner):
        """测试无工作流对话"""
        conversation = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮您的？"}
        ]
        skill = learner.learn_from_conversation(conversation)
        assert skill is None
    
    def test_infer_param_type(self, learner):
        """测试参数类型推断"""
        assert learner._infer_param_type("患者年龄") == "number"
        assert learner._infer_param_type("是否吸烟") == "boolean"
        assert learner._infer_param_type("症状描述") == "string"
        assert learner._infer_param_type("药物列表") == "array"
    
    def test_estimate_confidence(self, learner):
        """测试置信度评估"""
        high_conf = "第一步：A。第二步：B。第三步：C。这是标准操作流程。"
        assert learner._estimate_confidence(high_conf) > 0.5
        
        low_conf = "这是一个普通的句子。"
        assert learner._estimate_confidence(low_conf) < 0.5
    
    def test_suggest_skills(self, learner):
        """测试 Skill 建议"""
        conversation = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
            {"role": "user", "content": "告诉我操作步骤"},
            {"role": "assistant", "content": "第一步：准备。第二步：执行。第三步：完成。"},
        ]
        suggestions = learner.suggest_skills(conversation)
        assert len(suggestions) > 0
        assert all("confidence" in s for s in suggestions)


# === Builtin Tests ===

class TestBuiltinSkills:
    """测试内置 Skills"""
    
    @pytest.fixture
    def registry_with_builtins(self):
        """创建带内置 Skill 的注册表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)
            register_builtin_skills(registry)
            yield registry
    
    def test_register_builtin_skills(self, registry_with_builtins):
        """测试注册内置 Skills"""
        skills = registry_with_builtins.list_skills()
        assert len(skills) == 10
        
        names = registry_with_builtins.list_skill_names()
        assert "lung_cancer_diagnosis_workflow" in names
        assert "meta_analysis_writing_workflow" in names
        assert "grant_proposal_writing_workflow" in names
    
    def test_builtin_skill_structure(self, registry_with_builtins):
        """测试内置 Skill 结构"""
        skill = registry_with_builtins.get("lung_cancer_diagnosis_workflow")
        assert skill is not None
        assert skill.is_builtin is True
        assert len(skill.parameters) >= 2
        assert len(skill.steps) >= 2
        assert "clinical" in skill.tags
    
    def test_meta_analysis_skill(self, registry_with_builtins):
        """测试 Meta 分析 Skill"""
        skill = registry_with_builtins.get("meta_analysis_writing_workflow")
        assert skill is not None
        assert any(p.name == "effect_measure" for p in skill.parameters)
        effect_param = next(p for p in skill.parameters if p.name == "effect_measure")
        assert effect_param.enum == ["OR", "RR", "MD", "SMD"]
    
    def test_rct_protocol_skill(self, registry_with_builtins):
        """测试 RCT Skill"""
        skill = registry_with_builtins.get("rct_protocol_design_workflow")
        assert skill is not None
        # 检查是否有工具调用步骤
        tool_steps = [s for s in skill.steps if s.step_type == StepType.TOOL_CALL]
        assert len(tool_steps) >= 1
    
    def test_grant_proposal_skill(self, registry_with_builtins):
        """测试基金申请 Skill"""
        skill = registry_with_builtins.get("grant_proposal_writing_workflow")
        assert skill is not None
        assert any(p.name == "grant_type" for p in skill.parameters)
    
    def test_imaging_report_skill(self, registry_with_builtins):
        """测试影像报告 Skill"""
        skill = registry_with_builtins.get("imaging_report_structuring_workflow")
        assert skill is not None
        modality_param = next(p for p in skill.parameters if p.name == "modality")
        assert modality_param.enum == ["CT", "MRI", "X-ray", "Ultrasound", "PET-CT"]
    
    def test_drug_safety_skill(self, registry_with_builtins):
        """测试用药安全 Skill"""
        skill = registry_with_builtins.get("drug_safety_check_workflow")
        assert skill is not None
        assert any(p.name == "medications" for p in skill.parameters)
        assert any(p.name == "patient_age" for p in skill.parameters)


# === Integration Tests ===

class TestSkillIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_skill_lifecycle(self):
        """测试 Skill 完整生命周期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)
            executor = SkillExecutor(registry)
            
            # 1. 注册 Skill
            skill = Skill(
                name="integration_test",
                description="集成测试",
                parameters=[SkillParameter(name="value", description="值", type="string", required=True)],
                steps=[
                    SkillStep(
                        name="process",
                        step_type=StepType.OUTPUT,
                        config={"output_template": "Processed: ${value}"},
                        output_var="output"
                    )
                ]
            )
            registry.register(skill)
            
            # 2. 执行 Skill
            result = await executor.execute("integration_test", {"value": "test"})
            assert result.success is True
            assert "Processed: test" in str(result.output)
            
            # 3. 验证统计
            skill = registry.get("integration_test")
            assert skill.usage_count == 1
            
            # 4. 搜索
            results = registry.search("集成")
            assert len(results) == 1
            
            # 5. 注销
            registry.unregister("integration_test")
            assert not registry.has("integration_test")
    
    def test_builtin_registration_count(self):
        """测试内置 Skill 注册数量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)
            skills = register_builtin_skills(registry)
            assert len(skills) == 10
            assert len(registry.list_skills()) == 10
            assert all(s.is_builtin for s in registry.list_skills())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
