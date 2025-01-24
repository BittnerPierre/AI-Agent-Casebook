import asyncio
from pathlib import Path
from typing import List, Tuple, Union, Literal, Annotated

from dotenv import load_dotenv, find_dotenv
from llama_index.core import Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding
from typing_extensions import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END
)
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain import hub

from agents import RAGAgentFactory, RAGAgentType
from core.commons import initiate_model, initiate_embeddings
from core.base import SupportedModel

from langgraph.managed.is_last_step import RemainingSteps

MIN_REMAINING_STEP = 3
MAX_REVISION = 2


def load_guidelines():
    try:
        with open("script_guidelines.md", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "No guidelines available."


script_guidelines = load_guidelines()

llm = initiate_model(SupportedModel.DEFAULT)

team = "small video editing team for Youtube channels"

#
# 1. AGENT PROMPTS
#
# We define separate prompt templates or system messages for each role:
# - Host/Producer (agenda + final approval)
# - Researcher (fact-checking, references)
# - Writer (drafting)
# - Reviewer or Reflection (feedback on the script)
#

##############
# PRODUCER   #
##############


class Chapter(TypedDict):
    title: str
    covered_topics: List[str]


class Planning(TypedDict):
    topic: str
    plan: List[Chapter]


producer_prompt = hub.pull("video-script-producer-prompt")

plan_video = producer_prompt | llm.with_structured_output(Planning)


class Approval(TypedDict):
    status: Literal['approved', 'revised']


approve_video = producer_prompt | llm.with_structured_output(Approval)


##############
# RESEARCHER #
##############


class ResearchChapter(TypedDict):
    research: str
    comment: str


researcher_prompt = hub.pull("video-script-researcher-prompt")

research = researcher_prompt | llm.with_structured_output(ResearchChapter)

##############
# WRITER     #
##############


class DraftChapter(TypedDict):
    chapter: str
    comment: str


writer_prompt = hub.pull("video-script-writer-prompt")

write = writer_prompt | llm.with_structured_output(DraftChapter)


##############
# REVIEWER   #
##############

class ReviewFeedback(TypedDict):
    GoodPoints: str
    MissingOrNeedsResearch: str
    SuperfluousContent: str
    StyleRefinement: str
    NextNode: Literal['research', 'writer', 'approved']


review_prompt = hub.pull("video-script-reviewer-prompt")

review = review_prompt | llm.with_structured_output(ReviewFeedback)

####################
# GRAPH DEFINITION #
####################

# We'll store the conversation state in "messages" to pass from node to node.
# Additional fields: "chapters", "current_chapter", "final_script", etc.


#
# 1. Define the state of the graph
#
class VideoScriptState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Conversation so far
    chapters: List[Chapter]       # The list of chapters or topics
    current_chapter: int         # Index of the chapter we're working on
    final_script: str            # The aggregated script as we finalize each chapter
    chapter_versions: List[str]  # Partial or final versions of chapters
    feedbacks: List[str]          # List to hold feedback for each chapter
    next_node: Literal['research', 'writer', 'approved']
    revisions: List[int]
    remaining_steps: RemainingSteps


def _parse_chapters_from_response(response: str) -> List[Tuple[str, List[str]]]:
    # Extract the title and subchapters for each chapter
    chapters = [(chapter['title'], chapter['covered_topics']) for chapter in response]
    return chapters


def _format_chapters(chapters):
    formatted_chapters = ""
    for chapter, topics in chapters:
        formatted_chapters += f"{chapter}:\n"
        for topic in topics:
            formatted_chapters += f"  - {topic}\n"
        formatted_chapters += "\n"
    return formatted_chapters


#
# 2. Define Node
#
async def planning_node(state: VideoScriptState) -> VideoScriptState:
    """
    The Host/Producer sets the plan (how many chapters, the overall direction).
    In a real scenario, you'd call host_producer_prompt with the user request to produce an agenda.
    We'll simulate it here.
    """
    # If not already done, let's define chapters in the conversation or from user input
    # Example simulation: The user wants a 3-chapter video, so we store that:
    if not state.get("chapters"):
        res = await plan_video.ainvoke(input={"messages": state["messages"], "team": team})
        chapters = _parse_chapters_from_response(res['plan'])
        state["chapters"] = chapters
        state["current_chapter"] = 0
        state["chapter_versions"] = [""] * len(chapters)
        state["final_script"] = ""
        state["feedbacks"] = [""] * len(chapters)
        state["revisions"] = [0] * len(chapters)
        formatted_chapters = _format_chapters(chapters)
        producer_message = (f"Great!"
                            f" Here's a suggested agenda for your {len(chapters)}-chapter video on {res['topic']}."
                            f"\n\n{formatted_chapters}")
        host_message = AIMessage(content=producer_message, name="host-producer")
        state["messages"].append(host_message)
    return state


async def research_node(state: VideoScriptState) -> VideoScriptState:
    """
    The Researcher provides factual data/ideas for the current chapter.
    For demonstration, we just append a dummy 'AIMessage' with bullet points.
    """
    chapter = state["chapters"][state["current_chapter"]]
    state["messages"].append(HumanMessage(content=f"Provide research for '{chapter[0]}'", name="user"))
    res = await research.ainvoke(input={"messages": state["messages"], "team": team})
    content = f"# Research for {chapter[0]}\n\n{res['research']}\n\n-----\n\n# Researcher Comment\n\n{res['comment']}"
    state["messages"].append(AIMessage(content=content, name="researcher"))
    return state


async def writer_node(state: VideoScriptState) -> VideoScriptState:
    """
    The Writer composes or updates the script for the current chapter using the research input.
    """
    chapter = state["chapters"][state["current_chapter"]]
    state["messages"].append(HumanMessage(content=f"Draft the script for chapter '{chapter[0]}'", name="user"))
    # text = f"Writer: Here is a draft for {chapter}, integrating research bullet points..."
    res = await write.ainvoke(input={"messages": state["messages"],
                                     "team": team,
                                     "script_guidelines": script_guidelines
                                     })
    content = f"# Draft for {chapter[0]}\n\n{res['chapter']}\n\n-----\n\n# Writer Comment\n\n{res['comment']}"
    state["messages"].append(AIMessage(content=content, name="writer"))
    state["chapter_versions"][state["current_chapter"]] = res['chapter']
    return state


# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
members = ["research", "writer"]
options = members + ["approved"]


async def review_node(state: VideoScriptState) -> VideoScriptState:
    """
    The Host/Producer (or separate 'Reviewer' agent) checks the current draft:
      - If acceptable, we finalize the chapter.
      - If not acceptable, we request changes => 'draft_node' or 'research_node' again.
    For simplicity, we'll auto-approve or auto-reject randomly or by example logic.
    """
    chapter = state["chapters"][state["current_chapter"]]
    revision = state["revisions"][state["current_chapter"]] + 1
    state["messages"].append(HumanMessage(content=f"Review the draft for chapter '{chapter[0]}'", name="user"))

    res = await review.ainvoke(input={"messages": state["messages"],
                                      "team": team,
                                      "script_guidelines": script_guidelines
                                      })
    # review_feedback = res.content
    feedback_message = (
        f"# Feedback for {chapter[0]}\n\n"
        f"Good Points:\n {res['GoodPoints']}\n\n"
        f"Missing or Needs Research:\n {res['MissingOrNeedsResearch']}\n\n"
        f"Superfluous Content:\n {res['SuperfluousContent']}\n\n"
        f"Style Refinement:\n {res['StyleRefinement']}\n\n"
        f"NextNode: {res['NextNode']}\n\n"
        f"Revision: {revision}\n\n"
    )

    # Append the feedback to the state
    state["feedbacks"][state["current_chapter"]] = feedback_message
    state["messages"].append(HumanMessage(content=feedback_message, name="reviewer"))
    state["revisions"][state["current_chapter"]] = revision
    state["next_node"] = res["NextNode"]

    if (state["next_node"] == "approved") or (revision >= MAX_REVISION):
        # Append the last writer message to the final script and proceed.
        writer_msg = state["chapter_versions"][state["current_chapter"]]
        state["final_script"] += f"\n\n{writer_msg}"
        state["current_chapter"] += 1

    return state


#
# 3. Condition to see if we should loop or end
#
async def should_next_chapter(state: VideoScriptState) -> Literal["research", "writer", END]:
    """
    If there's another chapter left, return 'research' to gather new facts for the next chapter.
    Otherwise, 'END' if the entire script is complete.
    """
    if state["remaining_steps"] <= MIN_REMAINING_STEP:
        return END

    next_idx = state["current_chapter"]
    if next_idx >= len(state["chapters"]):
        return END
    else:
        revision = state["revisions"][state["current_chapter"]]
        if revision >= MAX_REVISION:
            return "research"

        state["messages"].append(HumanMessage(content="Do you approve the draft for the last chapter?", name="user"))
        try:
            res = await approve_video.ainvoke(input={"messages": state["messages"], "team": team})
        except Exception as e:
            # Handle the exception appropriately
            print(f"Error invoking approve_video: {e}")
            return state["next_node"]

        if res['status'] != 'approved':
            return state["next_node"]
        else:
            return "research"


#
# 4. Build the Graph
#
workflow = StateGraph(VideoScriptState)

# NODES
workflow.add_node("planning", planning_node)
workflow.add_node("research", research_node)
workflow.add_node("writer", writer_node)
workflow.add_node("review", review_node)

# EDGES
workflow.add_edge(START, "planning")
workflow.add_edge("planning", "research")
workflow.add_edge("research", "writer")
workflow.add_edge("writer", "review")

# After reviewing a chapter, decide if we do the next chapter or end.
workflow.add_conditional_edges("review", should_next_chapter, ["research", "writer", END])

# Compile the graph
memory = MemorySaver()
video_script_app = workflow.compile(checkpointer=memory)

#
# 5. Usage Example
#
# In real usage, you'd pass user messages or stored conversation. For now, we just pass empty messages to start.
#
example_input = {
    "messages": [HumanMessage(
        content="I'd like a 3-chapter video of 3 minutes of 300 words on 'AI Won't Take Your Jobs."
                " Those Who Use AI Will!', please!")],
    "chapters": [],         # or we let the planning node define them
    "current_chapter": 0,   # start at chapter 0
    "final_script": ""      # empty at the start
}

# Example of running the flow (asynchronously).


async def main():  # Define an async function
    config = {"recursion_limit": 40,
              "configurable": {"thread_id": "1"}}

    async for step in video_script_app.astream(example_input, config=config):
        print(step)
        print("----")

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function
