"""Async wrapper around the synchronous Osma SDK."""

from __future__ import annotations

import asyncio
from typing import Any


class OsmaAdapter:
    """Wraps the synchronous OsmaClient for use in async code.

    All methods use asyncio.to_thread() to avoid blocking the event loop.
    Also handles Osma-specific quirks (e.g., update_metadata replaces, not merges).
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._metadata_lock = asyncio.Lock()

    # --- Threads ---

    async def create_thread(
        self,
        external_user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return await asyncio.to_thread(
            self._client.threads.create,
            external_user_id=external_user_id,
            metadata=metadata or {},
        )

    async def send_message(
        self,
        thread_id: int,
        content: str,
        role: str = "user",
    ) -> Any:
        return await asyncio.to_thread(
            self._client.threads.create_message,
            thread_id=thread_id,
            content=content,
            role=role,
        )

    async def get_messages(self, thread_id: int) -> list[Any]:
        return await asyncio.to_thread(
            self._client.threads.list_messages,
            thread_id=thread_id,
        )

    async def update_metadata(
        self,
        thread_id: int,
        updates: dict[str, Any],
    ) -> None:
        """Merge updates into existing metadata (Osma replaces, so we read-merge-write)."""
        async with self._metadata_lock:
            thread = await asyncio.to_thread(self._client.threads.get, thread_id)
            merged = {**(thread.metadata or {}), **updates}
            await asyncio.to_thread(
                self._client.threads.update_metadata,
                thread_id,
                merged,
            )

    async def switch_to_human(self, thread_id: int) -> None:
        await asyncio.to_thread(
            self._client.threads.update_taken_by, thread_id, "Human",
        )

    async def switch_to_ai(self, thread_id: int) -> None:
        await asyncio.to_thread(
            self._client.threads.update_taken_by, thread_id, "AI",
        )

    # --- Sub-Agents (Lambda Agents) ---

    async def create_sub_agent(
        self,
        name: str,
        system_prompt: str,
        llm_model: int,
        enable_tool_calls: bool = True,
        enable_rag: bool = False,
        similarity_process: int | None = None,
        mcp_server_ids: list[int] | None = None,
    ) -> Any:
        agent = await asyncio.to_thread(
            self._client.lambda_agents.create,
            name=name,
            llm_model=llm_model,
            system_prompt=system_prompt,
            enable_tool_calls=enable_tool_calls,
            enable_rag=enable_rag,
            **({"similarity_process": similarity_process} if similarity_process else {}),
        )
        # Attach MCP servers if provided
        for server_id in (mcp_server_ids or []):
            await asyncio.to_thread(
                self._client.lambda_agents.tool_configs.create,
                agent_id=agent.id,
                tool_source_type="mcp_server",
                mcp_server=server_id,
                tool_selection_mode="all",
            )
        return agent

    async def invoke_sub_agent(self, agent_id: int, message: str) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._client.lambda_agents.test,
            agent_id,
            message=message,
        )

    # --- Workers (Workflows) ---

    async def create_workflow(
        self,
        name: str,
        step_type: str,
        config: dict[str, Any],
    ) -> Any:
        workflow = await asyncio.to_thread(
            self._client.workflows.create,
            name=name,
            status="active",
        )
        await asyncio.to_thread(
            self._client.workflows.steps.create,
            workflow_id=workflow.id,
            name="Execute",
            order=1,
            step_type=step_type,
            **{f"{step_type}_config": config},
        )
        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> Any:
        return await asyncio.to_thread(
            self._client.workflows.execute,
            workflow_id,
            input_data=input_data,
        )

    # --- Knowledge Bases ---

    async def create_knowledge_base(
        self,
        name: str,
        prompt: str,
        vector_top_k: int = 5,
    ) -> Any:
        return await asyncio.to_thread(
            self._client.knowledge.create,
            name=name,
            prompt=prompt,
            vector_top_k=vector_top_k,
        )

    async def upload_document(
        self,
        kb_id: int,
        content: str,
        title: str,
        external_user_id: str = "agent_docs",
    ) -> Any:
        return await asyncio.to_thread(
            self._client.knowledge.upload_document,
            kb_id,
            external_user_id=external_user_id,
            content=content,
            title=title,
        )
