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
