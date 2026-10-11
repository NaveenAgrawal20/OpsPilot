"""Small real MCP client. Day 4: verify exact SDK return shape with Codex."""

import os
from mcp import Client


async def execute_ticket_tool(draft_id: str) -> str:
    url = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")
    async with Client(url) as client:
        result = await client.call_tool("create_ticket", arguments={"draft_id": draft_id})
        if result.is_error:
            raise RuntimeError(f"MCP tool failed: {result}")
        # Return the raw structured/text result; don't invent a ticket ID.
        return str(result.structured_content or result.content)
