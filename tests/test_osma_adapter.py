# tests/test_osma_adapter.py
import pytest
from unittest.mock import MagicMock, patch
from speaker.osma_adapter import OsmaAdapter


class FakeThread:
    id = 1
    metadata = {"agent_id": "test"}
    session_data = {}


class FakeMessage:
    id = 1
    content = "Hello, I can help with that."
    role = "assistant"
    tool_calls = None


class FakeLambdaAgent:
    id = 1
    webhook_slug = "sub-agent-1"
    webhook_url = "https://api.example.com/agents/sub-agent-1"


@pytest.fixture
def mock_osma():
    client = MagicMock()
    client.threads.create.return_value = FakeThread()
    client.threads.create_message.return_value = FakeMessage()
    client.threads.list_messages.return_value = [FakeMessage()]
    client.threads.get.return_value = FakeThread()
    client.threads.update_metadata.return_value = None
    client.threads.update_taken_by.return_value = None
    client.lambda_agents.create.return_value = FakeLambdaAgent()
    client.lambda_agents.test.return_value = {
        "success": True,
        "data": {"response": "Result"},
        "execution_id": 1,
        "execution_time_ms": 150,
    }
    client.workflows.create.return_value = MagicMock(id="wf-uuid")
    client.workflows.steps.create.return_value = MagicMock(id="step-uuid")
    client.workflows.execute.return_value = MagicMock(
        id="exec-uuid", status="completed", output_data={"result": "ok"},
    )
    return client


@pytest.mark.asyncio
async def test_create_thread(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    thread = await adapter.create_thread("agent_1", {"key": "val"})
    assert thread.id == 1
    mock_osma.threads.create.assert_called_once()


@pytest.mark.asyncio
async def test_send_message(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    msg = await adapter.send_message(thread_id=1, content="Hello")
    assert msg.content == "Hello, I can help with that."
    mock_osma.threads.create_message.assert_called_once_with(
        thread_id=1, content="Hello", role="user",
    )


@pytest.mark.asyncio
async def test_get_messages(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    messages = await adapter.get_messages(thread_id=1)
    assert len(messages) == 1


@pytest.mark.asyncio
async def test_update_metadata_merges(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.update_metadata(thread_id=1, updates={"new_key": "new_val"})
    # Should have called get() first, then update_metadata with merged dict
    mock_osma.threads.get.assert_called_once_with(1)
    mock_osma.threads.update_metadata.assert_called_once()
    call_args = mock_osma.threads.update_metadata.call_args
    merged = call_args[1].get("metadata") or call_args[0][1]
    assert "agent_id" in merged  # original
    assert "new_key" in merged   # new


@pytest.mark.asyncio
async def test_switch_to_human(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.switch_to_human(thread_id=1)
    mock_osma.threads.update_taken_by.assert_called_once_with(1, "Human")


@pytest.mark.asyncio
async def test_switch_to_ai(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    await adapter.switch_to_ai(thread_id=1)
    mock_osma.threads.update_taken_by.assert_called_once_with(1, "AI")


@pytest.mark.asyncio
async def test_create_sub_agent(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    agent = await adapter.create_sub_agent(
        name="researcher",
        system_prompt="You research topics.",
        llm_model=1,
    )
    assert agent.webhook_slug == "sub-agent-1"


@pytest.mark.asyncio
async def test_invoke_sub_agent(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    result = await adapter.invoke_sub_agent(agent_id=1, message="Research X")
    assert result["success"] is True
    assert result["data"]["response"] == "Result"


@pytest.mark.asyncio
async def test_execute_workflow(mock_osma):
    adapter = OsmaAdapter(mock_osma)
    result = await adapter.execute_workflow(
        workflow_id="wf-uuid",
        input_data={"query": "test"},
    )
    assert result.status == "completed"
