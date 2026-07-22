"""
Medical Tool Test Harness Package
医学工具测试框架包

提供统一的测试基础设施，用于验证 MedAIagents 中所有医学工具的正确性、
健壮性和性能表现。

Usage:
    from tests.harness import MedicalToolHarness
    harness = MedicalToolHarness()
    harness.run_all_tests()
"""

from .medical_tool_harness import MedicalToolHarness, ToolTestCase, TestResult, HarnessTestStatus

__all__ = ["MedicalToolHarness", "ToolTestCase", "TestResult", "HarnessTestStatus"]
