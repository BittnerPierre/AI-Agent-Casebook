"""Simple command-line interface for Evernote search without interactive prompts."""

import asyncio
import sys
from pathlib import Path

from rich.console import Console

from .config import ChatbotConfig
from .evernote_handler import EvernoteHandler
from .formatter import ResponseFormatter
from .mcp_client import ProperMCPClient


async def search_evernote(query: str, get_content: bool = False, limit: int = 10) -> None:
    """Search Evernote notes and display results."""
    config = ChatbotConfig.from_env()
    console = Console()
    formatter = ResponseFormatter(config, console)

    # Setup progress tracking
    log_file = Path.home() / ".evernote_chatbot" / "search_debug.log"
    progress = formatter.init_progress_tracker(log_file)

    try:
        with progress:
            progress.start_task("search", f"Searching for: {query}")

            async with ProperMCPClient() as mcp_client:
                handler = EvernoteHandler(
                    mcp_client,
                    max_notes_per_query=limit,
                    allowed_notebooks=config.allowed_notebooks,
                    prefer_html=config.prefer_html
                )

                # Search for notes
                search_result = await handler.search_notes(query)
                progress.complete_task("search", f"Found {search_result.total_notes} notes")

                if search_result.total_notes == 0:
                    console.print("❌ No notes found for your query.")
                    console.print("\n💡 Try different search terms or check your notebook access.")
                    return

                console.print(f"✅ Found {search_result.total_notes} total notes")
                console.print(f"📄 Showing {len(search_result.notes)} results:\n")

            # Display results
            for i, note in enumerate(search_result.notes, 1):
                console.print(f"{i}. {note.title}")
                if note.created:
                    console.print(f"   📅 Created: {note.created.strftime('%Y-%m-%d %H:%M')}")
                if note.updated and note.updated != note.created:
                    console.print(f"   📝 Updated: {note.updated.strftime('%Y-%m-%d %H:%M')}")
                if note.tags:
                    console.print(f"   🏷️  Tags: {', '.join(note.tags)}")
                if note.notebook_name:
                    console.print(f"   📁 Notebook: {note.notebook_name}")
                console.print()

            # Get content if requested
            if get_content and search_result.notes:
                progress.start_task("content", f"Getting content for {len(search_result.notes)} notes...")

                note_guids = [note.guid for note in search_result.notes]
                notes_with_content = await handler.get_notes_with_content(note_guids)

                progress.complete_task("content", f"Retrieved content for {len(notes_with_content)} notes")

                console.print("\n")
                for note in search_result.notes:
                    if note.guid in notes_with_content:
                        metadata, content = notes_with_content[note.guid]
                        console.print("=" * 60)
                        console.print(f"📝 {note.title}")
                        console.print("=" * 60)

                        # Show first 500 characters of content
                        if content:
                            preview = content[:500].strip()
                            if len(content) > 500:
                                preview += "..."
                            console.print(preview)
                        else:
                            console.print("(No content available)")
                        console.print("\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        return


def main():
    """Main entry point for Search CLI."""
    if len(sys.argv) < 2:
        print("Usage: poetry run python -m evernote_chatbot.search_cli \"your search query\" [--content] [--limit N]")
        print("\nExamples:")
        print('  poetry run python -m evernote_chatbot.search_cli "LLM"')
        print('  poetry run python -m evernote_chatbot.search_cli "project planning" --content')
        print('  poetry run python -m evernote_chatbot.search_cli "meeting notes" --limit 5')
        sys.exit(1)

    query = sys.argv[1]
    get_content = "--content" in sys.argv

    # Parse limit
    limit = 10
    try:
        if "--limit" in sys.argv:
            limit_index = sys.argv.index("--limit")
            if limit_index + 1 < len(sys.argv):
                limit = int(sys.argv[limit_index + 1])
    except (ValueError, IndexError):
        limit = 10

    asyncio.run(search_evernote(query, get_content, limit))


if __name__ == "__main__":
    main()