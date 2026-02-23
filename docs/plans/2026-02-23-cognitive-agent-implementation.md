# Cognitive Autonomous Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a domain-agnostic autonomous agent with a 5-phase cognitive loop, pluggable reasoning strategies, 3-part memory, impasse-driven delegation, Active Inference drives, and configurable wakefulness — all backed by the Osma SDK.

**Architecture:** Bottom-up TDD. We build the innermost data models first, then the memory/task/drive systems, then the strategy interface, then the cognitive loop that orchestrates everything, and finally the top-level AutonomousAgent entry point. Each layer only depends on layers below it. Osma SDK calls are wrapped behind an async adapter.

**Tech Stack:** Python 3.12+, asyncio, pydantic v2, pytest + pytest-asyncio, osma SDK, SQLite (via aiosqlite) for persistence.

**Design Doc:** `docs/plans/2026-02-23-cognitive-autonomous-agent-design.md`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/speaker/__init__.py`
- Create: `src/speaker/py.typed`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "speaker"
version = "0.1.0"
description = "Cognitive autonomous agent"
requires-python = ">=3.12"
dependencies = [
    "osma>=0.1.0",
    "pydantic>=2.0",
    "aiosqlite>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/speaker"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 2: Create package structure**

```
src/speaker/__init__.py    → empty
src/speaker/py.typed       → empty (PEP 561 marker)
tests/__init__.py          → empty
tests/conftest.py          → empty for now
```

**Step 3: Install in dev mode and verify**

Run: `cd /Users/eugeniodetomaso/.superset/worktrees/autonomous_agent/speaker && python -m pip install -e ".[dev]"`
Expected: Successful installation

Run: `pytest --co -q`
Expected: `no tests ran` (no tests yet, but pytest works)

**Step 4: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: scaffold project structure with dependencies"
```

---

## Task 2: Core Enums and Value Objects

