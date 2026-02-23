# tests/test_task_queue.py
import pytest
from speaker.task_queue import TaskQueue
from speaker.models import Task, TaskStatus, TaskSource


def test_submit_task():
    q = TaskQueue()
    task = Task(description="Do X")
    q.submit(task)
    assert len(q) == 1
    assert q.get(task.id) is task


def test_submit_duplicate_raises():
    q = TaskQueue()
    task = Task(description="Do X")
    q.submit(task)
    with pytest.raises(ValueError, match="already exists"):
        q.submit(task)


def test_pending_tasks():
    q = TaskQueue()
    t1 = Task(description="A", priority=0.3)
    t2 = Task(description="B", priority=0.9)
    t3 = Task(description="C", status=TaskStatus.COMPLETED)
    q.submit(t1)
    q.submit(t2)
    q.submit(t3)
    pending = q.pending()
    assert len(pending) == 2
    assert pending[0].id == t2.id  # higher priority first


def test_active_tasks():
    q = TaskQueue()
    t1 = Task(description="A", status=TaskStatus.ACTIVE)
    t2 = Task(description="B", status=TaskStatus.PENDING)
    q.submit(t1)
    q.submit(t2)
    assert len(q.active()) == 1
    assert q.active()[0].id == t1.id


def test_blocked_tasks():
    q = TaskQueue()
    t = Task(description="A", status=TaskStatus.BLOCKED, blocked_by="human_1")
    q.submit(t)
    assert len(q.blocked()) == 1


def test_actionable_excludes_blocked_dependencies():
    q = TaskQueue()
    t1 = Task(description="Dep", status=TaskStatus.PENDING)
    t2 = Task(description="Main", status=TaskStatus.PENDING, depends_on=[t1.id])
    q.submit(t1)
    q.submit(t2)
    actionable = q.actionable()
    assert len(actionable) == 1
    assert actionable[0].id == t1.id  # t2 is blocked by dependency


def test_actionable_includes_after_dependency_completed():
    q = TaskQueue()
    t1 = Task(description="Dep", status=TaskStatus.COMPLETED)
    t2 = Task(description="Main", status=TaskStatus.PENDING, depends_on=[t1.id])
    q.submit(t1)
    q.submit(t2)
    actionable = q.actionable()
    assert len(actionable) == 1
    assert actionable[0].id == t2.id


def test_all_tasks():
    q = TaskQueue()
    for i in range(5):
        q.submit(Task(description=f"Task {i}"))
    assert len(q.all()) == 5


def test_has_work():
    q = TaskQueue()
    assert not q.has_work()
    q.submit(Task(description="X"))
    assert q.has_work()


def test_has_work_false_when_all_done():
    q = TaskQueue()
    q.submit(Task(description="X", status=TaskStatus.COMPLETED))
    assert not q.has_work()
