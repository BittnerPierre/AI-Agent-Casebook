"""MCP client for stdio communication with Evernote MCP server via Docker."""

import asyncio
import json
import logging
from typing import Any

from mcp.types import (
    CallToolResult,
    InitializeResult,
    ListToolsResult,
    Tool,
)

logger = logging.getLogger(__name__)


class MCPStdioClientError(Exception):
    """Base exception for MCP stdio client errors."""
    pass


class MCPStdioClient:
    """MCP client for stdio communication via Docker exec."""

    def __init__(
        self,
        container_name: str = "evernote-mcp-server-evernote-mcp-server-1",
        timeout: float = 30.0,
    ):
        self.container_name = container_name
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
        """Close the subprocess."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
            finally:
                self._process = None

    async def _start_process(self) -> None:
        """Start the Docker exec process."""
        cmd = [
            "docker", "exec", "-i", "--tty=false",
            self.container_name,
            "node", "mcp-server.js"
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            raise MCPStdioClientError(f"Failed to start MCP server process: {e}")

    async def _send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request to the MCP server."""
        if not self._process or not self._process.stdin:
            raise MCPStdioClientError("MCP server process not started")

        # Add request ID
        self._request_id += 1
        request["id"] = self._request_id

        # Send request
        request_json = json.dumps(request) + "\\n"
        print(f"DEBUG: Sending request: {request_json.strip()}")  # Debug print

        try:
            self._process.stdin.write(request_json.encode())
            await self._process.stdin.drain()
        except Exception as e:
            raise MCPStdioClientError(f"Failed to send request: {e}")

        # Read response
        try:
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=self.timeout
            )
            if not response_line:
                raise MCPStdioClientError("No response from MCP server")

            line_text = response_line.decode().strip()
            print(f"DEBUG: Received response: {line_text}")  # Debug print

            response_data = json.loads(line_text)
            print(f"DEBUG: Parsed response: {response_data}")  # Debug print

            if "error" in response_data:
                error = response_data["error"]
                raise MCPStdioClientError(f"MCP server error: {error}")

            return response_data

        except TimeoutError:
            raise MCPStdioClientError(f"Request timeout after {self.timeout} seconds")
        except json.JSONDecodeError as e:
            raise MCPStdioClientError(f"Invalid JSON response: {e}")

    async def initialize(self) -> InitializeResult:
        """Initialize the MCP connection."""
        if self._initialized:
            return InitializeResult(
                protocolVersion="2024-11-05",
                capabilities={},
                serverInfo={"name": "evernote-mcp-server", "version": "2.1.3"},
            )

        # Start the process
        await self._start_process()

        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "evernote-chatbot", "version": "0.1.0"},
            },
        }

        try:
            response_data = await self._send_request(request)
            result = InitializeResult.model_validate(response_data.get("result", {}))
            self._initialized = True
            return result
        except Exception as e:
            await self.close()
            raise MCPStdioClientError(f"Failed to initialize MCP connection: {e}")

    async def list_tools(self) -> ListToolsResult:
        """List available tools from the MCP server."""
        if not self._initialized:
            await self.initialize()

        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
        }

        try:
            response_data = await self._send_request(request)
            result = ListToolsResult.model_validate(response_data.get("result", {}))
            self._available_tools = result.tools
            return result
        except Exception as e:
            raise MCPStdioClientError(f"Failed to list tools: {e}")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> CallToolResult:
        """Call a tool on the MCP server."""
        if not self._initialized:
            await self.initialize()

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {},
            },
        }

        try:
            response_data = await self._send_request(request)
            return CallToolResult.model_validate(response_data.get("result", {}))
        except Exception as e:
            raise MCPStdioClientError(f"Failed to call tool '{name}': {e}")

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