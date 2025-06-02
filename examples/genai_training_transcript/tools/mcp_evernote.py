#!/usr/bin/env python3
"""
MCP server for Evernote integration.

Implements MCP Filesystem API methods using the Evernote Python SDK.
"""

import os
import asyncio
import argparse
from urllib.parse import urlparse

from evernote.api.client import EvernoteClient
from evernote.edam.type import Notebook, NoteFilter
from evernote.edam.notestore import NoteStore
import mcp.types as types
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions


def parse_uri(uri: str) -> tuple[str, ...]:
    parsed = urlparse(uri)
    if parsed.scheme != "evernote":
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
    return tuple(parsed.path.lstrip("/").split("/"))


async def read_file(note_store: NoteStore, uri: str) -> str:
    parts = parse_uri(uri)
    guid = parts[-1]
    return note_store.getNoteContent(guid)


async def write_file(note_store: NoteStore, uri: str, data: str) -> str:
    parts = parse_uri(uri)
    guid = parts[-1]
    note = note_store.getNote(guid, True, False, False, False)
    note.content = data
    updated = note_store.updateNote(note)
    return updated.guid


async def mkdir(note_store: NoteStore, uri: str) -> str:
    parts = parse_uri(uri)
    name = parts[0]
    notebook = Notebook(name=name)
    created = note_store.createNotebook(notebook)
    return created.guid


async def list_dirs(note_store: NoteStore, uri: str) -> list[types.Notebook]:
    return note_store.listNotebooks()


async def delete_dir(note_store: NoteStore, uri: str) -> bool:
    parts = parse_uri(uri)
    guid = parts[0]
    note_store.expungeNotebook(guid)
    return True


async def move(note_store: NoteStore, src_uri: str, dest_uri: str) -> None:
    raise NotImplementedError


async def search(note_store: NoteStore, uri: str, query: str) -> list[types.NoteMetadata]:
    filter = NoteFilter(words=query)
    result = note_store.findNotesMetadata(filter, 0, 100)
    return result.notes


async def stat(note_store: NoteStore, uri: str) -> dict[str, object]:
    parts = parse_uri(uri)
    guid = parts[-1]
    metadata = note_store.getNoteMetadata(guid, False, False, False, False)
    return {
        "guid": metadata.guid,
        "title": metadata.title,
        "created": metadata.created,
        "updated": metadata.updated,
        "size": len(metadata.content) if metadata.content else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP Evernote server for GenAI Training Transcript"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("EVERNOTE_TOKEN"),
        help="Evernote developer token",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use Evernote sandbox environment",
    )
    args = parser.parse_args()
    if not args.token:
        parser.error("Evernote token must be provided via --token or EVERNOTE_TOKEN")

    client = EvernoteClient(token=args.token, sandbox=args.sandbox)
    note_store = client.get_note_store()

    server = Server(name="Evernote MCP Server")
    @server.call_tool("read_file")
    async def _read_file(uri: str) -> str:
        return await read_file(note_store, uri)

    @server.call_tool("write_file")
    async def _write_file(uri: str, data: str) -> str:
        return await write_file(note_store, uri, data)

    @server.call_tool("mkdir")
    async def _mkdir(uri: str) -> str:
        return await mkdir(note_store, uri)

    @server.call_tool("list_dirs")
    async def _list_dirs(uri: str) -> list[types.Notebook]:
        return await list_dirs(note_store, uri)

    @server.call_tool("delete_dir")
    async def _delete_dir(uri: str) -> bool:
        return await delete_dir(note_store, uri)

    @server.call_tool("move")
    async def _move(src_uri: str, dest_uri: str) -> None:
        return await move(note_store, src_uri, dest_uri)

    @server.call_tool("search")
    async def _search(uri: str, query: str) -> list[types.NoteMetadata]:
        return await search(note_store, uri, query)

    @server.call_tool("stat")
    async def _stat(uri: str) -> dict[str, object]:
        return await stat(note_store, uri)

    async def run_server() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()