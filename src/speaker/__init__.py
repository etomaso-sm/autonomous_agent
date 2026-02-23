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
    WakeSource,
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
