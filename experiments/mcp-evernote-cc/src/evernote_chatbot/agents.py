"""Evernote AI Agent using OpenAI Agents SDK with MCP integration."""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseTextDeltaEvent,
)
from agents import Agent, Runner, function_tool, RunContextWrapper
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


def _create_evernote_agent_with_mcp(mcp_client) -> Agent:
    """
    Create the Evernote agent with MCP client wrapper.

    Args:
        mcp_client: ProperMCPClient instance (already initialized)

    Returns:
        Agent configured for Evernote operations
    """
    # Create custom tools that wrap the MCP client methods
    @function_tool
    async def evernote_search(query: str) -> str:
        """
        Search Evernote notes using natural language queries.

        Args:
            query: Natural language search query

        Returns:
            JSON string with search results including note titles, GUIDs, and metadata
        """
        import json
        result = await mcp_client.create_search(query)
        return json.dumps(result.content[0].text if result.content else str(result))

    @function_tool
    async def get_note_content(note_guid: str, format: str = "text") -> str:
        """
        Retrieve the full content of a specific Evernote note.

        Args:
            note_guid: The unique identifier (GUID) of the note
            format: Content format - "text" or "html" (default: "text")

        Returns:
            The note content as text or HTML
        """
        import json
        prefer_html = (format.lower() == "html")
        result = await mcp_client.get_note_content(note_guid, prefer_html=prefer_html)
        return json.dumps(result.content[0].text if result.content else str(result))

    evernote_agent = Agent(
        name="Evernote Search Agent",
        instructions="""
        You are an AI assistant that helps users search and retrieve information from their Evernote notes.

        # Available Tools
        You have access to the following Evernote tools:
        - **evernote_search(query)**: Search notes using natural language queries. Returns search results with note titles, GUIDs, dates, and tags.
        - **get_note_content(note_guid, format)**: Retrieve full note content by GUID. Format can be "text" or "html".

        # Behavior Guidelines
        1. **Understand user intent**: Parse natural language queries to create effective Evernote searches.
        2. **Use appropriate tools**: Start with evernote_search for new queries, then use get_note_content if users want to see full content.
        3. **Format results clearly**: Present note titles, creation dates, update dates, and tags in a readable format.
        4. **Handle content intelligently**: When users ask for content, retrieve it and summarize if needed.
        5. **Be conversational**: Respond naturally and ask clarifying questions if the query is ambiguous.

        # Example Interactions
        User: "Find my notes about machine learning"
        → Use evernote_search with query: "machine learning"
        → Present results with titles and dates

        User: "Show me the content of the note about transformers"
        → Use evernote_search to find the note
        → Use get_note_content with the note GUID to retrieve full content
        → Present or summarize the content

        # Constraints
        - You cannot modify or delete notes (read-only access)
        - You cannot create new notes or notebooks
        - Always respect the user's privacy and data

        # Tone
        Be helpful, concise, and professional. Avoid unnecessary technical details unless asked.
        """,
        tools=[evernote_search, get_note_content],
    )

    return evernote_agent


async def run_evernote_agent(
    mcp_client,
    conversation: list[dict[str, str]],
    stream: bool = True
) -> Any:
    """
    Run the Evernote agent with an existing MCP client.

    Args:
        mcp_client: ProperMCPClient instance (already initialized)
        conversation: List of conversation messages [{"role": "user", "content": "..."}]
        stream: Whether to stream the response (default: True)

    Returns:
        Agent run result (streamed or complete)

    Raises:
        Exception: If agent execution fails
    """
    try:
        # Create agent with MCP client
        evernote_agent = _create_evernote_agent_with_mcp(mcp_client)

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
    mcp_client,
    user_input: str,
    conversation_history: list[dict[str, str]] | None = None
) -> tuple[str, list[dict[str, str]]]:
    """
    Run the Evernote agent with a single user input and maintain conversation history.

    Args:
        mcp_client: ProperMCPClient instance (already initialized)
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
        mcp_client=mcp_client,
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
