from __future__ import annotations

import argparse
import asyncio
import os
import shlex
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from agents import Agent, Runner
from agents.items import (
    ItemHelpers,
    MCPListToolsItem,
    MessageOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from agents.mcp import MCPServerStreamableHttp
from agents.run_context import RunContextWrapper


@dataclass
class EvernoteChatContext:
    notebooks: list[str]
    max_notes: int
    summarize_html: bool


def build_instructions(
    context: RunContextWrapper[EvernoteChatContext], agent: Agent[EvernoteChatContext]
) -> str:
    ctx = context.context
    notebooks_hint = ""
    if ctx.notebooks:
        joined = ", ".join(ctx.notebooks)
        notebooks_hint = (
            "Focus searches on the following Evernote notebooks when relevant: "
            f"{joined}.\n"
        )

    limit_hint = f"Limit yourself to reviewing at most {ctx.max_notes} notes per request.\n"

    html_hint = (
        "Prefer HTML content if you need structure."
        if ctx.summarize_html
        else "Always request plain text content from Evernote."
    )

    return (
        "You are an Evernote research assistant.\n"
        "Use the Evernote MCP tools to find and read notes.\n"
        "Workflow:\n"
        "1. Call createSearch with plain language or Evernote search syntax to find note ids.\n"
        "2. When you have note ids, call getNote or getNoteContent to read metadata and bodies.\n"
        "3. Combine findings into clear summaries with actionable insights.\n"
        "Avoid vector stores or embeddings; rely entirely on Evernote search and metadata.\n"
        "Summaries must cite note titles and created/updated dates when helpful.\n"
        f"{notebooks_hint}"
        f"{limit_hint}"
        f"{html_hint}\n"
        "If the user asks for recent notes, sort by update time.\n"
        "If no notes match, say so and suggest alternative queries."
    )


DEFAULT_HEADERS: dict[str, str] = {}


def parse_headers(raw_headers: Sequence[str] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not raw_headers:
        return headers
    for header in raw_headers:
        if ":" not in header:
            raise ValueError(f"Invalid header format (expected Key: Value): {header}")
        key, value = header.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def build_mcp_streamable_http(url: str, headers: dict[str, str] | None = None) -> MCPServerStreamableHttp:
    params: dict[str, Any] = {"url": url}
    if headers:
        params["headers"] = headers
    return MCPServerStreamableHttp(
        name="Evernote MCP Server",
        params=params,
        cache_tools_list=True,
    )


def format_exception(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        lines = ["Exception group:"]
        for idx, sub in enumerate(exc.exceptions, 1):
            lines.append(f"  {idx}. {format_exception(sub)}")
        return "\n".join(lines)
    return str(exc)


def extract_assistant_text(new_items: Iterable[Any]) -> str:
    parts: list[str] = []
    for item in new_items:
        if isinstance(item, MessageOutputItem):
            parts.append(ItemHelpers.text_message_output(item))
    return "".join(parts)


def extract_tool_log(new_items: Iterable[Any]) -> list[str]:
    logs: list[str] = []
    for item in new_items:
        if isinstance(item, ToolCallItem):
            logs.append(f"→ tool call: {item.raw_item.name} {item.raw_item.arguments}")
        elif isinstance(item, ToolCallOutputItem):
            logs.append(f"← tool result: {item.raw_item.call_id}")
        elif isinstance(item, MCPListToolsItem):
            logs.append("Listed MCP tools")
    return logs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with Evernote via MCP")
    parser.add_argument(
        "--model",
        default=os.environ.get("EVERNOTE_CHAT_MODEL", "gpt-4.1-mini"),
        help="LLM to use with the Agents SDK",
    )
    parser.add_argument(
        "--http-url",
        default=os.environ.get("EVERNOTE_MCP_HTTP_URL", "https://localhost:3443/mcp"),
        help="Evernote MCP Streamable HTTP endpoint",
    )
    parser.add_argument(
        "--http-header",
        action="append",
        default=None,
        help="Custom HTTP headers for the MCP connection (Key: Value, repeatable)",
    )
    parser.add_argument(
        "--notebook",
        action="append",
        default=None,
        help="Restrict searches to one or more notebook names",
    )
    parser.add_argument(
        "--max-notes",
        type=int,
        default=int(os.environ.get("EVERNOTE_CHAT_MAX_NOTES", "20")),
        help="Preferred maximum number of notes to read per request",
    )
    parser.add_argument(
        "--prefer-html",
        action="store_true",
        help="Allow the agent to request HTML bodies when summarizing",
    )
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Print MCP tool activity after each response",
    )
    return parser


async def chat_loop(args: argparse.Namespace) -> None:
    try:
        headers = parse_headers(args.http_header)
    except ValueError as exc:
        print(f"Invalid header configuration: {exc}")
        return
    server = build_mcp_streamable_http(args.http_url, headers)
    context = EvernoteChatContext(
        notebooks=args.notebook or [],
        max_notes=args.max_notes,
        summarize_html=args.prefer_html,
    )

    agent = Agent(
        name="evernote_researcher",
        instructions=build_instructions,
        model=args.model,
        mcp_servers=[server],
        output_type=str,
    )

    print("Starting Evernote MCP chat. Type 'exit' to quit.\n")

    history: list[dict[str, Any]] | None = None

    try:
        await server.__aenter__()
    except FileNotFoundError as exc:
        print(f"Failed to connect to Evernote MCP server: {exc}")
        return
    except Exception as exc:
        print(f"Error initializing MCP server: {format_exception(exc)}")
        return

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye.")
                break

            items: list[dict[str, Any]]
            if history is None:
                items = [{"role": "user", "content": user_input}]
            else:
                items = history + [{"role": "user", "content": user_input}]

            print("Assistant: …", end="", flush=True)

            result = await Runner.run(agent, items, context=context)

            assistant_text = result.final_output if isinstance(result.final_output, str) else ""
            if not assistant_text:
                assistant_text = extract_assistant_text(result.new_items)

            print(f"\rAssistant: {assistant_text.strip()}\n")

            if args.show_tools:
                for log in extract_tool_log(result.new_items):
                    print(log)

            history = result.to_input_list()  # includes assistant reply
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {format_exception(exc)}")
    finally:
        await server.__aexit__(None, None, None)


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    asyncio.run(chat_loop(args))


if __name__ == "__main__":
    main()
