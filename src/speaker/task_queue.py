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
