"""Integration test: create an agent, submit a task, run cycles, verify behavior."""

import asyncio
import pytest
from unittest.mock import MagicMock
from datetime import timedelta

from speaker import (
    AutonomousAgent,
    AgentConfig,
    Task,
    TaskStatus,
    ReACTStrategy,
    TaskDrive,
    CuriosityDrive,
    CompletionDrive,
)


@pytest.fixture
def mock_osma():
    client = MagicMock()
    client.threads.create.return_value = MagicMock(id=1, metadata={})
    client.threads.create_message.return_value = MagicMock(content="done")
    client.threads.get.return_value = MagicMock(metadata={})
    client.threads.update_metadata.return_value = None
    return client


@pytest.mark.asyncio
async def test_full_agent_lifecycle(mock_osma):
    """Test: create agent → submit task → run cycles → task gets processed."""
    config = AgentConfig(
        strategy=ReACTStrategy(),
        osma_client=mock_osma,
        drives=[TaskDrive(), CuriosityDrive(), CompletionDrive()],
        heartbeat_interval=timedelta(seconds=0.1),
    )
    agent = AutonomousAgent(config)

    # Submit a task
    task = Task(description="Summarize the Q4 report")
    agent.submit_task(task)
    assert agent.task_queue.has_work()

    # Run a few cycles manually
    for _ in range(3):
        result = await agent.run_one_cycle()
        assert result.cycle_number > 0

    # The task should have been picked up (status changed from pending)
    t = agent.task_queue.get(task.id)
    assert t.status != TaskStatus.PENDING  # Should be active or beyond


@pytest.mark.asyncio
async def test_multiple_tasks_priority(mock_osma):
    """Higher priority tasks should be processed first."""
    config = AgentConfig(
        strategy=ReACTStrategy(),
        osma_client=mock_osma,
        drives=[TaskDrive()],
        heartbeat_interval=timedelta(seconds=1),
    )
    agent = AutonomousAgent(config)

    low = Task(description="Low priority", priority=0.1)
    high = Task(description="High priority", priority=0.9)
    agent.submit_task(low)
    agent.submit_task(high)

    result = await agent.run_one_cycle()
    # The high-priority task should be the current task
    assert agent.task_queue.get(high.id).status == TaskStatus.ACTIVE


@pytest.mark.asyncio
async def test_agent_start_stop(mock_osma):
    """Agent can start and stop cleanly."""
    config = AgentConfig(
        strategy=ReACTStrategy(),
        osma_client=mock_osma,
        drives=[TaskDrive()],
        heartbeat_interval=timedelta(seconds=0.05),
    )
    agent = AutonomousAgent(config)
    agent.submit_task(Task(description="Work"))

    run_task = asyncio.create_task(agent.start())
    await asyncio.sleep(0.2)
    agent.stop()
    await asyncio.wait_for(run_task, timeout=2.0)

    assert not agent.is_running
    assert agent.cycle_count >= 1
