"""Main entry point for Evernote Chatbot CLI."""

import asyncio
import sys

from .interactive_cli import ChatbotCLI
from .config import ChatbotConfig


def main() -> None:
    """Main entry point for the CLI application."""
    # For now, use default config and interactive mode
    config = ChatbotConfig.from_env()
    cli = ChatbotCLI(config)

    async def run():
        try:
            if await cli.initialize():
                await cli.run_interactive()
        finally:
            await cli.cleanup()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()