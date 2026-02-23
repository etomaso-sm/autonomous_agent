from speaker.models import (
    TaskStatus,
    TaskSource,
    ImpasseType,
    Task,
    WorkingMemory,
    Perception,
    Thought,
    TaskAttempt,
    HumanRequest,
    Delegation,
)


def test_task_status_values():
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.ACTIVE.value == "active"
    assert TaskStatus.BLOCKED.value == "blocked"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_task_source_values():
    assert TaskSource.HUMAN.value == "human"
    assert TaskSource.PARENT_AGENT.value == "parent_agent"
    assert TaskSource.SELF.value == "self"


def test_impasse_type_values():
    assert ImpasseType.INFORMATION.value == "information"
    assert ImpasseType.CAPABILITY.value == "capability"
    assert ImpasseType.DECISION.value == "decision"
    assert ImpasseType.RESOURCE.value == "resource"


def test_task_defaults():
    task = Task(description="Do something")
    assert task.status == TaskStatus.PENDING
    assert task.source == TaskSource.HUMAN
    assert task.priority == 0.5
    assert task.id  # auto-generated UUID
    assert task.attempts == []
    assert task.subtasks == []


def test_task_blocked():
    task = Task(description="Need info")
    task.status = TaskStatus.BLOCKED
    task.blocked_by = "human_request_1"
    task.blocked_reason = "awaiting_human"
    assert task.status == TaskStatus.BLOCKED
    assert task.blocked_reason == "awaiting_human"


def test_working_memory_clear():
    wm = WorkingMemory(
        current_task=Task(description="test"),
        perceptions=[Perception(kind="event", source="test", content="x")],
        scratchpad=[Thought(content="thinking")],
        active_context={"key": "value"},
    )
    assert wm.current_task is not None
    wm.clear()
    assert wm.current_task is None
    assert wm.perceptions == []
    assert wm.scratchpad == []
    assert wm.active_context == {}
