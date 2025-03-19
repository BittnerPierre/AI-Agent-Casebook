
import asyncio
import os

from core.base import SupportedModel
from core.commons import initiate_embeddings
from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import WebBaseLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from semantic_search.core import VectorStoreManager
from video_script.assistant import create_video_script_agent

from agents import set_default_openai_key, set_tracing_export_api_key
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
set_default_openai_key(OPENAI_API_KEY)

set_tracing_export_api_key(OPENAI_API_KEY)

# Example of running the flow (asynchronously).
async def main():  # Define an async function



    #
    # Usage Example
    #
    # In real usage, you'd pass user messages or stored conversation. For now, we just pass empty messages to start.
    #
    config = {"recursion_limit": 99,
              "configurable": {"thread_id": "1"}}
    
    # embeddings = initiate_embeddings(SupportedModel.DEFAULT)
    # search = SemanticSearchFactory.create_strategy(
    #     SearchStrategyType.SIMPLE_VECTOR,
    #     embeddings,
    #     kwargs={"collection_name", "simple-vector-store"}
    # )
    # VectorStoreManager(search)

    video_script_app = create_video_script_agent()

    urls = [
        "https://huyenchip.com//2025/01/07/agents.html",
        "https://www.anthropic.com/engineering/building-effective-agents",
        "https://docs.smith.langchain.com/evaluation/concepts",
        "https://docs.smith.langchain.com/evaluation/tutorials/agents",
    ]

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )
    doc_splits = text_splitter.split_documents(docs_list)

    search = VectorStoreManager.get_strategy()

    search.add_documents(doc_splits)

    prompt = ("I'd like a short video of 3 minutes (450 words) on 'AI Agents Evaluation'.")

    example_input = {
        "messages": [HumanMessage(
            content=prompt)],
        # "chapters": [],         # or we let the planning node define them
        # "current_chapter": 0,   # start at chapter 0
        "final_script": ""  # empty at the start
    }

    # Collect all steps from the astream generator and print each step
    steps = []
    async for step in video_script_app.astream(example_input, config=config, stream_mode="values"):
        steps.append(step)
        print(f"Step: {step}")

    # Access the last step
    last_step = steps[-1]

    print(f"Directive: '{prompt}'")

    # Print the last message of the last step
    last_message = last_step["messages"][-1]

    output = last_message.pretty_repr()
    print(f"Result: '{output}'")

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function
