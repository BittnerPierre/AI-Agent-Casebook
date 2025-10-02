"""CLI interface for Evernote Chatbot with session memory."""

import asyncio
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.prompt import Prompt

from .config import ChatbotConfig
from .evernote_handler import EvernoteHandler
from .formatter import ResponseFormatter
from .mcp_client import ProperMCPClient as MCPClient
from .session import ChatSession

app = typer.Typer(
    name="evernote-chat",
    help="Terminal chatbot for Evernote MCP server communication",
    no_args_is_help=True,
)


class ChatbotCLI:
    """Main CLI application for Evernote chatbot."""

    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.console = Console()
        self.formatter = ResponseFormatter(config, self.console)
        self.session: ChatSession | None = None
        self.mcp_client: MCPClient | None = None
        self.evernote_handler: EvernoteHandler | None = None

    async def initialize(self) -> bool:
        """Initialize MCP client and Evernote handler."""
        # Setup progress tracking with log file (but don't start it yet)
        log_file = Path.home() / ".evernote_chatbot" / "debug.log"
        progress = self.formatter.init_progress_tracker(log_file)

        try:
            # Use progress only during initialization, then stop it
            with progress:
                progress.start_task("connect", "Connecting to Evernote MCP server...")

                # Initialize MCP client
                self.mcp_client = MCPClient(
                    container_name=self.config.container_name,
                    timeout=self.config.mcp_timeout,
                )

                # Initialize connection
                await self.mcp_client.initialize()
                progress.update_task("connect", "Verifying MCP server capabilities...")

                # List available tools
                tools_list = await self.mcp_client.list_tools()
                available_tool_names = [tool.name for tool in tools_list]

                # Check for required tools
                required_tools = {"createSearch", "getSearch", "getNote", "getNoteContent"}
                missing_tools = required_tools - set(available_tool_names)

                if missing_tools:
                    progress.fail_task("connect", f"Missing required tools: {', '.join(missing_tools)}")
                    return False

                progress.update_task("connect", "Initializing Evernote handler...")

                # Initialize Evernote handler
                self.evernote_handler = EvernoteHandler(
                    mcp_client=self.mcp_client,
                    max_notes_per_query=self.config.max_notes_per_query,
                    allowed_notebooks=self.config.allowed_notebooks,
                    prefer_html=self.config.prefer_html,
                )

                # Initialize session
                self.session = ChatSession(
                    config=self.config,
                    save_history=self.config.save_history,
                    history_file=self.config.history_file,
                )

                progress.complete_task("connect", "Connected to Evernote MCP server!")

            # Progress tracker stops here - terminal is free for interactive prompts
            return True

        except Exception as e:
            if progress:
                progress.fail_task("connect", f"Connection failed: {str(e)}")
            else:
                self.formatter.display_error(e, "initialization")
            return False

    async def run_interactive(self) -> None:
        """Run the interactive chat session."""
        # Display welcome message
        self._display_welcome()

        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    "\n[bold blue]You[/bold blue]",
                    default="",
                    console=self.console
                ).strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ("/quit", "/exit", "/q"):
                    break
                elif user_input.lower() in ("/help", "/h"):
                    self._display_help()
                    continue
                elif user_input.lower() == "/config":
                    self.formatter.display_config()
                    continue
                elif user_input.lower() == "/history":
                    self._display_history()
                    continue
                elif user_input.lower() == "/clear":
                    self.session.clear_history()
                    self.formatter.display_info("Conversation history cleared.")
                    continue

                # Add to session history
                self.session.add_user_message(user_input)

                # Process the query
                await self._process_query(user_input)

            except KeyboardInterrupt:
                self.formatter.display_info("\\nUse /quit to exit.")
            except EOFError:
                # Handle EOF (Ctrl+D or stdin closed)
                self.formatter.display_info("\\nExiting...")
                break
            except Exception as e:
                self.formatter.display_error(e, "processing query")

        # Save session before exit
        if self.session:
            self.session.save_session_history()
            self.formatter.display_info("Session saved. Goodbye!")

    async def run_single_query(self, query: str) -> None:
        """Run a single query and exit."""
        try:
            await self._process_query(query)
        except Exception as e:
            self.formatter.display_error(e, "query execution")
            sys.exit(1)

    async def _process_query(self, query: str) -> None:
        """Process a user query and display results."""
        if not self.evernote_handler:
            self.formatter.display_error("Evernote handler not initialized")
            return

        try:
            # Create a new progress context for this query
            progress = self.formatter.progress
            if progress:
                with progress:
                    progress.start_task("search", f"Searching for: {query}")

                    # Search for notes
                    search_result = await self.evernote_handler.search_notes(query)
                    progress.complete_task("search", f"Found {search_result.total_notes} notes")

                    # Progress stops here, results display normally
            else:
                # Fallback if no progress system
                self.formatter.display_info(f"Searching for: {query}")
                search_result = await self.evernote_handler.search_notes(query)

            if search_result.total_notes == 0:
                response = self.formatter.format_search_results(search_result)
                self.formatter.print_markdown(response)
                self.session.add_assistant_message(f"No notes found for query: {query}")
                return

            # Display search results table (this stays visible)
            self.formatter.display_search_results_table(search_result)

            # Ask if user wants detailed content
            get_content = False
            try:
                if search_result.total_notes <= 5:
                    response = Prompt.ask(
                        "\\n[yellow]Get detailed content for these notes?[/yellow]",
                        choices=["yes", "no", "y", "n"],
                        default="yes",
                        console=self.console
                    )
                    get_content = response.lower() in ("yes", "y")
                else:
                    response = Prompt.ask(
                        f"\\n[yellow]Found {search_result.total_notes} notes. Get content for how many?[/yellow]",
                        default="5",
                        console=self.console
                    )
                    try:
                        limit = int(response)
                        if limit > 0:
                            search_result.notes = search_result.notes[:limit]
                            get_content = True
                        else:
                            get_content = False
                    except ValueError:
                        get_content = False
            except Exception as e:
                # If prompt fails, default to False
                print(f"Input error: {e}")
                get_content = False

            # Get detailed content if requested
            if get_content:
                note_count = len(search_result.notes)

                # Use progress context for content retrieval
                progress = self.formatter.progress
                if progress:
                    with progress:
                        progress.start_task("content", f"Retrieving content for {note_count} notes...")

                        note_guids = [note.guid for note in search_result.notes]
                        notes_with_content = await self.evernote_handler.get_notes_with_content(note_guids)

                        progress.complete_task("content", f"Retrieved content for {len(notes_with_content)} notes")
                else:
                    # Fallback without progress
                    self.formatter.display_info("Retrieving note contents...")
                    note_guids = [note.guid for note in search_result.notes]
                    notes_with_content = await self.evernote_handler.get_notes_with_content(note_guids)

                # Format and display results
                response = self.formatter.format_search_results(search_result, notes_with_content)
                self.formatter.print_markdown(response)

                # Create summary
                summary_text = self._create_query_summary(query, search_result, notes_with_content)
                self.session.add_assistant_message(summary_text)
            else:
                # Just show search results
                response = self.formatter.format_search_results(search_result)
                self.formatter.print_markdown(response)
                self.session.add_assistant_message(f"Found {search_result.total_notes} notes for: {query}")

        except Exception as e:
            import traceback
            print("DEBUG: Full error traceback:")
            traceback.print_exc()
            self.formatter.display_error(e, "query processing")

    def _create_query_summary(
        self,
        query: str,
        search_result,
        notes_with_content: dict[str, Any],
    ) -> str:
        """Create a summary of the query results."""
        summary_parts = [
            f"Query: {query}",
            f"Found {search_result.total_notes} notes",
            f"Retrieved content for {len(notes_with_content)} notes",
        ]

        # Add note titles
        if notes_with_content:
            titles = [metadata.title for metadata, _ in notes_with_content.values()]
            summary_parts.append(f"Notes: {', '.join(titles)}")

        return " | ".join(summary_parts)

    def _display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = """
# 🗒️ Evernote Chatbot

Welcome to your Evernote terminal assistant! Ask me about your notes using natural language.

## Example queries:
- "Summarize all my Evernotes regarding LLMs"
- "Find notes about project planning from last month"
- "Show me meeting notes tagged with quarterly-review"

## Commands:
- `/help` - Show help
- `/config` - Show current configuration
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/quit` - Exit

Type your question below to get started!
        """
        self.formatter.print_markdown(welcome_text.strip())

    def _display_help(self) -> None:
        """Display help information."""
        help_text = """
# Help - Evernote Chatbot Commands

## Search Commands
Just type your question naturally:
- "Find notes about machine learning"
- "Show me notes from last week"
- "What did I write about project X?"

## Special Commands
- `/help`, `/h` - Show this help
- `/config` - Display current configuration
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/quit`, `/exit`, `/q` - Exit the chatbot

## Tips
- Be specific in your queries for better results
- Use keywords that appear in your note titles or content
- Ask follow-up questions to refine your search
- The chatbot remembers your conversation within each session
        """
        self.formatter.print_markdown(help_text.strip())

    def _display_history(self) -> None:
        """Display conversation history."""
        if not self.session or not self.session.messages:
            self.formatter.display_info("No conversation history yet.")
            return

        self.console.print("\\n[bold]Conversation History:[/bold]")
        for i, message in enumerate(self.session.messages, 1):
            role = "You" if message["role"] == "user" else "Assistant"
            timestamp = message.get("timestamp", "Unknown time")
            self.console.print(f"\\n{i}. [{role}] ({timestamp})")
            self.console.print(f"   {message['content']}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.mcp_client:
            await self.mcp_client.close()


@app.command()
def chat(
    mcp_url: str | None = None,
    notebooks: str | None = None,
    max_notes: int | None = None,
    prefer_html: bool = False,
    headers: str | None = None,
    timeout: float | None = None,
    history_file: str | None = None,
    query: str | None = None,
) -> None:
    """Start the Evernote chatbot."""
    # Load base config from environment
    config = ChatbotConfig.from_env()

    # Merge CLI arguments
    config = config.merge_cli_args(
        mcp_url=mcp_url,
        allowed_notebooks=notebooks,
        max_notes_per_query=max_notes,
        prefer_html=prefer_html,
        mcp_headers=headers,
        mcp_timeout=timeout,
        history_file=history_file,
    )

    # Create CLI instance
    cli = ChatbotCLI(config)

    async def run_app():
        """Run the application."""
        try:
            # Initialize
            if not await cli.initialize():
                return

            # Run query or interactive mode
            if query:
                await cli.run_single_query(query)
            else:
                await cli.run_interactive()

        finally:
            await cli.cleanup()

    # Run the async application
    asyncio.run(run_app())


if __name__ == "__main__":
    app()