"""The 5-phase cognitive loop: PERCEIVE -> ORIENT -> REASON -> ACT -> REFLECT."""

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
