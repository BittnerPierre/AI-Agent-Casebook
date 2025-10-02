"""MCP client for stdio communication with Evernote MCP server via Docker."""

import asyncio
import json
from typing import Any

from mcp.types import (
    CallToolRequest,
    CallToolResult,
    InitializeRequest,
    InitializeRequestParams,
    InitializeResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPConnectionError(MCPClientError):
    """Exception for connection-related errors."""
    pass


class MCPServerError(MCPClientError):
    """Exception for server-side errors."""
    pass


class MCPClient:
    """MCP client for stdio communication via Docker."""

    def __init__(
        self,
        container_name: str = "evernote-mcp-server-evernote-mcp-server-1",
        docker_cmd: str = "docker",
        timeout: float = 30.0,
    ):
        self.container_name = container_name
        self.docker_cmd = docker_cmd
        self.timeout = timeout
        self._process: asyncio.subprocess.Process | None = None
        self._initialized = False
        self._available_tools: list[Tool] = []
        self._request_id = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def _post_request(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request to the MCP server."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = await self._client.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise MCPConnectionError(f"Failed to connect to MCP server at {url}: {e}")
        except httpx.HTTPStatusError as e:
            raise MCPServerError(f"MCP server error {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException as e:
            raise MCPConnectionError(f"Request timeout: {e}")
        except json.JSONDecodeError as e:
            raise MCPServerError(f"Invalid JSON response: {e}")

    async def initialize(self) -> InitializeResult:
        """Initialize the MCP connection."""
        if self._initialized:
            return InitializeResult(
                protocolVersion="2024-11-05",
                capabilities={},
                serverInfo={"name": "evernote-mcp-server", "version": "2.1.3"},
            )

        params = InitializeRequestParams(
            protocolVersion="2024-11-05",
            capabilities={},
            clientInfo={"name": "evernote-chatbot", "version": "0.1.0"},
        )

        request = InitializeRequest(
            method="initialize",
            params=params
        )

        try:
            response_data = await self._post_request("initialize", request.model_dump())
            result = InitializeResult.model_validate(response_data)
            self._initialized = True
            return result
        except Exception as e:
            raise MCPConnectionError(f"Failed to initialize MCP connection: {e}")

    async def list_tools(self) -> ListToolsResult:
        """List available tools from the MCP server."""
        if not self._initialized:
            await self.initialize()

        request = ListToolsRequest()

        try:
            response_data = await self._post_request("tools/list", request.model_dump())
            result = ListToolsResult.model_validate(response_data)
            self._available_tools = result.tools
            return result
        except Exception as e:
            raise MCPServerError(f"Failed to list tools: {e}")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> CallToolResult:
        """Call a tool on the MCP server."""
        if not self._initialized:
            await self.initialize()

        request = CallToolRequest(
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments or {},
            },
        )

        try:
            response_data = await self._post_request("tools/call", request.model_dump())
            return CallToolResult.model_validate(response_data)
        except Exception as e:
            raise MCPServerError(f"Failed to call tool '{name}': {e}")

    async def create_search(self, query: str) -> CallToolResult:
        """Create a search for Evernote notes."""
        return await self.call_tool("createSearch", {"query": query})

    async def get_search(self, search_id: str) -> CallToolResult:
        """Get cached search results."""
        return await self.call_tool("getSearch", {"searchId": search_id})

    async def get_note(self, note_guid: str) -> CallToolResult:
        """Get note metadata."""
        return await self.call_tool("getNote", {"noteGuid": note_guid})

    async def get_note_content(
        self,
        note_guid: str,
        prefer_html: bool = False,
    ) -> CallToolResult:
        """Get full note content."""
        arguments = {"noteGuid": note_guid}
        if prefer_html:
            arguments["format"] = "html"
        return await self.call_tool("getNoteContent", arguments)

    @property
    def available_tools(self) -> list[Tool]:
        """Get the list of available tools."""
        return self._available_tools.copy()

    @property
    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized