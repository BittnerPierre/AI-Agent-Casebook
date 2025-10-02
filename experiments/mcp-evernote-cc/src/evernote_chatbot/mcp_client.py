"""Proper MCP client using the standard MCP library."""

from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool


class ProperMCPClient:
    """MCP client using the standard MCP library."""

    def __init__(
        self,
        container_name: str = "evernote-mcp-server-evernote-mcp-server-1",
        timeout: float = 30.0,
    ):
        self.container_name = container_name
        self.timeout = timeout
        self.session: ClientSession | None = None
        self._available_tools: list[Tool] = []
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize the MCP connection using standard client."""
        if self._initialized:
            return

        # Create server parameters with stderr suppressed
        server_params = StdioServerParameters(
            command="docker",
            args=[
                "exec", "-i", "--tty=false",
                self.container_name,
                "sh", "-c", "node mcp-server.js 2>/dev/null"
            ]
        )

        # Connect using standard stdio client
        try:
            self.client_context = stdio_client(server_params)
            self.read, self.write = await self.client_context.__aenter__()

            # Create session
            self.session_context = ClientSession(self.read, self.write)
            self.session = await self.session_context.__aenter__()

            # Initialize the session
            await self.session.initialize()

            self._initialized = True

        except Exception as e:
            raise Exception(f"Failed to initialize MCP connection: {e}")

    async def close(self):
        """Close the MCP connection."""
        try:
            if hasattr(self, 'session_context') and self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if hasattr(self, 'client_context') and self.client_context:
                await self.client_context.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            self._initialized = False
            self.session = None

    async def list_tools(self) -> list[Tool]:
        """List available tools from the MCP server."""
        if not self._initialized:
            await self.initialize()

        if not self.session:
            raise Exception("MCP session not initialized")

        try:
            result = await self.session.list_tools()
            self._available_tools = result.tools
            return result.tools
        except Exception as e:
            raise Exception(f"Failed to list tools: {e}")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> Any:
        """Call a tool on the MCP server."""
        if not self._initialized:
            await self.initialize()

        if not self.session:
            raise Exception("MCP session not initialized")

        try:
            result = await self.session.call_tool(name, arguments or {})
            return result
        except Exception as e:
            raise Exception(f"Failed to call tool '{name}': {e}")

    async def create_search(self, query: str) -> Any:
        """Create a search for Evernote notes."""
        return await self.call_tool("createSearch", {"query": query})

    async def get_search(self, search_id: str) -> Any:
        """Get cached search results."""
        return await self.call_tool("getSearch", {"searchId": search_id})

    async def get_note(self, note_guid: str) -> Any:
        """Get note metadata."""
        return await self.call_tool("getNote", {"noteGuid": note_guid})

    async def get_note_content(
        self,
        note_guid: str,
        prefer_html: bool = False,
    ) -> Any:
        """Get full note content."""
        arguments = {
            "noteGuid": note_guid,
            "format": "html" if prefer_html else "text"
        }
        return await self.call_tool("getNoteContent", arguments)

    @property
    def available_tools(self) -> list[Tool]:
        """Get the list of available tools."""
        return self._available_tools.copy()

    @property
    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized