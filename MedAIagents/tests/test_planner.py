"""
任务规划器单元测试
Task Planner Unit Tests
"""

import json
from datetime import datetime

import pytest

from medai.planner import SubTask, TaskPlan, TaskPlanner, TaskStatus


# ============================================================
# TaskPlan / SubTask Model Tests
# ============================================================

class TestTaskPlanModel:

    def test_create_task_plan(self):
        plan = TaskPlan(
            goal="测试目标",
            subtasks=[
                SubTask(id="t1", description="子任务1"),
                SubTask(id="t2", description="子任务2"),
            ],
        )
        assert plan.goal == "测试目标"
        assert len(plan.subtasks) == 2
        assert plan.created_at is not None
        assert plan.completed_at is None

    def test_task_plan_serialization(self):
        plan = TaskPlan(
            goal="测试序列化",
            subtasks=[
                SubTask(id="t1", description="子任务1", tool="test_tool", arguments={"key": "val"}),
            ],
        )
        data = plan.model_dump()
        assert data["goal"] == "测试序列化"
        assert data["subtasks"][0]["id"] == "t1"
        assert data["subtasks"][0]["status"] == "pending"

    def test_get_subtask(self):
        plan = TaskPlan(
            goal="测试查找",
            subtasks=[
                SubTask(id="t1", description="子任务1"),
                SubTask(id="t2", description="子任务2"),
            ],
        )
        assert plan.get_subtask("t1").description == "子任务1"
        assert plan.get_subtask("nonexistent") is None

    def test_is_completed(self):
        plan = TaskPlan(
            goal="测试完成状态",
            subtasks=[
                SubTask(id="t1", description="子任务1", status=TaskStatus.COMPLETED),
                SubTask(id="t2", description="子任务2", status=TaskStatus.COMPLETED),
            ],
        )
        assert plan.is_completed() is True

        plan.subtasks[0].status = TaskStatus.PENDING
        assert plan.is_completed() is False

    def test_reset(self):
        st = SubTask(id="t1", description="子任务1", status=TaskStatus.COMPLETED, result="done")
        plan = TaskPlan(goal="测试重置", subtasks=[st])
        plan.completed_at = datetime.now()
        plan.reset()

        assert st.status == TaskStatus.PENDING
        assert st.result is None
        assert st.error is None
        assert plan.completed_at is None

    def test_self_dependency_removed(self):
        st = SubTask(id="t1", description="子任务1", dependencies=["t1", "t2"])
        assert "t1" not in st.dependencies
        assert "t2" in st.dependencies


# ============================================================
# Topological Sort Tests
# ============================================================

class TestTopologicalSort:

    def test_no_dependencies(self):
        planner = TaskPlanner(llm_router=None)
        subtasks = [
            SubTask(id="a", description="A"),
            SubTask(id="b", description="B"),
            SubTask(id="c", description="C"),
        ]
        result = planner._topological_sort(subtasks)
        assert result is not None
        assert len(result) == 3
        # 无依赖时顺序可能任意
        assert set(st.id for st in result) == {"a", "b", "c"}

    def test_with_dependencies(self):
        planner = TaskPlanner(llm_router=None)
        subtasks = [
            SubTask(id="a", description="A", dependencies=[]),
            SubTask(id="b", description="B", dependencies=["a"]),
            SubTask(id="c", description="C", dependencies=["a", "b"]),
        ]
        result = planner._topological_sort(subtasks)
        assert result is not None
        ids = [st.id for st in result]
        assert ids.index("a") < ids.index("b")
        assert ids.index("b") < ids.index("c")

    def test_circular_dependency(self):
        planner = TaskPlanner(llm_router=None)
        subtasks = [
            SubTask(id="a", description="A", dependencies=["c"]),
            SubTask(id="b", description="B", dependencies=["a"]),
            SubTask(id="c", description="C", dependencies=["b"]),
        ]
        result = planner._topological_sort(subtasks)
        assert result is None

    def test_complex_dependencies(self):
        planner = TaskPlanner(llm_router=None)
        #     a
        #    / \
        #   b   c
        #    \ /
        #     d
        subtasks = [
            SubTask(id="a", description="A"),
            SubTask(id="b", description="B", dependencies=["a"]),
            SubTask(id="c", description="C", dependencies=["a"]),
            SubTask(id="d", description="D", dependencies=["b", "c"]),
        ]
        result = planner._topological_sort(subtasks)
        assert result is not None
        ids = [st.id for st in result]
        assert ids.index("a") < ids.index("b")
        assert ids.index("a") < ids.index("c")
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")


# ============================================================
# Plan Tests (with mocked LLM)
# ============================================================

class MockLLMRouter:
    """Mock LLM 路由，用于测试"""

    def __init__(self, response: str = None):
        self.response = response

    async def chat(self, messages, **kwargs):
        return self.response


