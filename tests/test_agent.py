# tests/test_agent.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import timedelta

from speaker.agent import AutonomousAgent, AgentConfig
from speaker.models import Task, TaskStatus
from speaker.strategy import ReACTStrategy
from speaker.drives import TaskDrive


@pytest.fixture
def agent_config():
    mock_osma = MagicMock()
    mock_osma.threads.create.return_value = MagicMock(id=1, metadata={})
    mock_osma.threads.create_message.return_value = MagicMock(content="response")
    mock_osma.threads.get.return_value = MagicMock(metadata={})
    mock_osma.threads.update_metadata.return_value = None
    return AgentConfig(
        strategy=ReACTStrategy(),
        osma_client=mock_osma,
        drives=[TaskDrive()],
        heartbeat_interval=timedelta(seconds=0.1),
    )


def test_agent_creation(agent_config):
    agent = AutonomousAgent(agent_config)
    assert agent.is_running is False


@pytest.mark.asyncio
async def test_agent_submit_task(agent_config):
    agent = AutonomousAgent(agent_config)
    task = Task(description="Test task")
    agent.submit_task(task)
    assert len(agent.task_queue) == 1


@pytest.mark.asyncio
async def test_agent_run_one_cycle(agent_config):
    agent = AutonomousAgent(agent_config)
    task = Task(description="Quick task")
    agent.submit_task(task)
    result = await agent.run_one_cycle()
    assert result.cycle_number == 1
    assert len(result.actions_taken) > 0


@pytest.mark.asyncio
async def test_agent_start_and_stop(agent_config):
    agent = AutonomousAgent(agent_config)
    agent.submit_task(Task(description="Something"))

    # Start in background, let it run a couple cycles, then stop
    run_task = asyncio.create_task(agent.start())
    await asyncio.sleep(0.3)
    agent.stop()
    await asyncio.wait_for(run_task, timeout=2.0)

    assert agent.is_running is False
    assert agent.cycle_count >= 1
