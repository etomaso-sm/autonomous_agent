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