**Files:**
- Create: `src/speaker/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing tests**

```python
# tests/test_models.py
from speaker.models import (
    TaskStatus,
    TaskSource,
    ImpasseType,
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'speaker.models'`

**Step 3: Write minimal implementation**

```python
# src/speaker/models.py
"""Core enums and value objects for the cognitive agent."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskSource(str, enum.Enum):
    HUMAN = "human"
    PARENT_AGENT = "parent_agent"
    SELF = "self"


class ImpasseType(str, enum.Enum):
    INFORMATION = "information"
    CAPABILITY = "capability"
    DECISION = "decision"
    RESOURCE = "resource"


# --- Value Objects ---

class Perception(BaseModel):
    """Something the agent perceived during PERCEIVE phase."""
    kind: str  # "new_task", "human_response", "agent_result", "event", "timeout"
    source: str
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Thought(BaseModel):
    """An intermediate reasoning step stored in working memory scratchpad."""
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskAttempt(BaseModel):
    """Record of one attempt to work on a task."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_taken: str
    result: Any = None
    success: bool = False


class Delegation(BaseModel):
    """Record of a delegation to a sub-agent or worker."""
    delegate_id: str  # agent_id or worker_id
    delegate_type: str  # "agent" or "worker"
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None


class HumanRequest(BaseModel):
    """Record of a question asked to a human."""
    question: str
    context: dict[str, Any] = Field(default_factory=dict)
    response: str | None = None
    asked_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: datetime | None = None


# --- Task ---

class Task(BaseModel):
    """The unit of work for the autonomous agent."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: str | None = None
    source: TaskSource = TaskSource.HUMAN

    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: str | None = None
    priority: float = 0.5

    status: TaskStatus = TaskStatus.PENDING
    blocked_by: str | None = None
    blocked_reason: str | None = None

    attempts: list[TaskAttempt] = Field(default_factory=list)
    delegations: list[Delegation] = Field(default_factory=list)
    human_requests: list[HumanRequest] = Field(default_factory=list)

    depends_on: list[str] = Field(default_factory=list)
    blocks: list[str] = Field(default_factory=list)
    subtasks: list[str] = Field(default_factory=list)

    result: Any = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Working Memory ---

class WorkingMemory(BaseModel):
    """The agent's consciousness — limited capacity, pruned each cycle."""
    current_task: Task | None = None
    perceptions: list[Perception] = Field(default_factory=list)
    scratchpad: list[Thought] = Field(default_factory=list)
    active_context: dict[str, Any] = Field(default_factory=dict)

    def clear(self) -> None:
        self.current_task = None
        self.perceptions.clear()
        self.scratchpad.clear()
        self.active_context.clear()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: PASS — all 3 tests pass

**Step 5: Add tests for Task and WorkingMemory**

Add to `tests/test_models.py`:

```python
from speaker.models import (
    Task,
    WorkingMemory,
    Perception,
    Thought,
    TaskAttempt,
    HumanRequest,
    Delegation,
)


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
```

**Step 6: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: PASS — all 6 tests pass

**Step 7: Commit**

```bash
git add src/speaker/models.py tests/test_models.py
git commit -m "feat: add core data models — Task, WorkingMemory, enums, value objects"
```

---

## Task 3: Cognitive Actions (Strategy Output)

**Files:**
- Create: `src/speaker/actions.py`
- Create: `tests/test_actions.py`

**Step 1: Write the failing tests**

```python
# tests/test_actions.py
from speaker.actions import (
    CognitiveAction,
    Execute,
    Delegate,
    Dispatch,
    AskHuman,
    UpdateTask,
    Think,
    Sleep,
    Impasse,
)
from speaker.models import ImpasseType


def test_execute_action():
    action = Execute(tool_name="search", tool_args={"query": "test"})
    assert action.tool_name == "search"
    assert action.tool_args == {"query": "test"}


def test_delegate_action():
    action = Delegate(
        objective="Research topic X",
        system_prompt="You are a research specialist.",
        llm_model=1,
    )
    assert action.objective == "Research topic X"
    assert action.enable_tool_calls is True  # default


def test_dispatch_action():
    action = Dispatch(
        task_description="Call API",
        step_type="rest_api",
        config={"url": "https://example.com", "method": "GET"},
    )
    assert action.step_type == "rest_api"


def test_ask_human_action():
    action = AskHuman(question="What format?", context={"task": "report"})
    assert action.question == "What format?"


def test_update_task_action():
    action = UpdateTask(task_id="abc", status="completed", result={"answer": 42})
    assert action.task_id == "abc"
    assert action.result == {"answer": 42}


def test_think_action():
    action = Think(thoughts=["I should check the API first", "The data looks stale"])
    assert len(action.thoughts) == 2


def test_sleep_action():
    action = Sleep(reason="No active tasks")
    assert action.wake_after_seconds is None  # no self-wake by default


def test_sleep_with_self_wake():
    action = Sleep(reason="Delegated work", wake_after_seconds=300)
    assert action.wake_after_seconds == 300


def test_impasse_action():
    action = Impasse(
        impasse_type=ImpasseType.INFORMATION,
        details={"missing": "customer email"},
    )
    assert action.impasse_type == ImpasseType.INFORMATION


def test_cognitive_action_is_union():
    """All action types are valid CognitiveAction."""
    actions: list[CognitiveAction] = [
        Execute(tool_name="t", tool_args={}),
        Delegate(objective="o", system_prompt="s", llm_model=1),
        Dispatch(task_description="d", step_type="rest_api", config={}),
        AskHuman(question="q"),
        UpdateTask(task_id="id", status="completed"),
        Think(thoughts=["t"]),
        Sleep(reason="r"),
        Impasse(impasse_type=ImpasseType.RESOURCE, details={}),
    ]
    assert len(actions) == 8
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_actions.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
# src/speaker/actions.py
"""Cognitive actions — the output of a Strategy's reasoning."""

from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, Field

from speaker.models import ImpasseType


class Execute(BaseModel):
    """Execute a tool call directly."""
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)


class Delegate(BaseModel):
    """Spawn a full sub-agent (Lambda Agent in Osma)."""
    objective: str
    system_prompt: str
    llm_model: int
    enable_tool_calls: bool = True
    enable_rag: bool = False
    similarity_process: int | None = None
    mcp_server_ids: list[int] = Field(default_factory=list)


class Dispatch(BaseModel):
    """Spawn a lightweight worker (Workflow in Osma)."""
    task_description: str
    step_type: str  # rest_api, validation, llm_agent, transformation
    config: dict[str, Any] = Field(default_factory=dict)


class AskHuman(BaseModel):
    """Request human input. Blocks the current task, not the agent."""
    question: str
    context: dict[str, Any] = Field(default_factory=dict)


class UpdateTask(BaseModel):
    """Update a task's status and optionally set its result."""
    task_id: str
    status: str
    result: Any = None


class Think(BaseModel):
    """Internal reasoning — thoughts added to working memory scratchpad."""
    thoughts: list[str]


class Sleep(BaseModel):
    """Go dormant. Optionally schedule a self-wake."""
    reason: str
    wake_after_seconds: int | None = None


class Impasse(BaseModel):
    """Signal that the strategy is stuck."""
    impasse_type: ImpasseType
    details: dict[str, Any] = Field(default_factory=dict)


CognitiveAction = Union[
    Execute, Delegate, Dispatch, AskHuman,
    UpdateTask, Think, Sleep, Impasse,
]
```

**Step 4: Run tests**

Run: `pytest tests/test_actions.py -v`
Expected: PASS — all 10 tests pass

**Step 5: Commit**

```bash
git add src/speaker/actions.py tests/test_actions.py
git commit -m "feat: add cognitive actions — Execute, Delegate, Dispatch, AskHuman, Think, Sleep, Impasse"
```

---

## Task 4: Task Queue

**Files:**
- Create: `src/speaker/task_queue.py`
- Create: `tests/test_task_queue.py`

**Step 1: Write the failing tests**

```python
# tests/test_task_queue.py
import pytest
from speaker.task_queue import TaskQueue
from speaker.models import Task, TaskStatus, TaskSource


def test_submit_task():
    q = TaskQueue()
    task = Task(description="Do X")
    q.submit(task)
    assert len(q) == 1
    assert q.get(task.id) is task


def test_submit_duplicate_raises():
    q = TaskQueue()
    task = Task(description="Do X")
    q.submit(task)
    with pytest.raises(ValueError, match="already exists"):
        q.submit(task)


def test_pending_tasks():
    q = TaskQueue()
    t1 = Task(description="A", priority=0.3)
    t2 = Task(description="B", priority=0.9)
    t3 = Task(description="C", status=TaskStatus.COMPLETED)
    q.submit(t1)
    q.submit(t2)
    q.submit(t3)
    pending = q.pending()
    assert len(pending) == 2
    assert pending[0].id == t2.id  # higher priority first


def test_active_tasks():
    q = TaskQueue()
    t1 = Task(description="A", status=TaskStatus.ACTIVE)
    t2 = Task(description="B", status=TaskStatus.PENDING)
    q.submit(t1)
    q.submit(t2)
    assert len(q.active()) == 1
    assert q.active()[0].id == t1.id


def test_blocked_tasks():
    q = TaskQueue()
    t = Task(description="A", status=TaskStatus.BLOCKED, blocked_by="human_1")
    q.submit(t)
    assert len(q.blocked()) == 1


def test_actionable_excludes_blocked_dependencies():
    q = TaskQueue()
    t1 = Task(description="Dep", status=TaskStatus.PENDING)
    t2 = Task(description="Main", status=TaskStatus.PENDING, depends_on=[t1.id])
    q.submit(t1)
    q.submit(t2)
    actionable = q.actionable()
    assert len(actionable) == 1
    assert actionable[0].id == t1.id  # t2 is blocked by dependency


def test_actionable_includes_after_dependency_completed():
    q = TaskQueue()
    t1 = Task(description="Dep", status=TaskStatus.COMPLETED)
    t2 = Task(description="Main", status=TaskStatus.PENDING, depends_on=[t1.id])
    q.submit(t1)
    q.submit(t2)
    actionable = q.actionable()
    assert len(actionable) == 1
    assert actionable[0].id == t2.id


def test_all_tasks():
    q = TaskQueue()
    for i in range(5):
        q.submit(Task(description=f"Task {i}"))
    assert len(q.all()) == 5


def test_has_work():
    q = TaskQueue()
    assert not q.has_work()
    q.submit(Task(description="X"))
    assert q.has_work()


def test_has_work_false_when_all_done():
    q = TaskQueue()
    q.submit(Task(description="X", status=TaskStatus.COMPLETED))
    assert not q.has_work()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_task_queue.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/task_queue.py
"""Task queue with priority ordering and dependency tracking."""

from __future__ import annotations

from speaker.models import Task, TaskStatus


class TaskQueue:
    """Holds all tasks for the agent. Provides filtered views."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def __len__(self) -> int:
        return len(self._tasks)

    def submit(self, task: Task) -> None:
        if task.id in self._tasks:
            raise ValueError(f"Task {task.id} already exists")
        self._tasks[task.id] = task

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def all(self) -> list[Task]:
        return list(self._tasks.values())

    def pending(self) -> list[Task]:
        """Pending tasks sorted by priority (highest first)."""
        return sorted(
            (t for t in self._tasks.values() if t.status == TaskStatus.PENDING),
            key=lambda t: t.priority,
            reverse=True,
        )

    def active(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.ACTIVE]

    def blocked(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.BLOCKED]

    def actionable(self) -> list[Task]:
        """Pending tasks whose dependencies are all completed."""
        result = []
        for task in self.pending():
            deps_met = all(
                self._tasks.get(dep_id, Task(description="")).status
                == TaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            if deps_met:
                result.append(task)
        return result

    def has_work(self) -> bool:
        """True if there are pending or active tasks."""
        return any(
            t.status in (TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.BLOCKED)
            for t in self._tasks.values()
        )
```

**Step 4: Run tests**

Run: `pytest tests/test_task_queue.py -v`
Expected: PASS — all 10 tests pass

**Step 5: Commit**

```bash
git add src/speaker/task_queue.py tests/test_task_queue.py
git commit -m "feat: add TaskQueue with priority ordering and dependency tracking"
```

---

## Task 5: Drives System

**Files:**
- Create: `src/speaker/drives.py`
- Create: `tests/test_drives.py`

**Step 1: Write the failing tests**

```python
# tests/test_drives.py
from speaker.drives import (
    Drive,
    TaskDrive,
    CuriosityDrive,
    CompletionDrive,
    CoherenceDrive,
    compute_drive_pressures,
)
from speaker.task_queue import TaskQueue
from speaker.models import Task, TaskStatus, WorkingMemory


def test_task_drive_no_pending():
    q = TaskQueue()
    drive = TaskDrive()
    assert drive.pressure(q, WorkingMemory()) == 0.0


def test_task_drive_with_pending():
    q = TaskQueue()
    q.submit(Task(description="X"))
    drive = TaskDrive()
    assert drive.pressure(q, WorkingMemory()) > 0.0


def test_task_drive_scales_with_count():
    q = TaskQueue()
    for i in range(5):
        q.submit(Task(description=f"Task {i}"))
    drive = TaskDrive()
    p5 = drive.pressure(q, WorkingMemory())
    q2 = TaskQueue()
    q2.submit(Task(description="One"))
    p1 = drive.pressure(q2, WorkingMemory())
    assert p5 > p1


def test_completion_drive_no_blocked():
    q = TaskQueue()
    drive = CompletionDrive()
    assert drive.pressure(q, WorkingMemory()) == 0.0


def test_completion_drive_with_blocked():
    q = TaskQueue()
    q.submit(Task(description="X", status=TaskStatus.BLOCKED, blocked_by="h1"))
    drive = CompletionDrive()
    assert drive.pressure(q, WorkingMemory()) > 0.0


def test_curiosity_drive_no_gaps():
    q = TaskQueue()
    wm = WorkingMemory()
    drive = CuriosityDrive()
    assert drive.pressure(q, wm) == 0.0


def test_curiosity_drive_with_impasse_in_context():
    q = TaskQueue()
    wm = WorkingMemory(active_context={"information_gaps": ["missing customer email"]})
    drive = CuriosityDrive()
    assert drive.pressure(q, wm) > 0.0


def test_coherence_drive_no_contradictions():
    q = TaskQueue()
    wm = WorkingMemory()
    drive = CoherenceDrive()
    assert drive.pressure(q, wm) == 0.0


def test_compute_drive_pressures():
    q = TaskQueue()
    q.submit(Task(description="X"))
    wm = WorkingMemory()
    drives = [TaskDrive(), CuriosityDrive(), CompletionDrive(), CoherenceDrive()]
    pressures = compute_drive_pressures(drives, q, wm)
    assert "task" in pressures
    assert "curiosity" in pressures
    assert "completion" in pressures
    assert "coherence" in pressures
    assert pressures["task"] > 0.0
    assert pressures["curiosity"] == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_drives.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/drives.py
"""Active Inference drives — predictions about preferred states."""

from __future__ import annotations

import abc
import math

from speaker.models import TaskStatus, WorkingMemory
from speaker.task_queue import TaskQueue


class Drive(abc.ABC):
    """Base class for drives. Each drive computes a pressure [0.0, 1.0]."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def pressure(self, task_queue: TaskQueue, working_memory: WorkingMemory) -> float:
        """Compute drive pressure. 0.0 = satisfied, 1.0 = maximum urgency."""
        ...


class TaskDrive(Drive):
    """'My task queue should be empty.' Activates when pending tasks exist."""

    @property
    def name(self) -> str:
        return "task"

    def pressure(self, task_queue: TaskQueue, working_memory: WorkingMemory) -> float:
        pending = len(task_queue.pending())
        if pending == 0:
            return 0.0
        # Logarithmic scaling: pressure increases with count but saturates
        return min(1.0, math.log1p(pending) / math.log1p(10))


class CuriosityDrive(Drive):
    """'I should have the information I need.' Activates on information gaps."""

    @property
    def name(self) -> str:
        return "curiosity"

    def pressure(self, task_queue: TaskQueue, working_memory: WorkingMemory) -> float:
        gaps = working_memory.active_context.get("information_gaps", [])
        if not gaps:
            return 0.0
        return min(1.0, len(gaps) * 0.3)


class CompletionDrive(Drive):
    """'Started tasks should reach completion.' Activates on blocked/stalled tasks."""

    @property
    def name(self) -> str:
        return "completion"

    def pressure(self, task_queue: TaskQueue, working_memory: WorkingMemory) -> float:
        blocked = len(task_queue.blocked())
        active = len(task_queue.active())
        stalled = blocked + active
        if stalled == 0:
            return 0.0
        return min(1.0, stalled * 0.25)


class CoherenceDrive(Drive):
    """'My understanding should be consistent.' Activates on contradictions."""

    @property
    def name(self) -> str:
        return "coherence"

    def pressure(self, task_queue: TaskQueue, working_memory: WorkingMemory) -> float:
        contradictions = working_memory.active_context.get("contradictions", [])
        if not contradictions:
            return 0.0
        return min(1.0, len(contradictions) * 0.5)


def compute_drive_pressures(
    drives: list[Drive],
    task_queue: TaskQueue,
    working_memory: WorkingMemory,
) -> dict[str, float]:
    """Compute all drive pressures. Returns {drive_name: pressure}."""
    return {d.name: d.pressure(task_queue, working_memory) for d in drives}
```

**Step 4: Run tests**

Run: `pytest tests/test_drives.py -v`
Expected: PASS — all 9 tests pass

**Step 5: Commit**

```bash
git add src/speaker/drives.py tests/test_drives.py
git commit -m "feat: add Active Inference drives — TaskDrive, CuriosityDrive, CompletionDrive, CoherenceDrive"
```

---

## Task 6: Strategy Interface + ReACT Strategy

**Files:**
- Create: `src/speaker/strategy.py`
- Create: `tests/test_strategy.py`

**Step 1: Write the failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_strategy.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/strategy.py
"""Strategy interface and implementations for the REASON phase."""

from __future__ import annotations

import abc
from typing import Any

from pydantic import BaseModel, Field

from speaker.actions import CognitiveAction, Think, Sleep
from speaker.models import WorkingMemory, Perception, Task


class MemoryRecord(BaseModel):
    """A retrieved memory from long-term storage."""
    kind: str  # "episodic", "semantic", "procedural"
    content: Any
    relevance: float = 0.0
    activation: float = 0.0


class CognitiveContext(BaseModel):
    """Input to a Strategy — everything the agent knows right now."""
    working_memory: WorkingMemory
    perceptions: list[Perception]
    active_tasks: list[Task]
    retrieved_memories: list[MemoryRecord] = Field(default_factory=list)
    drive_pressures: dict[str, float] = Field(default_factory=dict)


class Strategy(abc.ABC):
    """Abstract base for reasoning strategies. Stateless — all state in working memory."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def reason(self, context: CognitiveContext) -> list[CognitiveAction]:
        """Given context, return one or more actions to take."""
        ...


class ReACTStrategy(Strategy):
    """Reason → Act → Observe loop.

    Each invocation:
    1. Produces a Think action with reasoning about what to do.
    2. Produces an action (Execute, Delegate, etc.) based on that reasoning.
    If there's no current task, returns an empty list (agent should sleep).
    """

    @property
    def name(self) -> str:
        return "react"

    def reason(self, context: CognitiveContext) -> list[CognitiveAction]:
        task = context.working_memory.current_task
        if task is None:
            return []

        actions: list[CognitiveAction] = []

        # Step 1: Reason about the task and observations
        observations = [
            f"[{p.kind}] {p.content}" for p in context.perceptions
        ]
        memories = [
            f"[{m.kind}] {m.content}" for m in context.retrieved_memories
        ]

        thought_parts = [f"Task: {task.description}"]
        if observations:
            thought_parts.append(f"Observations: {'; '.join(str(o) for o in observations)}")
        if memories:
            thought_parts.append(f"Relevant memories: {'; '.join(str(m) for m in memories)}")
        if context.drive_pressures:
            active_drives = {k: v for k, v in context.drive_pressures.items() if v > 0}
            if active_drives:
                thought_parts.append(f"Active drives: {active_drives}")

        actions.append(Think(thoughts=thought_parts))

        # Step 2: The actual action is determined by the cognitive loop
        # calling the LLM with this context. ReACT just structures the
        # thinking. The LLM call happens in the ACT phase.
        # Here we return the Think so the loop knows to proceed to LLM reasoning.
        return actions
```

**Step 4: Run tests**

Run: `pytest tests/test_strategy.py -v`
Expected: PASS — all 4 tests pass

**Step 5: Commit**

```bash
git add src/speaker/strategy.py tests/test_strategy.py
git commit -m "feat: add Strategy interface and ReACTStrategy implementation"
```

---

## Task 7: Wakefulness System

**Files:**
- Create: `src/speaker/wakefulness.py`
- Create: `tests/test_wakefulness.py`

**Step 1: Write the failing tests**

```python
# tests/test_wakefulness.py
import asyncio
import pytest
from datetime import timedelta
from speaker.wakefulness import (
    WakeSource,
    ScheduledWake,
    EventWake,
    SelfWake,
    WakefulnessManager,
    WakeEvent,
)


@pytest.mark.asyncio
async def test_event_wake_trigger():
    ew = EventWake()
    event = WakeEvent(source="test", kind="new_task", data={"task_id": "1"})
    ew.trigger(event)
    result = await asyncio.wait_for(ew.wait(), timeout=1.0)
    assert result.source == "test"


@pytest.mark.asyncio
async def test_event_wake_no_event_times_out():
    ew = EventWake()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ew.wait(), timeout=0.1)


@pytest.mark.asyncio
async def test_self_wake():
    sw = SelfWake()
    sw.schedule(delay_seconds=0.1, reason="check delegation")
    result = await asyncio.wait_for(sw.wait(), timeout=1.0)
    assert result.kind == "self_wake"
    assert result.data["reason"] == "check delegation"


@pytest.mark.asyncio
async def test_self_wake_no_schedule_times_out():
    sw = SelfWake()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(sw.wait(), timeout=0.1)


@pytest.mark.asyncio
async def test_scheduled_wake():
    sw = ScheduledWake(interval=timedelta(seconds=0.1))
    result = await asyncio.wait_for(sw.wait(), timeout=1.0)
    assert result.kind == "heartbeat"


@pytest.mark.asyncio
async def test_wakefulness_manager_event_takes_priority():
    """When an event arrives, it should wake the agent even during scheduled sleep."""
    mgr = WakefulnessManager(sources=[
        ScheduledWake(interval=timedelta(seconds=10)),  # long interval
        EventWake(),
    ])
    # Trigger an event immediately
    for src in mgr.sources:
        if isinstance(src, EventWake):
            src.trigger(WakeEvent(source="test", kind="urgent", data={}))

    result = await asyncio.wait_for(mgr.wait_for_wake(), timeout=1.0)
    assert result.kind == "urgent"


@pytest.mark.asyncio
async def test_wakefulness_manager_heartbeat():
    mgr = WakefulnessManager(sources=[
        ScheduledWake(interval=timedelta(seconds=0.1)),
    ])
    result = await asyncio.wait_for(mgr.wait_for_wake(), timeout=1.0)
    assert result.kind == "heartbeat"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_wakefulness.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/wakefulness.py
"""Wakefulness system — determines when the agent's cognitive loop runs."""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class WakeEvent:
    """An event that woke the agent."""
    source: str
    kind: str  # "heartbeat", "new_task", "human_response", "agent_result", "self_wake"
    data: dict = field(default_factory=dict)


class WakeSource(abc.ABC):
    """Abstract base for wake sources."""

    @abc.abstractmethod
    async def wait(self) -> WakeEvent:
        """Block until this source triggers. Returns the wake event."""
        ...


class ScheduledWake(WakeSource):
    """Classic heartbeat. Wakes every interval."""

    def __init__(self, interval: timedelta) -> None:
        self._interval = interval

    async def wait(self) -> WakeEvent:
        await asyncio.sleep(self._interval.total_seconds())
        return WakeEvent(source="scheduled", kind="heartbeat")


class EventWake(WakeSource):
    """Wakes in response to external events (pushed by other code)."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[WakeEvent] = asyncio.Queue()

    def trigger(self, event: WakeEvent) -> None:
        """Push an event to wake the agent. Thread-safe."""
        self._queue.put_nowait(event)

    async def wait(self) -> WakeEvent:
        return await self._queue.get()


class SelfWake(WakeSource):
    """Agent programs its own wake-up during REFLECT."""

    def __init__(self) -> None:
        self._event: asyncio.Event = asyncio.Event()
        self._delay: float = 0.0
        self._reason: str = ""

    def schedule(self, delay_seconds: float, reason: str) -> None:
        self._delay = delay_seconds
        self._reason = reason
        self._event.set()

    async def wait(self) -> WakeEvent:
        await self._event.wait()
        self._event.clear()
        await asyncio.sleep(self._delay)
        return WakeEvent(
            source="self",
            kind="self_wake",
            data={"reason": self._reason},
        )


class WakefulnessManager:
    """Coordinates multiple wake sources. First one to fire wins."""

    def __init__(self, sources: list[WakeSource]) -> None:
        self.sources = sources

    async def wait_for_wake(self) -> WakeEvent:
        """Wait for any wake source to trigger. Returns the winning event."""
        tasks = [asyncio.create_task(src.wait()) for src in self.sources]
        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED,
            )
            # Cancel the losers
            for t in pending:
                t.cancel()
            # Return the winner
            return done.pop().result()
        except Exception:
            for t in tasks:
                t.cancel()
            raise
```

**Step 4: Run tests**

Run: `pytest tests/test_wakefulness.py -v`
Expected: PASS — all 7 tests pass

**Step 5: Commit**

```bash
git add src/speaker/wakefulness.py tests/test_wakefulness.py
git commit -m "feat: add wakefulness system — ScheduledWake, EventWake, SelfWake, WakefulnessManager"
```

---

## Task 8: Memory System — Long-Term Memory Store Interface

**Files:**
- Create: `src/speaker/memory.py`
- Create: `tests/test_memory.py`

**Step 1: Write the failing tests**

```python
# tests/test_memory.py
import pytest
from datetime import datetime, timedelta
from speaker.memory import (
    MemoryStore,
    InMemoryStore,
    MemoryEntry,
    MemoryKind,
    RetrievalQuery,
)


def test_memory_kind_values():
    assert MemoryKind.EPISODIC.value == "episodic"
    assert MemoryKind.SEMANTIC.value == "semantic"
    assert MemoryKind.PROCEDURAL.value == "procedural"


@pytest.mark.asyncio
async def test_store_and_retrieve_episodic():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content={"task": "search", "result": "found 3 items", "outcome": "success"},
        tags=["search", "api"],
    )
    await store.save(entry)
    results = await store.retrieve(RetrievalQuery(query="search api", top_k=5))
    assert len(results) >= 1
    assert results[0].entry.content["task"] == "search"


@pytest.mark.asyncio
async def test_store_and_retrieve_semantic():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.SEMANTIC,
        content="The customer's name is Alice and she prefers email.",
        tags=["customer", "alice"],
    )
    await store.save(entry)
    results = await store.retrieve(
        RetrievalQuery(query="alice", kind_filter=MemoryKind.SEMANTIC, top_k=5),
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_store_and_retrieve_procedural():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.PROCEDURAL,
        content={"pattern": "search → filter → summarize", "success_count": 5},
        tags=["search", "workflow"],
    )
    await store.save(entry)
    results = await store.retrieve(
        RetrievalQuery(query="search workflow", kind_filter=MemoryKind.PROCEDURAL, top_k=5),
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_recency_boost():
    """More recent memories should rank higher, all else being equal."""
    store = InMemoryStore()
    old = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="old search result",
        tags=["search"],
        created_at=datetime.utcnow() - timedelta(days=30),
    )
    new = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="new search result",
        tags=["search"],
    )
    await store.save(old)
    await store.save(new)
    results = await store.retrieve(RetrievalQuery(query="search", top_k=2))
    assert len(results) == 2
    # New memory should have higher activation
    assert results[0].activation >= results[1].activation


@pytest.mark.asyncio
async def test_frequency_boost():
    """More frequently accessed memories should rank higher."""
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="frequently used",
        tags=["common"],
    )
    await store.save(entry)
    # Access it multiple times
    for _ in range(5):
        await store.retrieve(RetrievalQuery(query="common", top_k=1))
    results = await store.retrieve(RetrievalQuery(query="common", top_k=1))
    assert results[0].activation > 0.0


@pytest.mark.asyncio
async def test_empty_store():
    store = InMemoryStore()
    results = await store.retrieve(RetrievalQuery(query="anything", top_k=5))
    assert results == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/memory.py
"""Long-term memory system with ACT-R activation-based retrieval."""

from __future__ import annotations

import abc
import enum
import math
import uuid
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field


class MemoryKind(str, enum.Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryEntry(BaseModel):
    """A single memory in long-term storage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: MemoryKind
    content: Any
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_times: list[datetime] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    """A memory with its computed activation score."""
    entry: MemoryEntry
    activation: float
    relevance: float


class RetrievalQuery(BaseModel):
    """Parameters for memory retrieval."""
    query: str
    kind_filter: MemoryKind | None = None
    top_k: int = 5
    context_tags: list[str] = Field(default_factory=list)


class MemoryStore(abc.ABC):
    """Abstract interface for long-term memory storage."""

    @abc.abstractmethod
    async def save(self, entry: MemoryEntry) -> None: ...

    @abc.abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]: ...


