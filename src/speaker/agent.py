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
