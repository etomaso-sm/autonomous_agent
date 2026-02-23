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
