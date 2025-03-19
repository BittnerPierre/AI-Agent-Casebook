import asyncio
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from llama_index.core import Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding

from ai_agents import RAGAgentFactory, RAGAgentType
from core.base import SupportedModel
from core.commons import initiate_model, initiate_embeddings
from video_script.assistant import _format_chapters
from video_script.state import VideoScriptState

model = initiate_model(SupportedModel.DEFAULT)
embeddings = initiate_embeddings(SupportedModel.DEFAULT)

multi_source_paths = [
    Path("../data/documents/evaluation/Agents.pdf"),
    Path("../data/documents/evaluation/Building_effective_agents.pdf"),
    Path("../data/documents/evaluation/Chat_Bot_Evaluation.pdf"),
    Path("../data/documents/evaluation/Chat_Bot_Benchmarking.pdf"),
]


kwargs = {
    "model": model,
    "embeddings": embeddings,
    "source_paths": multi_source_paths
}

research_agent = RAGAgentFactory.create_agent(RAGAgentType.MULTI_DOCUMENT, **kwargs)


def format_topics_as_bullets(topics: list[str]) -> str:
    """
    Format a list of chapter topics as a nicely structured bullet-point list.
    """
    return "\n".join(f"- {topic}" for topic in topics)


async def research_node2(state: VideoScriptState) -> VideoScriptState:
    """
    The Researcher provides factual data/ideas for the current chapter.
    For demonstration, we just append a dummy 'AIMessage' with bullet points.
    """
    chapter = state["chapters"][state["current_chapter"]]
    chapter_title = chapter[0]
    chapter_topics = format_topics_as_bullets(chapter[1])
    message_content = (
        f"Provide research for '{chapter_title}':\n"
        f"Covered topics:\n{chapter_topics}"
    )
    state["messages"].append(HumanMessage(content=message_content, name="user"))
    # last_message = state["messages"][-1]
    # res = await research_agent.runnable.ainvoke(input={message_content})
    res = research_agent.invoke(message_content)
    print(f"Response: '{res}'")
    # last_message = res["messages"][-1]
    last_message = res
    # content = f"# Research for {chapter[0]}\n\n{last_message['research']}\n\n-----\n\n# Researcher Comment\n\n{last_message['comment']}"
    content = f"# Research for {chapter[0]}\n\n{last_message}"
    state["messages"].append(AIMessage(content=content, name="researcher"))
    return state

from video_script.assistant import planning_node

#
# 4. Build the Graph
#
workflow = StateGraph(VideoScriptState)

# NODES
workflow.add_node("planning", planning_node)
workflow.add_node("research", research_node2)


# EDGES
workflow.add_edge(START, "planning")
workflow.add_edge("planning", "research")
workflow.add_edge("research", END)

# Compile the graph
memory = MemorySaver()
research_app = workflow.compile(checkpointer=memory)

#
# 5. Usage Example
#
# In real usage, you'd pass user messages or stored conversation. For now, we just pass empty messages to start.
#
example_input = {
    "messages": [HumanMessage(content="I'd like a 3-chapter video of 3 minutes of 300 words on 'AI Agent Evaluation."
                                      " , please!")],
    "chapters": [],         # or we let the planning node define them
    "current_chapter": 0,   # start at chapter 0
    "final_script": ""      # empty at the start
}

# Example of running the flow (asynchronously).


async def main():  # Define an async function
    config = {"recursion_limit": 40,
              "configurable": {"thread_id": "1"}}

    async for step in research_app.astream(example_input, config=config):
        print(step)
        print("----")

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function