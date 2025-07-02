import asyncio
import logging

from .agentic_manager import ResearchManager
from .config import get_config


config = get_config()
logging.basicConfig(level=getattr(logging, config.logging.level), format=config.logging.format)
logger = logging.getLogger(__name__)

async def main() -> None:
    query = input("What would you like to research? ")
    await ResearchManager().run(query)


def cli_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()