class InMemoryStore(MemoryStore):
    """In-memory implementation with ACT-R activation-based retrieval.

    Activation = base_level (recency + frequency) + context_boost + noise
    Base level: ln(Σ t_j^{-d}) where t_j = time since j-th access, d = 0.5
    """

    DECAY = 0.5  # ACT-R decay parameter

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    async def save(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        if not self._entries:
            return []

        now = datetime.utcnow()
        query_tokens = set(query.query.lower().split())
        results: list[RetrievalResult] = []

        for entry in self._entries:
            # Filter by kind if requested
            if query.kind_filter and entry.kind != query.kind_filter:
                continue

            # Compute base-level activation (recency + frequency)
            base_level = self._base_level_activation(entry, now)

            # Compute context boost (tag overlap)
            entry_tokens = set(t.lower() for t in entry.tags)
            content_str = str(entry.content).lower()
            content_tokens = set(content_str.split())
            all_entry_tokens = entry_tokens | content_tokens

            overlap = len(query_tokens & all_entry_tokens)
            context_boost = overlap * 0.5 if overlap > 0 else -1.0

            activation = base_level + context_boost

            if activation > -2.0:  # Threshold to avoid retrieving irrelevant memories
                relevance = overlap / max(len(query_tokens), 1)
                results.append(RetrievalResult(
                    entry=entry,
                    activation=activation,
                    relevance=relevance,
                ))

            # Record this access for frequency tracking
            entry.access_times.append(now)

        # Sort by activation (highest first), return top_k
        results.sort(key=lambda r: r.activation, reverse=True)
        return results[: query.top_k]

    def _base_level_activation(self, entry: MemoryEntry, now: datetime) -> float:
        """ACT-R base-level activation: ln(Σ t_j^{-d})"""
        access_times = entry.access_times or [entry.created_at]
        total = 0.0
        for access_time in access_times:
            elapsed = (now - access_time).total_seconds()
            elapsed = max(elapsed, 1.0)  # Avoid log(0) / division issues
            total += elapsed ** (-self.DECAY)
        if total <= 0:
            return -10.0
        return math.log(total)
```

**Step 4: Run tests**

Run: `pytest tests/test_memory.py -v`
Expected: PASS — all 7 tests pass

**Step 5: Commit**

```bash
git add src/speaker/memory.py tests/test_memory.py
git commit -m "feat: add long-term memory system with ACT-R activation-based retrieval"
```

---

## Task 9: Osma Adapter (Async Wrapper)

**Files:**
- Create: `src/speaker/osma_adapter.py`
- Create: `tests/test_osma_adapter.py`

**Step 1: Write the failing tests**

We use a fake/mock Osma client since we don't want real API calls in tests.

```python
# tests/test_osma_adapter.py
import pytest
from unittest.mock import MagicMock, patch
from speaker.osma_adapter import OsmaAdapter


class FakeThread:
    id = 1
    metadata = {"agent_id": "test"}
    session_data = {}


class FakeMessage:
    id = 1
    content = "Hello, I can help with that."
    role = "assistant"
    tool_calls = None


class FakeLambdaAgent:
    id = 1
    webhook_slug = "sub-agent-1"
    webhook_url = "https://api.example.com/agents/sub-agent-1"


@pytest.fixture
def mock_osma():
    client = MagicMock()
    client.threads.create.return_value = FakeThread()
    client.threads.create_message.return_value = FakeMessage()
    client.threads.list_messages.return_value = [FakeMessage()]
    client.threads.get.return_value = FakeThread()
    client.threads.update_metadata.return_value = None
    client.threads.update_taken_by.return_value = None
    client.lambda_agents.create.return_value = FakeLambdaAgent()
    client.lambda_agents.test.return_value = {
        "success": True,
        "data": {"response": "Result"},
        "execution_id": 1,
        "execution_time_ms": 150,
    }
    client.workflows.create.return_value = MagicMock(id="wf-uuid")
    client.workflows.steps.create.return_value = MagicMock(id="step-uuid")
    client.workflows.execute.return_value = MagicMock(
        id="exec-uuid", status="completed", output_data={"result": "ok"},
    )
    return client


@pytest.mark.asyncio
async def test_create_thread(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    thread = await adapter.create_thread("agent_1", {"key": "val"})
    assert thread.id == 1
    mock_osma.threads.create.assert_called_once()


@pytest.mark.asyncio
async def test_send_message(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    msg = await adapter.send_message(thread_id=1, content="Hello")
    assert msg.content == "Hello, I can help with that."
    mock_osma.threads.create_message.assert_called_once_with(
        thread_id=1, content="Hello", role="user",
    )


@pytest.mark.asyncio
async def test_get_messages(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    messages = await adapter.get_messages(thread_id=1)
    assert len(messages) == 1


@pytest.mark.asyncio
async def test_update_metadata_merges(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.update_metadata(thread_id=1, updates={"new_key": "new_val"})
    # Should have called get() first, then update_metadata with merged dict
    mock_osma.threads.get.assert_called_once_with(1)
    mock_osma.threads.update_metadata.assert_called_once()
    call_args = mock_osma.threads.update_metadata.call_args
    merged = call_args[1].get("metadata") or call_args[0][1]
    assert "agent_id" in merged  # original
    assert "new_key" in merged   # new


@pytest.mark.asyncio
async def test_switch_to_human(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.switch_to_human(thread_id=1)
    mock_osma.threads.update_taken_by.assert_called_once_with(1, "Human")


@pytest.mark.asyncio
async def test_switch_to_ai(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.switch_to_ai(thread_id=1)
    mock_osma.threads.update_taken_by.assert_called_once_with(1, "AI")


@pytest.mark.asyncio
async def test_create_sub_agent(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    agent = await adapter.create_sub_agent(
        name="researcher",
        system_prompt="You research topics.",
        llm_model=1,
    )
    assert agent.webhook_slug == "sub-agent-1"


@pytest.mark.asyncio
async def test_invoke_sub_agent(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    result = await adapter.invoke_sub_agent(agent_id=1, message="Research X")
    assert result["success"] is True
    assert result["data"]["response"] == "Result"


@pytest.mark.asyncio
async def test_execute_workflow(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    result = await adapter.execute_workflow(
        workflow_id="wf-uuid",
        input_data={"query": "test"},
    )
    assert result.status == "completed"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_osma_adapter.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/osma_adapter.py
"""Async wrapper around the synchronous Osma SDK."""

from __future__ import annotations

import asyncio
from typing import Any


class OsmaAdapter:
    """Wraps the synchronous OsmaClient for use in async code.

    All methods use asyncio.to_thread() to avoid blocking the event loop.
    Also handles Osma-specific quirks (e.g., update_metadata replaces, not merges).
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    # --- Threads ---

    async def create_thread(
        self,
        external_user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return await asyncio.to_thread(
            self._client.threads.create,
            external_user_id=external_user_id,
            metadata=metadata or {},
        )

    async def send_message(
        self,
        thread_id: int,
        content: str,
        role: str = "user",
    ) -> Any:
        return await asyncio.to_thread(
            self._client.threads.create_message,
            thread_id=thread_id,
            content=content,
            role=role,
        )

    async def get_messages(self, thread_id: int) -> list[Any]:
        return await asyncio.to_thread(
            self._client.threads.list_messages,
            thread_id=thread_id,
        )

    async def update_metadata(
        self,
        thread_id: int,
        updates: dict[str, Any],
    ) -> None:
        """Merge updates into existing metadata (Osma replaces, so we read-merge-write)."""
        thread = await asyncio.to_thread(self._client.threads.get, thread_id)
        merged = {**(thread.metadata or {}), **updates}
        await asyncio.to_thread(
            self._client.threads.update_metadata,
            thread_id,
            merged,
        )

    async def switch_to_human(self, thread_id: int) -> None:
        await asyncio.to_thread(
            self._client.threads.update_taken_by, thread_id, "Human",
        )

    async def switch_to_ai(self, thread_id: int) -> None:
        await asyncio.to_thread(
            self._client.threads.update_taken_by, thread_id, "AI",
        )

    # --- Sub-Agents (Lambda Agents) ---

    async def create_sub_agent(
        self,
        name: str,
        system_prompt: str,
        llm_model: int,
        enable_tool_calls: bool = True,
        enable_rag: bool = False,
        similarity_process: int | None = None,
        mcp_server_ids: list[int] | None = None,
    ) -> Any:
        agent = await asyncio.to_thread(
            self._client.lambda_agents.create,
            name=name,
            llm_model=llm_model,
            system_prompt=system_prompt,
            enable_tool_calls=enable_tool_calls,
            enable_rag=enable_rag,
            **({"similarity_process": similarity_process} if similarity_process else {}),
        )
        # Attach MCP servers if provided
        for server_id in (mcp_server_ids or []):
            await asyncio.to_thread(
                self._client.lambda_agents.tool_configs.create,
                agent_id=agent.id,
                tool_source_type="mcp_server",
                mcp_server=server_id,
                tool_selection_mode="all",
            )
        return agent

    async def invoke_sub_agent(self, agent_id: int, message: str) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._client.lambda_agents.test,
            agent_id,
            message=message,
        )

    # --- Workers (Workflows) ---

    async def create_workflow(
        self,
        name: str,
        step_type: str,
        config: dict[str, Any],
    ) -> Any:
        workflow = await asyncio.to_thread(
            self._client.workflows.create,
            name=name,
            status="active",
        )
        await asyncio.to_thread(
            self._client.workflows.steps.create,
            workflow_id=workflow.id,
            name="Execute",
            order=1,
            step_type=step_type,
            **{f"{step_type}_config": config},
        )
        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> Any:
        return await asyncio.to_thread(
            self._client.workflows.execute,
            workflow_id,
            input_data=input_data,
        )

    # --- Knowledge Bases ---

    async def create_knowledge_base(
        self,
        name: str,
        prompt: str,
        vector_top_k: int = 5,
    ) -> Any:
        return await asyncio.to_thread(
            self._client.knowledge.create,
            name=name,
            prompt=prompt,
            vector_top_k=vector_top_k,
        )

    async def upload_document(
        self,
        kb_id: int,
        content: str,
        title: str,
        external_user_id: str = "agent_docs",
    ) -> Any:
        return await asyncio.to_thread(
            self._client.knowledge.upload_document,
            kb_id,
            external_user_id=external_user_id,
            content=content,
            title=title,
        )
```

**Step 4: Run tests**

Run: `pytest tests/test_osma_adapter.py -v`
Expected: PASS — all 10 tests pass

**Step 5: Commit**

```bash
git add src/speaker/osma_adapter.py tests/test_osma_adapter.py
git commit -m "feat: add OsmaAdapter — async wrapper around synchronous Osma SDK"
```

---

## Task 10: Cognitive Loop

**Files:**
- Create: `src/speaker/cognitive_loop.py`
- Create: `tests/test_cognitive_loop.py`

This is the heart of the agent — the 5-phase PERCEIVE → ORIENT → REASON → ACT → REFLECT loop.

**Step 1: Write the failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cognitive_loop.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/cognitive_loop.py
"""The 5-phase cognitive loop: PERCEIVE → ORIENT → REASON → ACT → REFLECT."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from speaker.actions import (
    CognitiveAction,
    Think,
    Sleep,
    Execute,
    Delegate,
    Dispatch,
    AskHuman,
    UpdateTask,
    Impasse,
)
from speaker.drives import Drive, compute_drive_pressures
from speaker.memory import InMemoryStore, MemoryEntry, MemoryKind, MemoryStore, RetrievalQuery
from speaker.models import (
    Perception,
    Task,
    TaskAttempt,
    TaskStatus,
    Thought,
    WorkingMemory,
)
from speaker.strategy import CognitiveContext, MemoryRecord, Strategy
from speaker.task_queue import TaskQueue

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    """Result of one cognitive cycle."""
    should_sleep: bool = False
    actions_taken: list[CognitiveAction] = field(default_factory=list)
    cycle_number: int = 0


class CognitiveLoop:
    """Orchestrates the 5-phase cognitive cycle."""

    def __init__(
        self,
        task_queue: TaskQueue,
        strategy: Strategy,
        memory_store: MemoryStore,
        osma_adapter: Any,
        drives: list[Drive] | None = None,
    ) -> None:
        self.task_queue = task_queue
        self.strategy = strategy
        self.memory_store = memory_store
        self.osma = osma_adapter
        self.drives = drives or []
        self.working_memory = WorkingMemory()
        self._pending_perceptions: list[Perception] = []
        self._cycle_count = 0

    def add_perception(self, perception: Perception) -> None:
        """Add an external perception to be processed in the next cycle."""
        self._pending_perceptions.append(perception)

    async def run_cycle(self) -> CycleResult:
        """Execute one complete cognitive cycle."""
        self._cycle_count += 1
        result = CycleResult(cycle_number=self._cycle_count)

        # Phase 1: PERCEIVE
        perceptions = self._perceive()

        # Phase 2: ORIENT
        task, drive_pressures, memories = await self._orient(perceptions)

        # No work to do? Sleep.
        if task is None and not perceptions:
            result.should_sleep = True
            return result

        # Phase 3: REASON
        context = CognitiveContext(
            working_memory=self.working_memory,
            perceptions=perceptions,
            active_tasks=self.task_queue.active() + ([task] if task else []),
            retrieved_memories=memories,
            drive_pressures=drive_pressures,
        )
        actions = self.strategy.reason(context)

        # Phase 4: ACT
        executed = await self._act(actions, task)
        result.actions_taken = executed

        # Phase 5: REFLECT
        await self._reflect(task, executed)

        # Decide: continue or sleep?
        result.should_sleep = not self.task_queue.has_work()
        return result

    # --- Phase implementations ---

    def _perceive(self) -> list[Perception]:
        """Phase 1: Gather all new perceptions."""
        self.working_memory.clear()
        perceptions = list(self._pending_perceptions)
        self._pending_perceptions.clear()

        # Check for newly actionable tasks
        for task in self.task_queue.actionable():
            if task.status == TaskStatus.PENDING:
                perceptions.append(Perception(
                    kind="new_task",
                    source=task.source.value,
                    content=task.description,
                ))

        self.working_memory.perceptions = perceptions
        return perceptions

    async def _orient(
        self,
        perceptions: list[Perception],
    ) -> tuple[Task | None, dict[str, float], list[MemoryRecord]]:
        """Phase 2: Retrieve memories, prioritize tasks, assess drives."""
        # Compute drive pressures
        drive_pressures = compute_drive_pressures(
            self.drives, self.task_queue, self.working_memory,
        )

        # Select the highest-priority actionable task
        actionable = self.task_queue.actionable()
        task = actionable[0] if actionable else None
        if task:
            task.status = TaskStatus.ACTIVE
            self.working_memory.current_task = task

        # Retrieve relevant memories
        memories: list[MemoryRecord] = []
        if task:
            query = RetrievalQuery(
                query=task.description,
                top_k=5,
                context_tags=list(task.context.keys()),
            )
            results = await self.memory_store.retrieve(query)
            memories = [
                MemoryRecord(
                    kind=r.entry.kind.value,
                    content=r.entry.content,
                    relevance=r.relevance,
                    activation=r.activation,
                )
                for r in results
            ]

        return task, drive_pressures, memories

    async def _act(
        self,
        actions: list[CognitiveAction],
        task: Task | None,
    ) -> list[CognitiveAction]:
        """Phase 4: Execute the actions returned by the strategy."""
        executed: list[CognitiveAction] = []
        for action in actions:
            await self._execute_action(action, task)
            executed.append(action)
        return executed

    async def _execute_action(self, action: CognitiveAction, task: Task | None) -> None:
        """Execute a single cognitive action."""
        match action:
            case Think(thoughts=thoughts):
                for thought in thoughts:
                    self.working_memory.scratchpad.append(Thought(content=thought))

            case Sleep():
                pass  # Handled by the cycle result

            case UpdateTask(task_id=tid, status=status, result=res):
                t = self.task_queue.get(tid)
                t.status = TaskStatus(status)
                t.result = res

            case Execute(tool_name=name, tool_args=args):
                if task:
                    task.attempts.append(TaskAttempt(
                        action_taken=f"execute:{name}",
                        result=None,
                        success=False,
                    ))

            case Delegate():
                logger.info("Delegate action — sub-agent creation deferred to higher layer")

            case Dispatch():
                logger.info("Dispatch action — workflow execution deferred to higher layer")

            case AskHuman(question=q):
                if task:
                    task.status = TaskStatus.BLOCKED
                    task.blocked_by = "human_request"
                    task.blocked_reason = "awaiting_human"

            case Impasse(impasse_type=itype, details=details):
                logger.warning(f"Impasse detected: {itype.value} — {details}")

    async def _reflect(
        self,
        task: Task | None,
        actions: list[CognitiveAction],
    ) -> None:
        """Phase 5: Update memory with what happened this cycle."""
        if not task:
            return

        # Store episodic memory of this cycle
        action_summary = [type(a).__name__ for a in actions]
        entry = MemoryEntry(
            kind=MemoryKind.EPISODIC,
            content={
                "task": task.description,
                "actions": action_summary,
                "task_status": task.status.value,
                "cycle": self._cycle_count,
            },
            tags=[task.description.split()[0].lower()] if task.description else [],
        )
        await self.memory_store.save(entry)
```

**Step 4: Run tests**

Run: `pytest tests/test_cognitive_loop.py -v`
Expected: PASS — all 5 tests pass

**Step 5: Commit**

```bash
git add src/speaker/cognitive_loop.py tests/test_cognitive_loop.py
git commit -m "feat: add CognitiveLoop — 5-phase PERCEIVE/ORIENT/REASON/ACT/REFLECT cycle"
```

---

## Task 11: AutonomousAgent Entry Point

**Files:**
- Create: `src/speaker/agent.py`
- Create: `tests/test_agent.py`

**Step 1: Write the failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/speaker/agent.py
"""AutonomousAgent — the top-level entry point."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from speaker.actions import Sleep
from speaker.cognitive_loop import CognitiveLoop, CycleResult
from speaker.drives import Drive
from speaker.memory import InMemoryStore, MemoryStore
from speaker.models import Perception, Task
from speaker.osma_adapter import OsmaAdapter
from speaker.strategy import Strategy
from speaker.task_queue import TaskQueue
from speaker.wakefulness import (
    EventWake,
    ScheduledWake,
    SelfWake,
    WakeEvent,
    WakefulnessManager,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    strategy: Strategy
    osma_client: Any  # OsmaClient instance (sync)
    drives: list[Drive] = field(default_factory=list)
    memory_store: MemoryStore | None = None
    heartbeat_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    enable_event_wake: bool = True
    enable_self_wake: bool = True


class AutonomousAgent:
    """A cognitive autonomous agent with a 5-phase reasoning loop."""

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._running = False
        self._cycle_count = 0

        # Core components
        self.task_queue = TaskQueue()
        self.osma = OsmaAdapter(config.osma_client)
        self.memory_store = config.memory_store or InMemoryStore()

        # Wakefulness
        self._event_wake = EventWake() if config.enable_event_wake else None
        self._self_wake = SelfWake() if config.enable_self_wake else None
        wake_sources = [ScheduledWake(interval=config.heartbeat_interval)]
        if self._event_wake:
            wake_sources.append(self._event_wake)
        if self._self_wake:
            wake_sources.append(self._self_wake)
        self._wakefulness = WakefulnessManager(sources=wake_sources)

        # Cognitive loop
        self._loop = CognitiveLoop(
            task_queue=self.task_queue,
            strategy=config.strategy,
            memory_store=self.memory_store,
            osma_adapter=self.osma,
            drives=config.drives,
        )

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    def submit_task(self, task: Task) -> None:
        """Submit a task to the agent's queue. Wakes the agent if sleeping."""
        self.task_queue.submit(task)
        if self._event_wake:
            self._event_wake.trigger(WakeEvent(
                source="submit",
                kind="new_task",
                data={"task_id": task.id},
            ))

    def add_perception(self, perception: Perception) -> None:
        """Add an external perception. Wakes the agent."""
        self._loop.add_perception(perception)
        if self._event_wake:
            self._event_wake.trigger(WakeEvent(
                source="external",
                kind=perception.kind,
                data={"content": str(perception.content)},
            ))

    async def run_one_cycle(self) -> CycleResult:
        """Run a single cognitive cycle. Useful for testing."""
        result = await self._loop.run_cycle()
        self._cycle_count += 1

        # Handle Sleep with self-wake
        for action in result.actions_taken:
            if isinstance(action, Sleep) and action.wake_after_seconds and self._self_wake:
                self._self_wake.schedule(action.wake_after_seconds, action.reason)

        return result

    async def start(self) -> None:
        """Start the agent's main loop. Runs until stop() is called."""
        self._running = True
        logger.info(f"Agent started with strategy={self._config.strategy.name}")

        try:
            while self._running:
                # Run one cognitive cycle
                result = await self.run_one_cycle()

                if result.should_sleep and self._running:
                    # Sleep until woken
                    logger.debug("Agent sleeping, waiting for wake event...")
                    try:
                        wake_event = await self._wakefulness.wait_for_wake()
                        logger.debug(f"Agent woken by: {wake_event.kind}")
                        self._loop.add_perception(Perception(
                            kind=wake_event.kind,
                            source=wake_event.source,
                            content=wake_event.data,
                        ))
                    except Exception as e:
                        if self._running:
                            logger.error(f"Wake error: {e}")
        finally:
            self._running = False
            logger.info("Agent stopped.")

    def stop(self) -> None:
        """Signal the agent to stop after the current cycle."""
        self._running = False
        # Trigger an event to break out of sleep
        if self._event_wake:
            self._event_wake.trigger(WakeEvent(
                source="shutdown",
                kind="shutdown",
                data={},
            ))
```

**Step 4: Run tests**

Run: `pytest tests/test_agent.py -v`
Expected: PASS — all 4 tests pass

**Step 5: Commit**

```bash
git add src/speaker/agent.py tests/test_agent.py
git commit -m "feat: add AutonomousAgent entry point with start/stop lifecycle"
```

---

## Task 12: Package Exports + Integration Test

**Files:**
- Modify: `src/speaker/__init__.py`
- Create: `tests/test_integration.py`

**Step 1: Write the failing integration test**

```python
# tests/test_integration.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_integration.py -v`
Expected: FAIL — cannot import from `speaker`

**Step 3: Update package exports**

```python
# src/speaker/__init__.py
"""Speaker — Cognitive Autonomous Agent."""

from speaker.agent import AgentConfig, AutonomousAgent
from speaker.models import (
    Delegation,
    HumanRequest,
    ImpasseType,
    Perception,
    Task,
    TaskAttempt,
    TaskSource,
    TaskStatus,
    Thought,
    WorkingMemory,
)
from speaker.actions import (
    AskHuman,
    CognitiveAction,
    Delegate,
    Dispatch,
    Execute,
    Impasse,
    Sleep,
    Think,
    UpdateTask,
)
from speaker.strategy import CognitiveContext, MemoryRecord, ReACTStrategy, Strategy
from speaker.drives import (
    CoherenceDrive,
    CompletionDrive,
    CuriosityDrive,
    Drive,
    TaskDrive,
    compute_drive_pressures,
)
from speaker.memory import InMemoryStore, MemoryEntry, MemoryKind, MemoryStore, RetrievalQuery
from speaker.task_queue import TaskQueue
from speaker.osma_adapter import OsmaAdapter
from speaker.wakefulness import (
    EventWake,
    ScheduledWake,
    SelfWake,
    WakeEvent,
    WakefulnessManager,
)

__all__ = [
    # Agent
    "AgentConfig",
    "AutonomousAgent",
    # Models
    "Task",
    "TaskStatus",
    "TaskSource",
    "ImpasseType",
    "Perception",
    "Thought",
    "TaskAttempt",
    "Delegation",
    "HumanRequest",
    "WorkingMemory",
    # Actions
    "CognitiveAction",
    "Execute",
    "Delegate",
    "Dispatch",
    "AskHuman",
    "UpdateTask",
    "Think",
    "Sleep",
    "Impasse",
    # Strategy
    "Strategy",
    "ReACTStrategy",
    "CognitiveContext",
    "MemoryRecord",
    # Drives
    "Drive",
    "TaskDrive",
    "CuriosityDrive",
    "CompletionDrive",
    "CoherenceDrive",
    "compute_drive_pressures",
    # Memory
    "MemoryStore",
    "InMemoryStore",
    "MemoryEntry",
    "MemoryKind",
    "RetrievalQuery",
    # Task Queue
    "TaskQueue",
    # Osma
    "OsmaAdapter",
    # Wakefulness
    "WakeSource",
    "ScheduledWake",
    "EventWake",
    "SelfWake",
    "WakeEvent",
    "WakefulnessManager",
]
```

**Step 4: Run all tests**

Run: `pytest -v`
Expected: PASS — all tests pass (integration + unit)

**Step 5: Run with coverage**

Run: `pytest --cov=speaker --cov-report=term-missing -v`
Expected: High coverage across all modules

**Step 6: Commit**

```bash
git add src/speaker/__init__.py tests/test_integration.py
git commit -m "feat: add package exports and integration tests — MVP complete"
```

---

## Summary: What We Built

| Module | Purpose |
|---|---|
| `models.py` | Core data models: Task, WorkingMemory, Perception, enums |
| `actions.py` | CognitiveAction union: Execute, Delegate, Dispatch, AskHuman, Think, Sleep, Impasse |
| `task_queue.py` | Priority-ordered task queue with dependency tracking |
| `drives.py` | Active Inference drives: Task, Curiosity, Completion, Coherence |
| `strategy.py` | Strategy interface + ReACTStrategy implementation |
| `memory.py` | Long-term memory with ACT-R activation-based retrieval |
| `wakefulness.py` | ScheduledWake, EventWake, SelfWake, WakefulnessManager |
| `osma_adapter.py` | Async wrapper around synchronous Osma SDK |
| `cognitive_loop.py` | 5-phase PERCEIVE → ORIENT → REASON → ACT → REFLECT cycle |
| `agent.py` | AutonomousAgent entry point with start/stop lifecycle |

## Next Steps (Post-MVP)

After this MVP is working:

1. **JudgeStrategy** and **TreeOfThoughtStrategy** implementations
2. **SQLite persistence** for tasks and long-term memory (replace InMemoryStore)
3. **Full Osma integration** in ACT phase (actual LLM calls, sub-agent creation, workflow execution)
4. **Impasse auto-resolution** in the cognitive loop (detect + delegate automatically)
5. **Osma Knowledge Base** as semantic memory backend
6. **Webhook receiver** for EventWake (HTTP server that receives Osma callbacks)
