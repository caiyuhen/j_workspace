"""
自进化机制测试
"""
import pytest
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

from medai.evolution.learner import FeedbackCollector
from medai.evolution.optimizer import PromptOptimizer
from medai.evolution.tracker import PerformanceTracker


@pytest.fixture
def temp_feedback_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_perf_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


class TestFeedbackCollector:
    def test_record_and_query(self, temp_feedback_db):
        collector = FeedbackCollector(db_path=temp_feedback_db)
        collector.record_feedback(
            task_id='t1', task_type='diagnosis',
            input_text='symptoms', output_text='result',
            feedback='good', rating=5
        )
        history = collector.get_feedback_history(task_type='diagnosis')
        assert len(history) == 1
        assert history[0]['task_id'] == 't1'
        assert history[0]['rating'] == 5

    def test_average_rating(self, temp_feedback_db):
        collector = FeedbackCollector(db_path=temp_feedback_db)
        collector.record_feedback('t1', 'diagnosis', 'i1', 'o1', 'ok', 4)
        collector.record_feedback('t2', 'diagnosis', 'i2', 'o2', 'bad', 2)
        collector.record_feedback('t3', 'summary', 'i3', 'o3', 'good', 5)

        assert collector.get_average_rating('diagnosis') == 3.0
        assert collector.get_average_rating() == pytest.approx(11 / 3)

    def test_common_issues(self, temp_feedback_db):
        collector = FeedbackCollector(db_path=temp_feedback_db)
        collector.record_feedback('t1', 'diagnosis', 'i1', 'o1', '结果有错误', 2)
        collector.record_feedback('t2', 'diagnosis', 'i2', 'o2', '很好', 5)
        collector.record_feedback('t3', 'diagnosis', 'i3', 'o3', '不准确', 1)

        issues = collector.get_common_issues('diagnosis')
        assert len(issues) == 2
        assert '结果有错误' in issues
        assert '不准确' in issues

    def test_invalid_rating(self, temp_feedback_db):
        collector = FeedbackCollector(db_path=temp_feedback_db)
        with pytest.raises(ValueError):
            collector.record_feedback('t1', 'x', 'i', 'o', 'f', 0)


class TestPerformanceTracker:
    def test_record_and_report(self, temp_perf_db):
        tracker = PerformanceTracker(db_path=temp_perf_db)
        tracker.record_execution('diagnosis', 1200, True, {'prompt_tokens': 100, 'completion_tokens': 50})
        tracker.record_execution('diagnosis', 800, False, {'prompt_tokens': 80, 'completion_tokens': 20})

        report = tracker.get_performance_report(days=1)
        assert report['total_tasks'] == 2
        assert report['success_rate'] == 0.5
        assert report['avg_duration_ms'] == 1000.0
        assert report['token_usage']['prompt_tokens'] == 180

    def test_empty_report(self, temp_perf_db):
        tracker = PerformanceTracker(db_path=temp_perf_db)
        report = tracker.get_performance_report(days=7)
        assert report['total_tasks'] == 0
        assert report['success_rate'] == 0.0


@pytest.mark.asyncio
async def test_prompt_optimizer():
    mock_router = MagicMock()
    mock_router.chat = AsyncMock(return_value='Optimized prompt: Be helpful and accurate.')

    optimizer = PromptOptimizer(mock_router)
    result = await optimizer.optimize_system_prompt(
        current_prompt='You are a doctor.',
        role='medical_diagnosis',
        feedback_history=[
            {'rating': 2, 'feedback': 'Not accurate enough'},
            {'rating': 3, 'feedback': 'Okay but could be better'}
        ]
    )

    assert 'helpful' in result or 'Optimized prompt' in result
    mock_router.chat.assert_awaited_once()
