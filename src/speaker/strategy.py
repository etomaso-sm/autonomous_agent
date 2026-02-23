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