class TestPlan:

    @pytest.mark.asyncio
    async def test_plan_success(self):
        mock_response = json.dumps({
            "goal": "分析患者病情",
            "subtasks": [
                {"id": "t1", "description": "收集症状", "tool": "diagnose", "arguments": {}, "dependencies": []},
                {"id": "t2", "description": "分析影像", "tool": "analyze_imaging", "arguments": {}, "dependencies": ["t1"]},
            ]
        })
        planner = TaskPlanner(llm_router=MockLLMRouter(mock_response))
        plan = await planner.plan("请分析这位患者的病情", [])

        assert plan.goal == "分析患者病情"
        assert len(plan.subtasks) == 2
        assert plan.subtasks[0].id == "t1"
        assert plan.subtasks[1].dependencies == ["t1"]

    @pytest.mark.asyncio
    async def test_plan_fallback_on_error(self):
        class FailingLLM:
            async def chat(self, messages, **kwargs):
                raise RuntimeError("LLM failed")

        planner = TaskPlanner(llm_router=FailingLLM())
        plan = await planner.plan("测试请求", [])

        assert plan.goal == "测试请求"
        assert len(plan.subtasks) == 1
        assert plan.subtasks[0].description == "测试请求"

    def test_parse_plan_with_markdown(self):
        planner = TaskPlanner(llm_router=None)
        response = '```json\n{"goal": "g", "subtasks": [{"id": "t1", "description": "d"}]}\n```'
        plan = planner._parse_plan(response)
        assert plan.goal == "g"
        assert plan.subtasks[0].id == "t1"

    def test_parse_plan_invalid_json_fallback(self):
        planner = TaskPlanner(llm_router=None)
        response = 'Some text before { "goal": "g", "subtasks": [] } some text after'
        plan = planner._parse_plan(response)
        assert plan.goal == "g"


# ============================================================
# Execute Tests
# ============================================================

class MockExecutor:
    """Mock 执行器"""

    def __init__(self, fail_tool: str = None):
        self.fail_tool = fail_tool
        self.calls = []

    async def execute(self, tool_name: str, arguments: dict):
        self.calls.append((tool_name, arguments))
        if tool_name == self.fail_tool:
            raise RuntimeError(f"Tool {tool_name} failed")
        return {"tool": tool_name, "args": arguments}


class TestExecute:

    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        planner = TaskPlanner(llm_router=None)
        plan = TaskPlan(
            goal="并行测试",
            subtasks=[
                SubTask(id="t1", description="任务1", tool="tool_a"),
                SubTask(id="t2", description="任务2", tool="tool_b"),
                SubTask(id="t3", description="任务3", tool="tool_c", dependencies=["t1"]),
            ],
        )
        executor = MockExecutor()
        result_plan = await planner.execute(plan, executor, max_parallel=3)

        assert result_plan.subtasks[0].status == TaskStatus.COMPLETED
        assert result_plan.subtasks[1].status == TaskStatus.COMPLETED
        assert result_plan.subtasks[2].status == TaskStatus.COMPLETED
        assert result_plan.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_retry(self):
        planner = TaskPlanner(llm_router=None)
        plan = TaskPlan(
            goal="重试测试",
            subtasks=[
                SubTask(id="t1", description="任务1", tool="fail_once"),
            ],
        )

        class FailOnceExecutor:
            def __init__(self):
                self.call_count = 0

            async def execute(self, tool_name: str, arguments: dict):
                self.call_count += 1
                if self.call_count == 1:
                    raise RuntimeError("first failure")
                return {"success": True}

        executor = FailOnceExecutor()
        result_plan = await planner.execute(plan, executor, max_parallel=1)

        # 第一次失败后重试成功
        assert result_plan.subtasks[0].status == TaskStatus.COMPLETED
        assert executor.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_failure_propagation(self):
        planner = TaskPlanner(llm_router=None)
        plan = TaskPlan(
            goal="失败传播测试",
            subtasks=[
                SubTask(id="t1", description="任务1", tool="bad_tool"),
                SubTask(id="t2", description="任务2", tool="tool_b", dependencies=["t1"]),
            ],
        )
        executor = MockExecutor(fail_tool="bad_tool")
        result_plan = await planner.execute(plan, executor, max_parallel=1)

        assert result_plan.subtasks[0].status == TaskStatus.FAILED
        # 依赖 t1 的 t2 也应标记为失败
        assert result_plan.subtasks[1].status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_max_parallel(self):
        planner = TaskPlanner(llm_router=None)
        plan = TaskPlan(
            goal="并发限制测试",
            subtasks=[
                SubTask(id="t1", description="任务1", tool="tool_a"),
                SubTask(id="t2", description="任务2", tool="tool_b"),
                SubTask(id="t3", description="任务3", tool="tool_c"),
            ],
        )
        executor = MockExecutor()
        result_plan = await planner.execute(plan, executor, max_parallel=2)

        for st in result_plan.subtasks:
            assert st.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_circular_dependency(self):
        planner = TaskPlanner(llm_router=None)
        plan = TaskPlan(
            goal="循环依赖测试",
            subtasks=[
                SubTask(id="t1", description="任务1", dependencies=["t2"]),
                SubTask(id="t2", description="任务2", dependencies=["t1"]),
            ],
        )
        executor = MockExecutor()
        with pytest.raises(ValueError, match="循环"):
            await planner.execute(plan, executor)
