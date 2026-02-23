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
