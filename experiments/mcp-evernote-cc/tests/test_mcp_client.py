"""Tests for MCP client."""

import json
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from evernote_chatbot.mcp_client import (
    MCPClient,
    MCPConnectionError,
    MCPServerError,
)


class TestMCPClient:
    """Test cases for MCPClient class."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"result": "success"}
        response.raise_for_status = Mock()
        return response

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mcp_client(self, mock_client):
        """Create MCP client with mocked HTTP client."""
        client = MCPClient("https://test.com/mcp")
        client._client = mock_client
        return client

    async def test_initialization(self):
        """Test MCP client initialization."""
        client = MCPClient(
            base_url="https://example.com:8443/mcp",
            headers={"Authorization": "Bearer token"},
            timeout=60.0,
        )

        assert client.base_url == "https://example.com:8443/mcp"
        assert client.timeout == 60.0
        assert not client.is_initialized
        assert client.available_tools == []

        await client.close()

    async def test_context_manager(self, mock_client, mock_response):
        """Test using MCP client as async context manager."""
        mock_client.post.return_value = mock_response
        mock_response.json.return_value = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"},
        }

        client = MCPClient("https://test.com/mcp")
        client._client = mock_client

        async with client as c:
            assert c.is_initialized
            mock_client.post.assert_called_once()

        mock_client.aclose.assert_called_once()

    async def test_initialize_success(self, mcp_client, mock_response):
        """Test successful initialization."""
        mcp_client._client.post.return_value = mock_response
        mock_response.json.return_value = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "evernote-mcp-server", "version": "2.1.3"},
        }

        result = await mcp_client.initialize()

        assert result.protocolVersion == "2024-11-05"
        assert mcp_client.is_initialized
        mcp_client._client.post.assert_called_once_with(
            "https://test.com/mcp/initialize",
            json={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "evernote-chatbot", "version": "0.1.0"},
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_initialize_connection_error(self, mcp_client):
        """Test initialization with connection error."""
        mcp_client._client.post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(MCPConnectionError, match="Failed to connect"):
            await mcp_client.initialize()

        assert not mcp_client.is_initialized

    async def test_initialize_http_error(self, mcp_client):
        """Test initialization with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        error = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mcp_client._client.post.side_effect = error

        with pytest.raises(MCPServerError, match="MCP server error 500"):
            await mcp_client.initialize()

    async def test_initialize_timeout(self, mcp_client):
        """Test initialization with timeout."""
        mcp_client._client.post.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(MCPConnectionError, match="Request timeout"):
            await mcp_client.initialize()

    async def test_initialize_invalid_json(self, mcp_client, mock_response):
        """Test initialization with invalid JSON response."""
        mcp_client._client.post.return_value = mock_response
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with pytest.raises(MCPServerError, match="Invalid JSON response"):
            await mcp_client.initialize()

    async def test_list_tools(self, mcp_client, mock_response):
        """Test listing tools."""
        # Setup initialization
        mcp_client._initialized = True

        # Setup tools response
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "createSearch",
                    "description": "Create a search",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                {
                    "name": "getNote",
                    "description": "Get a note",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        }
        mcp_client._client.post.return_value = mock_response

        result = await mcp_client.list_tools()

        assert len(result.tools) == 2
        assert result.tools[0].name == "createSearch"
        assert result.tools[1].name == "getNote"
        assert len(mcp_client.available_tools) == 2

    async def test_call_tool(self, mcp_client, mock_response):
        """Test calling a tool."""
        mcp_client._initialized = True

        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Tool response"}]
        }
        mcp_client._client.post.return_value = mock_response

        result = await mcp_client.call_tool(
            "createSearch", {"query": "test query"}
        )

        assert result.content[0].text == "Tool response"

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "createSearch",
                    "arguments": {"query": "test query"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_create_search(self, mcp_client, mock_response):
        """Test create search convenience method."""
        mcp_client._initialized = True
        mock_response.json.return_value = {"content": []}
        mcp_client._client.post.return_value = mock_response

        await mcp_client.create_search("test query")

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "createSearch",
                    "arguments": {"query": "test query"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_get_search(self, mcp_client, mock_response):
        """Test get search convenience method."""
        mcp_client._initialized = True
        mock_response.json.return_value = {"content": []}
        mcp_client._client.post.return_value = mock_response

        await mcp_client.get_search("search123")

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "getSearch",
                    "arguments": {"searchId": "search123"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_get_note(self, mcp_client, mock_response):
        """Test get note convenience method."""
        mcp_client._initialized = True
        mock_response.json.return_value = {"content": []}
        mcp_client._client.post.return_value = mock_response

        await mcp_client.get_note("note123")

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "getNote",
                    "arguments": {"noteGuid": "note123"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_get_note_content(self, mcp_client, mock_response):
        """Test get note content convenience method."""
        mcp_client._initialized = True
        mock_response.json.return_value = {"content": []}
        mcp_client._client.post.return_value = mock_response

        # Test without HTML preference
        await mcp_client.get_note_content("note123")

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "getNoteContent",
                    "arguments": {"noteGuid": "note123"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

        # Test with HTML preference
        await mcp_client.get_note_content("note123", prefer_html=True)

        mcp_client._client.post.assert_called_with(
            "https://test.com/mcp/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "getNoteContent",
                    "arguments": {"noteGuid": "note123", "format": "html"},
                },
            },
            headers={"Content-Type": "application/json"},
        )

    async def test_auto_initialize_on_tool_call(self, mcp_client, mock_response):
        """Test that calling a tool auto-initializes if not initialized."""
        # Client starts uninitialized
        assert not mcp_client.is_initialized

        # Mock responses for both initialize and tool call
        init_response = Mock()
        init_response.json.return_value = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"},
        }
        init_response.raise_for_status = Mock()

        tool_response = Mock()
        tool_response.json.return_value = {"content": []}
        tool_response.raise_for_status = Mock()

        mcp_client._client.post.side_effect = [init_response, tool_response]

        await mcp_client.call_tool("test", {})

        # Should have made two calls: initialize and tool call
        assert mcp_client._client.post.call_count == 2
        assert mcp_client.is_initialized

    async def test_base_url_normalization(self):
        """Test that base URL is normalized (trailing slash removed)."""
        client = MCPClient("https://example.com/mcp/")
        assert client.base_url == "https://example.com/mcp"

        await client.close()

    async def test_close(self, mcp_client):
        """Test client cleanup."""
        await mcp_client.close()
        mcp_client._client.aclose.assert_called_once()