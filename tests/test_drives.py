# tests/test_drives.py
from speaker.drives import (
    Drive,
    TaskDrive,
    CuriosityDrive,
    CompletionDrive,
    CoherenceDrive,
    compute_drive_pressures,
)
from speaker.task_queue import TaskQueue
from speaker.models import Task, TaskStatus, WorkingMemory


def test_task_drive_no_pending():
    q = TaskQueue()
    drive = TaskDrive()
    assert drive.pressure(q, WorkingMemory()) == 0.0


def test_task_drive_with_pending():
    q = TaskQueue()
    q.submit(Task(description="X"))
    drive = TaskDrive()
    assert drive.pressure(q, WorkingMemory()) > 0.0


def test_task_drive_scales_with_count():
    q = TaskQueue()
    for i in range(5):
        q.submit(Task(description=f"Task {i}"))
    drive = TaskDrive()
    p5 = drive.pressure(q, WorkingMemory())
    q2 = TaskQueue()
    q2.submit(Task(description="One"))
    p1 = drive.pressure(q2, WorkingMemory())
    assert p5 > p1


def test_completion_drive_no_blocked():
    q = TaskQueue()
    drive = CompletionDrive()
    assert drive.pressure(q, WorkingMemory()) == 0.0


def test_completion_drive_with_blocked():
    q = TaskQueue()
    q.submit(Task(description="X", status=TaskStatus.BLOCKED, blocked_by="h1"))
    drive = CompletionDrive()
    assert drive.pressure(q, WorkingMemory()) > 0.0


def test_curiosity_drive_no_gaps():
    q = TaskQueue()
    wm = WorkingMemory()
    drive = CuriosityDrive()
    assert drive.pressure(q, wm) == 0.0


def test_curiosity_drive_with_impasse_in_context():
    q = TaskQueue()
    wm = WorkingMemory(active_context={"information_gaps": ["missing customer email"]})
    drive = CuriosityDrive()
    assert drive.pressure(q, wm) > 0.0


def test_coherence_drive_no_contradictions():
    q = TaskQueue()
    wm = WorkingMemory()
    drive = CoherenceDrive()
    assert drive.pressure(q, wm) == 0.0


def test_compute_drive_pressures():
    q = TaskQueue()
    q.submit(Task(description="X"))
    wm = WorkingMemory()
    drives = [TaskDrive(), CuriosityDrive(), CompletionDrive(), CoherenceDrive()]
    pressures = compute_drive_pressures(drives, q, wm)
    assert "task" in pressures
    assert "curiosity" in pressures
    assert "completion" in pressures
    assert "coherence" in pressures
    assert pressures["task"] > 0.0
    assert pressures["curiosity"] == 0.0
