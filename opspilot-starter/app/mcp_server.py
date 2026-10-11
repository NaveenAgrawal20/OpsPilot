"""Real MCP v2 tool server, deliberately separate from the FastAPI process.

Start with: python -m app.mcp_server
Connect with MCP Inspector or the client at http://127.0.0.1:8001/mcp
"""

from mcp.server import MCPServer
from .knowledge import search_docs as local_search_docs
from .tickets import create_approved_ticket

mcp = MCPServer("OpsPilot Tools")


@mcp.tool()
def search_runbooks(query: str) -> list[dict]:
    """Retrieve relevant public IT runbook passages."""
    return local_search_docs(query)


@mcp.tool()
def create_ticket(draft_id: str) -> dict:
    """Create a ticket ONLY if its stored draft has already been approved."""
    return create_approved_ticket(draft_id)


if __name__ == "__main__":
    # Local-only demo; production deployment needs real authentication and audit.
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
