"""Protocol-level test; runs once the MCP SDK is installed locally."""

import asyncio
import pytest

pytest.importorskip("mcp")
from mcp import Client
from app.mcp_server import mcp


def test_mcp_tool_is_discoverable_and_can_search():
    async def check():
        async with Client(mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {"search_runbooks", "create_ticket"} <= names
            response = await client.call_tool("search_runbooks", {"query": "OOMKilled memory"})
            assert not response.is_error
            assert response.structured_content is not None

    asyncio.run(check())
