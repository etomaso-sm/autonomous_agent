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
