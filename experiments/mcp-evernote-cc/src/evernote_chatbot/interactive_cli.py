"""CLI interface for Evernote Chatbot with session memory."""

import asyncio
import sys

try:
    import readline
    readline.set_history_length(1000)
except ImportError:
    # readline not available on some systems
    readline = None

import typer
from rich.console import Console
from rich.prompt import Prompt

from .config import ChatbotConfig
from .formatter import ResponseFormatter
from .session import ChatSession
from .agents import run_evernote_agent_interactive, _create_evernote_mcp_server

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
        self.mcp_server = None

    async def initialize(self) -> bool:
        """Initialize session."""
        try:
            # Initialize session
            self.session = ChatSession(
                config=self.config,
                save_history=self.config.save_history,
                history_file=self.config.history_file,
            )

            self.formatter.display_info("✅ Evernote Agent initialized")
            return True

        except Exception as e:
            self.formatter.display_error(e, "initialization")
            return False

    async def run_interactive(self) -> None:
        """Run the interactive chat session."""
        # Create MCP server once for the entire session
        mcp_server = _create_evernote_mcp_server(self.config.container_name)

        # Use async context manager for MCP server lifecycle
        async with mcp_server as server:
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

                    # Process the query (agent will handle adding messages)
                    await self._process_query(user_input, server)

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
        # Create MCP server for single query
        mcp_server = _create_evernote_mcp_server(self.config.container_name)

        # Use async context manager for MCP server lifecycle
        async with mcp_server as server:
            try:
                await self._process_query(query, server)
            except Exception as e:
                self.formatter.display_error(e, "query execution")
                sys.exit(1)

    async def _process_query(self, query: str, mcp_server) -> None:
        """Process a user query using the AI agent."""
        try:
            # Show thinking indicator
            self.console.print("\n[bold cyan]🤖 Agent:[/bold cyan]", end=" ")

            # Get conversation history in the format expected by the agent
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.session.messages
            ]

            # Run the agent with streaming
            response_text, updated_history = await run_evernote_agent_interactive(
                mcp_server=mcp_server,
                user_input=query,
                conversation_history=conversation_history
            )

            # Sync session with updated history from agent
            # The agent added user and assistant messages, we need to add them to session properly
            from datetime import datetime

            # Find new messages (those not in session yet)
            num_existing = len(self.session.messages)
            new_messages = updated_history[num_existing:]

            # Add new messages to session with proper timestamps
            for msg in new_messages:
                if msg["role"] == "user":
                    self.session.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self.session.add_assistant_message(msg["content"])

        except Exception as e:
            import traceback
            print("\nDEBUG: Full error traceback:")
            traceback.print_exc()
            self.formatter.display_error(e, "agent query processing")


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
        # MCP server cleanup is handled automatically by Runner/Agents SDK
        pass


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