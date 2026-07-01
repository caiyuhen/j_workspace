"""
多 Agent 编排单元测试
Multi-Agent Orchestration Unit Tests
"""

import pytest

from medai.agents import (
    AgentOrchestrator,
    BaseAgent,
    BioinformaticsAgent,
    ClinicalAgent,
    ImagingAgent,
    ResearchAgent,
    WritingAgent,
)


# ============================================================
# Mock LLM Router
# ============================================================

class MockLLMRouter:
    """Mock LLM 路由"""

    def __init__(self, response: str = "mock response"):
        self.response = response
        self.messages_history = []

    async def chat(self, messages, **kwargs):
        self.messages_history.append(messages)
        return self.response


# ============================================================
# BaseAgent Tests
# ============================================================

class TestBaseAgent:

    def test_init(self):
        llm = MockLLMRouter()
        agent = BaseAgent(
            name="测试Agent",
            role="test",
            system_prompt="你是一个测试助手",
            llm_router=llm,
        )
        assert agent.name == "测试Agent"
        assert agent.role == "test"
        assert agent.system_prompt == "你是一个测试助手"
        assert agent.memory == []
        assert len(agent.tools) == 0

    @pytest.mark.asyncio
    async def test_run(self):
        llm = MockLLMRouter("你好，这是回复")
        agent = BaseAgent(
            name="测试Agent",
            role="test",
            system_prompt="系统提示",
            llm_router=llm,
        )
        result = await agent.run("用户任务")
        assert result == "你好，这是回复"
        assert len(agent.memory) == 2
        assert agent.memory[0]["role"] == "user"
        assert agent.memory[0]["content"] == "用户任务"
        assert agent.memory[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_run_with_context(self):
        llm = MockLLMRouter()
        agent = BaseAgent(
            name="测试Agent",
            role="test",
            system_prompt="系统提示",
            llm_router=llm,
        )
        await agent.run("任务", context={"key": "value"})
        # 验证消息中包含上下文
        last_messages = llm.messages_history[-1]
        assert any("key" in str(msg.get("content", "")) for msg in last_messages)

    def test_clear_memory(self):
        llm = MockLLMRouter()
        agent = BaseAgent(
            name="测试Agent",
            role="test",
            system_prompt="系统提示",
            llm_router=llm,
        )
        agent.memory = [{"role": "user", "content": "test"}]
        agent.clear_memory()
        assert agent.memory == []

    def test_get_memory(self):
        llm = MockLLMRouter()
        agent = BaseAgent(
            name="测试Agent",
            role="test",
            system_prompt="系统提示",
            llm_router=llm,
        )
        agent.memory = [
            {"role": "user", "content": f"msg{i}"}
            for i in range(15)
        ]
        assert len(agent.get_memory(limit=5)) == 5
        assert len(agent.get_memory(limit=20)) == 15


# ============================================================
# Specialized Agent Tests
# ============================================================

class TestSpecializedAgents:

    def test_clinical_agent(self):
        llm = MockLLMRouter()
        agent = ClinicalAgent(llm_router=llm)
        assert agent.name == "临床Agent"
        assert agent.role == "clinical"
        assert agent.tools.has_tool("diagnose")
        assert agent.tools.has_tool("check_medication_safety")
        assert agent.tools.has_tool("generate_medical_note")

    def test_imaging_agent(self):
        llm = MockLLMRouter()
        agent = ImagingAgent(llm_router=llm)
        assert agent.name == "影像Agent"
        assert agent.role == "imaging"
        assert agent.tools.has_tool("analyze_imaging")

    def test_research_agent(self):
        llm = MockLLMRouter()
        agent = ResearchAgent(llm_router=llm)
        assert agent.name == "科研Agent"
        assert agent.role == "research"
        assert agent.tools.has_tool("search_literature")
        assert agent.tools.has_tool("calculate_sample_size")

    def test_writing_agent(self):
        llm = MockLLMRouter()
        agent = WritingAgent(llm_router=llm)
        assert agent.name == "写作Agent"
        assert agent.role == "writing"
        assert agent.tools.has_tool("export_document")

    def test_bioinformatics_agent(self):
        llm = MockLLMRouter()
        agent = BioinformaticsAgent(llm_router=llm)
        assert agent.name == "生信Agent"
        assert agent.role == "bioinformatics"
        assert agent.tools.has_tool("export_document")


# ============================================================
# AgentOrchestrator Tests
# ============================================================

class TestAgentOrchestrator:

    def test_register_and_get_agent(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        agent = ClinicalAgent(llm_router=llm)

        orch.register_agent(agent)
        assert orch.get_agent("临床Agent") is agent

        with pytest.raises(KeyError, match="未找到"):
            orch.get_agent("不存在的Agent")

    def test_list_agents(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        orch.register_agent(ClinicalAgent(llm_router=llm))
        orch.register_agent(ImagingAgent(llm_router=llm))

        agents_info = orch.list_agents()
        assert len(agents_info) == 2
        names = {a["name"] for a in agents_info}
        assert "临床Agent" in names
        assert "影像Agent" in names

    @pytest.mark.asyncio
    async def test_delegate(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter("delegate result")
        orch.register_agent(ClinicalAgent(llm_router=llm))
        orch.register_agent(ImagingAgent(llm_router=llm))

        results = await orch.delegate("测试任务", required_roles=["clinical", "imaging"])
        assert "临床Agent" in results
        assert "影像Agent" in results
        assert results["临床Agent"] == "delegate result"

    @pytest.mark.asyncio
    async def test_delegate_missing_role(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        orch.register_agent(ClinicalAgent(llm_router=llm))

        results = await orch.delegate("测试任务", required_roles=["nonexistent"])
        assert "error" in results

    @pytest.mark.asyncio
    async def test_collaborate(self):
        orch = AgentOrchestrator()

        class CountingLLM:
            def __init__(self):
                self.count = 0

            async def chat(self, messages, **kwargs):
                self.count += 1
                return f"step{self.count}"

        llm = CountingLLM()
        orch.register_agent(ClinicalAgent(llm_router=llm))
        orch.register_agent(WritingAgent(llm_router=llm))

        result = await orch.collaborate(
            "撰写病例报告",
            agent_sequence=["临床Agent", "写作Agent"],
        )
        assert result == "step2"

    @pytest.mark.asyncio
    async def test_collaborate_missing_agent(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        orch.register_agent(ClinicalAgent(llm_router=llm))

        result = await orch.collaborate("任务", agent_sequence=["不存在的Agent"])
        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_collaborate_empty_sequence(self):
        orch = AgentOrchestrator()
        result = await orch.collaborate("任务", agent_sequence=[])
        assert result == "未指定协作 Agent 序列"

    def test_find_agent_by_role(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        clinical = ClinicalAgent(llm_router=llm)
        orch.register_agent(clinical)

        found = orch._find_agent_by_role("clinical")
        assert found is clinical
        assert orch._find_agent_by_role("nonexistent") is None

    def test_select_agent_for_subtask(self):
        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        clinical = ClinicalAgent(llm_router=llm)
        imaging = ImagingAgent(llm_router=llm)
        orch.register_agent(clinical)
        orch.register_agent(imaging)

        # 模拟子任务
        class FakeSubTask:
            def __init__(self, description, tool=None):
                self.description = description
                self.tool = tool

        st1 = FakeSubTask("诊断患者症状", tool="diagnose")
        assert orch._select_agent_for_subtask(st1).role == "clinical"

        st2 = FakeSubTask("分析CT影像", tool="analyze_imaging")
        assert orch._select_agent_for_subtask(st2).role == "imaging"

        st3 = FakeSubTask("其他任务")
        # 默认返回第一个注册的
        assert orch._select_agent_for_subtask(st3) is clinical

    def test_synthesize_results(self):
        orch = AgentOrchestrator()
        results = {"t1": "结果A", "t2": "结果B"}
        text = orch._synthesize_results(results)
        assert "任务执行结果汇总" in text
        assert "结果A" in text
        assert "结果B" in text

    @pytest.mark.asyncio
    async def test_auto_orchestrate(self):
        from medai.planner import TaskPlanner

        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        orch.register_agent(ClinicalAgent(llm_router=llm))
        orch.register_agent(WritingAgent(llm_router=llm))

        # Mock planner 返回简单计划
        class MockPlanner:
            async def plan(self, task, tools):
                from medai.planner import SubTask, TaskPlan
                return TaskPlan(
                    goal=task,
                    subtasks=[
                        SubTask(id="st1", description="临床分析"),
                        SubTask(id="st2", description="撰写报告", dependencies=["st1"]),
                    ],
                )

        result = await orch.auto_orchestrate("完成一个医学任务", planner=MockPlanner())
        assert "任务执行结果汇总" in result
        assert "st1" in result
        assert "st2" in result

    @pytest.mark.asyncio
    async def test_auto_orchestrate_empty_plan(self):
        from medai.planner import TaskPlan

        orch = AgentOrchestrator()
        llm = MockLLMRouter()
        orch.register_agent(ClinicalAgent(llm_router=llm))

        class MockPlanner:
            async def plan(self, task, tools):
                return TaskPlan(goal=task, subtasks=[])

        result = await orch.auto_orchestrate("任务", planner=MockPlanner())
        assert "任务分解结果为空" in result
