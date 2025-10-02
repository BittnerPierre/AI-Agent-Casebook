"""Simple command-line interface for Evernote search without interactive prompts."""

import asyncio
import sys

from .config import ChatbotConfig
from .evernote_handler import EvernoteHandler
from .mcp_client import ProperMCPClient


async def search_evernote(query: str, get_content: bool = False, limit: int = 10) -> None:
    """Search Evernote notes and display results."""
    config = ChatbotConfig.from_env()

    print(f"🔍 Searching for: {query}")

    try:
        async with ProperMCPClient() as mcp_client:
            handler = EvernoteHandler(
                mcp_client,
                max_notes_per_query=limit,
                allowed_notebooks=config.allowed_notebooks,
                prefer_html=config.prefer_html
            )

            # Search for notes
            search_result = await handler.search_notes(query)

            if search_result.total_notes == 0:
                print("❌ No notes found for your query.")
                print("\n💡 Try different search terms or check your notebook access.")
                return

            print(f"✅ Found {search_result.total_notes} total notes")
            print(f"📄 Showing {len(search_result.notes)} results:\n")

            # Display results
            for i, note in enumerate(search_result.notes, 1):
                print(f"{i}. {note.title}")
                if note.created:
                    print(f"   📅 Created: {note.created.strftime('%Y-%m-%d %H:%M')}")
                if note.updated and note.updated != note.created:
                    print(f"   📝 Updated: {note.updated.strftime('%Y-%m-%d %H:%M')}")
                if note.tags:
                    print(f"   🏷️  Tags: {', '.join(note.tags)}")
                if note.notebook_name:
                    print(f"   📁 Notebook: {note.notebook_name}")
                print()

            # Get content if requested
            if get_content and search_result.notes:
                print("📖 Getting note contents...\n")

                note_guids = [note.guid for note in search_result.notes]
                notes_with_content = await handler.get_notes_with_content(note_guids)

                for note in search_result.notes:
                    if note.guid in notes_with_content:
                        metadata, content = notes_with_content[note.guid]
                        print("=" * 60)
                        print(f"📝 {note.title}")
                        print("=" * 60)

                        # Show first 500 characters of content
                        if content:
                            preview = content[:500].strip()
                            if len(content) > 500:
                                preview += "..."
                            print(preview)
                        else:
                            print("(No content available)")
                        print("\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        return


def main():
    """Main entry point for simple CLI."""
    if len(sys.argv) < 2:
        print("Usage: poetry run python -m evernote_chatbot.simple_cli \"your search query\" [--content] [--limit N]")
        print("\nExamples:")
        print('  poetry run python -m evernote_chatbot.simple_cli "LLM"')
        print('  poetry run python -m evernote_chatbot.simple_cli "project planning" --content')
        print('  poetry run python -m evernote_chatbot.simple_cli "meeting notes" --limit 5')
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