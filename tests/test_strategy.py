# tests/test_strategy.py
from speaker.strategy import Strategy, CognitiveContext, ReACTStrategy
from speaker.models import (
    Task,
    TaskStatus,
    WorkingMemory,
    Perception,
)
from speaker.actions import CognitiveAction, Think, Execute, UpdateTask, Impasse


def test_strategy_is_abstract():
    """Strategy cannot be instantiated directly."""
    import pytest
    with pytest.raises(TypeError):
        Strategy()


def test_cognitive_context_creation():
    ctx = CognitiveContext(
        working_memory=WorkingMemory(),
        perceptions=[],
        active_tasks=[],
        retrieved_memories=[],
        drive_pressures={"task": 0.5},
    )
    assert ctx.drive_pressures["task"] == 0.5


def test_react_strategy_returns_actions():
    strategy = ReACTStrategy()
    ctx = CognitiveContext(
        working_memory=WorkingMemory(
            current_task=Task(description="Find the answer to X"),
        ),
        perceptions=[Perception(kind="new_task", source="human", content="Find X")],
        active_tasks=[Task(description="Find the answer to X")],
        retrieved_memories=[],
        drive_pressures={"task": 0.8},
    )
    actions = strategy.reason(ctx)
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, CognitiveAction) for a in actions)


def test_react_strategy_with_no_task():
    """When there's no current task, strategy should return empty or Sleep."""
    strategy = ReACTStrategy()
    ctx = CognitiveContext(
        working_memory=WorkingMemory(),
        perceptions=[],
        active_tasks=[],
        retrieved_memories=[],
        drive_pressures={},
    )
    actions = strategy.reason(ctx)
    assert isinstance(actions, list)
