import asyncio
import logging
import argparse
import importlib
import os.path
from pathlib import Path

from .agentic_manager import ResearchManager as AgenticResearchManager
from .manager import ResearchManager as StandardResearchManager
from .config import get_config
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings
# LangSmith tracing support
from agents import set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from openai import OpenAI
from .agents.utils import get_vector_store_id_by_name
from .agents.schemas import ResearchInfo

def get_manager_class(manager_path: str):
    """Dynamically import and return a manager class from a path string."""
    if not manager_path or "." not in manager_path:
        # Default managers
        if manager_path == "agentic_manager":
            return AgenticResearchManager
        elif manager_path == "manager":
            return StandardResearchManager
        else:
            raise ValueError(f"Unknown manager: {manager_path}")
    
    # For custom managers with format like "module.ClassName"
    module_path, class_name = manager_path.rsplit(".", 1)
    module = importlib.import_module(f".{module_path}", package="src")
    return getattr(module, class_name)


async def main() -> None:
    # Configure logging and get config first
    config = get_config()
    logging.basicConfig(level=getattr(logging, config.logging.level), format=config.logging.format)
    logger = logging.getLogger(__name__)
    
    # Get default manager from config
    default_manager = config.manager.default_manager
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agentic Research CLI")
    parser.add_argument("--syllabus", type=str, help="Path to a syllabus file")
    parser.add_argument("--manager", type=str, default=default_manager, 
                        help=f"Manager implementation to use (default: {default_manager})")
    parser.add_argument("--query", type=str, help="Research query (alternative to interactive input)")
    parser.add_argument("--vector-store", type=str, help="Name of the vector store to use (overrides config)")
    args = parser.parse_args()

    # Override vector store name if provided
    if args.vector_store:
        logger.info(f"Using custom vector store: {args.vector_store}")
        config.vector_store.name = args.vector_store

    # Get the appropriate manager class
    manager_class = get_manager_class(args.manager)
    
    # Get input: either from syllabus file, command line argument, or interactive input
    if args.syllabus:
        syllabus_path = Path(args.syllabus)
        if not syllabus_path.exists():
            logger.error(f"Syllabus file not found: {args.syllabus}")
            return
        
        with open(syllabus_path, 'r', encoding='utf-8') as f:
            syllabus_content = f.read()
            query = ("Prépare un rapport de recherche complet et bien structuré permettant de rédiger un support de formation sur les sujets suivants:\n"
                    f"<syllabus>\n{syllabus_content}\n</syllabus>")
        logger.info(f"Using syllabus from file: {args.syllabus}")
    elif args.query:
        query = args.query
    else:
        query = input("What would you like to research? ")

    set_trace_processors([OpenAIAgentsTracingProcessor()])

    async with MCPServerSse(
        name="SSE Dataprep Server",
        params={
            "url": "http://localhost:8001/sse",
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="SSE Example", trace_id=trace_id):
            client = OpenAI()
            vector_store_name = config.vector_store.name    
            vector_store_id = get_vector_store_id_by_name(client, vector_store_name)
            research_info = ResearchInfo(vector_store_name=vector_store_name, vector_store_id=vector_store_id)
            if vector_store_id is None:
                vector_store_obj = client.vector_stores.create(
                    name=vector_store_name
                )
                vector_store_id = vector_store_obj.id
                config.vector_store.vector_store_id = vector_store_id
                print(f"Vector store created: {vector_store_id}")
            else:
                print(f"Vector store already exists: {vector_store_id}")
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await manager_class().run(server, query, research_info)
   
def cli_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()
