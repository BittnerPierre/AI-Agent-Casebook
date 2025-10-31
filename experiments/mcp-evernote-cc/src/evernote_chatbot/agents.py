"""Evernote AI Agent using OpenAI Agents SDK with MCP integration."""

import asyncio
import os
import shutil
from typing import Any

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseTextDeltaEvent,
)
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Console, Group

from .config import ChatbotConfig

# Load environment variables from root .env
_ = load_dotenv(find_dotenv())

# Initialize OpenAI client
client = OpenAI()


async def process_stream_events(response):
    """
    Process and print stream events from an agent response.

    Args:
        response: The response object containing stream events
    """
    async for event in response.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseFunctionCallArgumentsDeltaEvent):
                # Streamed parameters for tool call
                print(event.data.delta, end="", flush=True)
            elif isinstance(event.data, ResponseTextDeltaEvent):
                # Streamed final answer tokens
                print(event.data.delta, end="", flush=True)
        elif event.type == "agent_updated_stream_event":
            # Current agent in use
            print(f"\n> Current Agent: {event.new_agent.name}")
        elif event.type == "run_item_stream_event":
            if event.name == "tool_called":
                # Full tool call after streaming
                print()
                if hasattr(event.item.raw_item, 'name'):
                    print(f"> Tool Called: {event.item.raw_item.name}")
                else:
                    print("> Tool Called")
            elif event.name == "tool_output":
                # Tool execution response
                output = event.item.raw_item.get('output', '')
                # Truncate long outputs for readability
                if len(str(output)) > 200:
                    output = str(output)[:200] + "..."
                print(f"> Tool Output: {output}")


def _create_evernote_mcp_server(container_name: str) -> MCPServerStdio:
    """
    Create the Evernote MCP server connection.

    Args:
        container_name: Docker container name for the Evernote MCP server

    Returns:
        MCPServerStdio instance configured for Evernote operations
    """
    # Find docker command - try multiple locations
    docker_cmd = shutil.which("docker")
    if not docker_cmd:
        # Try common Docker locations on macOS
        possible_paths = [
            "/Applications/Docker.app/Contents/Resources/bin/docker",
            "/usr/local/bin/docker",
            "/opt/homebrew/bin/docker",
        ]
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                docker_cmd = path
                break

    if not docker_cmd:
        raise Exception(
            "Docker command not found. Please ensure Docker Desktop is installed."
        )

    # Create MCP server using docker exec to connect to running container
    evernote_mcp_server = MCPServerStdio(
        name="EVERNOTE_MCP_SERVER",
        params={
            "command": docker_cmd,
            "args": [
                "exec", "-i", "--tty=false",
                container_name,
                "sh", "-c", "node mcp-server.js 2>/dev/null"
            ],
        },
        cache_tools_list=True,
    )

    return evernote_mcp_server


def _create_evernote_agent_with_mcp(mcp_server: MCPServerStdio) -> Agent:
    """
    Create the Evernote agent with MCP server.

    Args:
        mcp_server: MCPServerStdio instance for Evernote

    Returns:
        Agent configured with MCP server
    """
    # Create agent with MCP server
    evernote_agent = Agent(
        name="Evernote Search Agent",
        instructions="""
        You are an AI assistant that helps users search and retrieve information from their Evernote notes.

        # Available MCP Tools
        You have access to Evernote MCP tools that allow you to:
        - Search for notes using natural language queries
        - Retrieve full note content by GUID
        - Get note metadata

        # Behavior Guidelines
        1. **Understand user intent**: Parse natural language queries to create effective Evernote searches.
        2. **Use appropriate tools**: Start with search for new queries, then retrieve content if users want full details.
        3. **Format results clearly**: Present note titles, creation dates, update dates, and tags in a readable format.
        4. **Handle content intelligently**: When users ask for content, retrieve it and summarize if needed.
        5. **Be conversational**: Respond naturally and ask clarifying questions if the query is ambiguous.

        # Example Interactions
        User: "Find my notes about machine learning"
        → Use createSearch tool with query: "machine learning"
        → Present results with titles and dates

        User: "Show me the content of the note about transformers"
        → Use createSearch to find the note
        → Use getNoteContent with the note GUID to retrieve full content
        → Present or summarize the content

        # Constraints
        - You cannot modify or delete notes (read-only access)
        - You cannot create new notes or notebooks
        - Always respect the user's privacy and data

        # Tone
        Be helpful, concise, and professional. Avoid unnecessary technical details unless asked.
        """,
        mcp_servers=[mcp_server],
    )

    return evernote_agent


async def run_evernote_agent(
    mcp_server: MCPServerStdio,
    conversation: list[dict[str, str]],
    stream: bool = True
) -> Any:
    """
    Run the Evernote agent with MCP server.

    Args:
        mcp_server: MCPServerStdio instance for Evernote
        conversation: List of conversation messages [{"role": "user", "content": "..."}]
        stream: Whether to stream the response (default: True)

    Returns:
        Agent run result (streamed or complete)

    Raises:
        Exception: If agent execution fails
    """
    try:
        # Create agent with MCP server
        evernote_agent = _create_evernote_agent_with_mcp(mcp_server)

        # Run agent with or without streaming
        if stream:
            result = Runner.run_streamed(evernote_agent, conversation)
            return result
        else:
            result = await Runner.run(evernote_agent, conversation)
            return result

    except Exception as e:
        print(f"❌ Error running Evernote agent: {e}")
        raise


async def run_evernote_agent_interactive(
    mcp_server: MCPServerStdio,
    user_input: str,
    conversation_history: list[dict[str, str]] | None = None
) -> tuple[str, list[dict[str, str]]]:
    """
    Run the Evernote agent with a single user input and maintain conversation history.

    Args:
        mcp_server: MCPServerStdio instance for Evernote
        user_input: User's input message
        conversation_history: Previous conversation history (optional)

    Returns:
        Tuple of (agent_response, updated_conversation_history)
    """
    if conversation_history is None:
        conversation_history = []

    # Add user message to conversation
    conversation_history.append({"role": "user", "content": user_input})

    # Run agent with streaming
    streamed_result = await run_evernote_agent(
        mcp_server=mcp_server,
        conversation=conversation_history,
        stream=True
    )

    # Setup rich live display for tool calls
    import sys
    console = Console(file=sys.stderr)  # Use stderr to avoid interfering with stdout
    live = Live(console=console, auto_refresh=True, transient=True)
    live.start()

    tool_items: list[str] = []  # List of active tool names
    response_text = ""
    response_started = False

    try:
        async for event in streamed_result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    # Once response starts, stop live (transient will auto-clear)
                    if not response_started:
                        response_started = True
                        live.stop()
                    response_text += event.data.delta
                    print(event.data.delta, end="", flush=True)
            elif event.type == "run_item_stream_event":
                if event.name == "tool_called" and not response_started:
                    # Add tool to live display with spinner
                    if hasattr(event.item.raw_item, 'name'):
                        tool_name = event.item.raw_item.name
                        if tool_name not in tool_items:
                            tool_items.append(tool_name)

                        # Update live display with all active tools
                        spinners = [Spinner("dots", text=f"🔧 {name}") for name in tool_items]
                        live.update(Group(*spinners))

        # Stop live display if still running (transient will auto-clear)
        if not response_started:
            live.stop()

        print()  # New line after streaming

    finally:
        if live.is_started:
            live.stop()

    # Add assistant response to conversation
    conversation_history.append({"role": "assistant", "content": response_text})

    return response_text, conversation_history
