import asyncio
import logging
import argparse
import importlib
import os.path  
from pathlib import Path
import tempfile

from .agentic_manager import ResearchManager as AgenticResearchManager
from .manager import ResearchManager as StandardResearchManager
from .config import get_config
from agents import Agent, Runner, add_trace_processor
from agents.mcp import MCPServerSse, MCPServerStdio  
from agents.model_settings import ModelSettings
# LangSmith tracing support
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from openai import OpenAI
from .agents.utils import get_vector_store_id_by_name
from .agents.schemas import ResearchInfo
from .tracing.trace_processor import FileTraceProcessor


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

    os.environ['OPENAI_AGENTS_DISABLE_TRACING'] = '1'

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
    parser.add_argument("--vector-store", type=str, help="Name of the vector store to use (overrides config)", default=config.vector_store.name)
    parser.add_argument("--max-search-plan", type=str, default=config.agents.max_search_plan,
                        help=f"Maximum number of search plans to generate (default: {config.agents.max_search_plan})") 
    parser.add_argument("--output-dir", type=str, default=config.agents.output_dir,
                        help=f"Output directory (default: {config.agents.output_dir})")
    parser.add_argument("--debug", action="store_true", default=config.debug.enabled,
                        help=f"Debug mode (default: {config.debug.enabled})")
    args = parser.parse_args()

    # Override vector store name if provided
    if args.vector_store:
        config.vector_store.name = args.vector_store
        logger.info(f"Using custom vector store name: {args.vector_store}")

    # Get the appropriate manager class
    manager_class = get_manager_class(args.manager)
    
    if args.max_search_plan:
        config.agents.max_search_plan = args.max_search_plan
        logger.info(f"Using custom max search plan: {args.max_search_plan}")

    if args.output_dir:
        config.agents.output_dir = args.output_dir
        logger.info(f"Using custom output directory: {args.output_dir}")
        if not os.path.exists(config.agents.output_dir):
            os.makedirs(config.agents.output_dir)

    if args.debug:
        config.debug.enabled = args.debug
        logger.info(f"Using custom debug mode: {args.debug}")

    # Get input: either from syllabus file, command line argument, or interactive input
    if args.syllabus:
        syllabus_path = Path(args.syllabus)
        if not syllabus_path.exists():
            logger.error(f"Syllabus file not found: {args.syllabus}")
            return
        
        with open(syllabus_path, 'r', encoding='utf-8') as f:
            syllabus_content = f.read()
            query = (f"<syllabus>\n{syllabus_content}\n</syllabus>")
        logger.info(f"Using syllabus from file: {args.syllabus}")
    elif args.query:
        query = args.query
    else:
        query = input("What would you like to research? ")

    # add_trace_processor(OpenAIAgentsTracingProcessor())
    add_trace_processor(FileTraceProcessor(log_dir="traces", log_file="trace.log"))
    debug_mode = config.debug.enabled

    with tempfile.TemporaryDirectory(delete=not debug_mode) as temp_dir:
        fs_server = MCPServerStdio(
            name="FS_MCP_SERVER",
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", temp_dir],
            },
        )
        canonical_tmp_dir = os.path.realpath(temp_dir)

        dataprep_server = MCPServerSse(
            name="DATAPREP_MCP_SERVER",
            params={
                "url": "http://localhost:8001/sse",
            },
        )
        async with fs_server, dataprep_server:
            # trace_id = gen_trace_id()
            #with trace(workflow_name="SSE Example", trace_id=trace_id):
            client = OpenAI()
            vector_store_id = get_vector_store_id_by_name(client, config.vector_store.name)
            if vector_store_id is None:
                vector_store_obj = client.vector_stores.create(
                    name=config.vector_store.name
                )
                config.vector_store.vector_store_id = vector_store_obj.id
                print(f"Vector store created: '{config.vector_store.vector_store_id}'")
            else:
                config.vector_store.vector_store_id = vector_store_id
                print(f"Vector store already exists: '{config.vector_store.vector_store_id}'")

            research_info = ResearchInfo(
                vector_store_name=config.vector_store.name,
                vector_store_id=config.vector_store.vector_store_id,
                temp_dir=canonical_tmp_dir,
                max_search_plan=config.agents.max_search_plan,
                output_dir=config.agents.output_dir)
            
            # print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await manager_class().run(dataprep_server=dataprep_server, fs_server=fs_server, query=query, research_info=research_info)

def cli_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()
