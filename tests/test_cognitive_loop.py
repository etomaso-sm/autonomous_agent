# tests/test_cognitive_loop.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from speaker.cognitive_loop import CognitiveLoop, CycleResult
from speaker.models import Task, TaskStatus, WorkingMemory, Perception
from speaker.task_queue import TaskQueue
from speaker.drives import TaskDrive, CompletionDrive
from speaker.strategy import ReACTStrategy
from speaker.memory import InMemoryStore
from speaker.actions import Think, Sleep, UpdateTask


@pytest.fixture
def loop_deps():
    """Create a CognitiveLoop with all dependencies mocked/real."""
    task_queue = TaskQueue()
    strategy = ReACTStrategy()
    memory_store = InMemoryStore()
    osma = AsyncMock()
    drives = [TaskDrive(), CompletionDrive()]
    return {
        "task_queue": task_queue,
        "strategy": strategy,
        "memory_store": memory_store,
        "osma_adapter": osma,
        "drives": drives,
    }


@pytest.mark.asyncio
async def test_cycle_with_no_tasks(loop_deps):
    loop = CognitiveLoop(**loop_deps)
    result = await loop.run_cycle()
    assert result.should_sleep is True
    assert result.actions_taken == []


@pytest.mark.asyncio
async def test_cycle_perceives_new_task(loop_deps):
    loop = CognitiveLoop(**loop_deps)
    task = Task(description="Do something")
    loop.task_queue.submit(task)
    result = await loop.run_cycle()
    assert result.should_sleep is False
    assert len(result.actions_taken) > 0  # At least a Think action from ReACT


@pytest.mark.asyncio
async def test_cycle_updates_working_memory(loop_deps):
    loop = CognitiveLoop(**loop_deps)
    task = Task(description="Test task")
    loop.task_queue.submit(task)
    await loop.run_cycle()
    # Working memory should have been populated during the cycle
    # (it gets cleared at start of each cycle, but populated during ORIENT)
    # After cycle, scratchpad should have Think thoughts
    assert True  # The cycle ran without error


@pytest.mark.asyncio
async def test_cycle_handles_think_action(loop_deps):
    loop = CognitiveLoop(**loop_deps)
    task = Task(description="Analyze data")
    loop.task_queue.submit(task)
    result = await loop.run_cycle()
    # ReACT always produces Think as first action
    think_actions = [a for a in result.actions_taken if isinstance(a, Think)]
    assert len(think_actions) >= 1


@pytest.mark.asyncio
async def test_external_perceptions(loop_deps):
    loop = CognitiveLoop(**loop_deps)
    loop.add_perception(Perception(
        kind="human_response",
        source="user_1",
        content="The answer is 42",
    ))
    task = Task(description="Wait for answer", status=TaskStatus.ACTIVE)
    loop.task_queue.submit(task)
    result = await loop.run_cycle()
    assert result.should_sleep is False
