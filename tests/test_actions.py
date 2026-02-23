# tests/test_actions.py
from speaker.actions import (
    CognitiveAction,
    Execute,
    Delegate,
    Dispatch,
    AskHuman,
    UpdateTask,
    Think,
    Sleep,
    Impasse,
)
from speaker.models import ImpasseType


def test_execute_action():
    action = Execute(tool_name="search", tool_args={"query": "test"})
    assert action.tool_name == "search"
    assert action.tool_args == {"query": "test"}


def test_delegate_action():
    action = Delegate(
        objective="Research topic X",
        system_prompt="You are a research specialist.",
        llm_model=1,
    )
    assert action.objective == "Research topic X"
    assert action.enable_tool_calls is True  # default


def test_dispatch_action():
    action = Dispatch(
        task_description="Call API",
        step_type="rest_api",
        config={"url": "https://example.com", "method": "GET"},
    )
    assert action.step_type == "rest_api"


def test_ask_human_action():
    action = AskHuman(question="What format?", context={"task": "report"})
    assert action.question == "What format?"


def test_update_task_action():
    action = UpdateTask(task_id="abc", status="completed", result={"answer": 42})
    assert action.task_id == "abc"
    assert action.result == {"answer": 42}


def test_think_action():
    action = Think(thoughts=["I should check the API first", "The data looks stale"])
    assert len(action.thoughts) == 2


def test_sleep_action():
    action = Sleep(reason="No active tasks")
    assert action.wake_after_seconds is None  # no self-wake by default


def test_sleep_with_self_wake():
    action = Sleep(reason="Delegated work", wake_after_seconds=300)
    assert action.wake_after_seconds == 300


def test_impasse_action():
    action = Impasse(
        impasse_type=ImpasseType.INFORMATION,
        details={"missing": "customer email"},
    )
    assert action.impasse_type == ImpasseType.INFORMATION


def test_cognitive_action_is_union():
    """All action types are valid CognitiveAction."""
    actions: list[CognitiveAction] = [
        Execute(tool_name="t", tool_args={}),
        Delegate(objective="o", system_prompt="s", llm_model=1),
        Dispatch(task_description="d", step_type="rest_api", config={}),
        AskHuman(question="q"),
        UpdateTask(task_id="id", status="completed"),
        Think(thoughts=["t"]),
        Sleep(reason="r"),
        Impasse(impasse_type=ImpasseType.RESOURCE, details={}),
    ]
    assert len(actions) == 8
