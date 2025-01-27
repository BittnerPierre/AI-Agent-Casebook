import asyncio
from pathlib import Path
from typing import List, Tuple, Union, Literal, Annotated

from dotenv import load_dotenv, find_dotenv
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
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

from core.logger import logger

MIN_REMAINING_STEP = 3
MAX_REVISION = 1

# TODO SHOULD BE OUTSIDE CODEBASE AND MANAGE IN CONFIG
GUIDELINE_FILENAME = "app/video_script/script_guidelines.md"

def load_guidelines():
    try:
        with open(GUIDELINE_FILENAME, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"No guidelines available {GUIDELINE_FILENAME}.")
        return "No guidelines available."


script_guidelines = load_guidelines()

llm = initiate_model(SupportedModel.GPT_4_O)

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

researcher = researcher_prompt | llm.with_structured_output(ResearchChapter)

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
    NextNode: Literal['researcher', 'writer', 'approved']


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
    messages: Annotated[List[BaseMessage], add_messages]
    chapters: List[Chapter]
    current_chapter_index: int
    current_chapter_content: str
    current_chapter_feedback: str
    current_chapter_revision: int
    final_script: str
    next_node: Literal['researcher', 'writer', 'approved']
    remaining_steps: RemainingSteps


#####################
# TOOLING
#####################


def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next and give your motivation. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]
        motivation: str

    def supervisor_node(state: VideoScriptState) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        motivation = response["motivation"]

        if goto == "FINISH":
            goto = END

        return Command(goto=goto,
                       update={"next_node": goto,
                               "messages": [HumanMessage(content=motivation, name="supervisor")]}
                       )

    return supervisor_node


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


# def _move_to_next_chapter(state: VideoScriptState):
#     state["current_chapter_index"] += 1
#     state["current_chapter_content"] = ""
#     state["current_chapter_feedback"] = ""
#     state["current_chapter_revision"] = 0
#     print(f"_move_to_next_chapter: {state["current_chapter_index"]}")


#####################
# NODE DEFINITION
#####################

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
        state["current_chapter_index"] = 0
        state["current_chapter_content"] = ""
        state["current_chapter_feedback"] = ""
        state["current_chapter_revision"] = 0
        # state["current_chapter"] = 0
        # state["chapter_versions"] = [""] * len(chapters)
        # state["final_script"] = ""
        # state["feedbacks"] = [""] * len(chapters)
        # state["revisions"] = [0] * len(chapters)
        formatted_chapters = _format_chapters(chapters)
        producer_message = (f"Great!"
                            f" Here's a suggested agenda for your {len(chapters)}-chapter video on {res['topic']}."
                            f"\n\n{formatted_chapters}")
        host_message = HumanMessage(content=producer_message, name="host-producer")
        state["messages"].append(host_message)
    return state


async def researcher_node(state: VideoScriptState) -> Command[Literal["writer"]]:
    """
    The Researcher provides factual data/ideas for the current chapter.
    For demonstration, we just append a dummy 'AIMessage' with bullet points.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter[0]
    message_content = f"Provide research for '{chapter_title}'"
    human_message = HumanMessage(content=message_content, name="user")
    messages = state["messages"] + [human_message]
    res = await researcher.ainvoke(input={"messages": messages, "team": team})
    research_response_comment = res.get('comment', 'No comment provided.')
    research_chapter_content = res['research']
    research_message_content = (f"# Research for {chapter_title}"
                                f"\n\n{research_chapter_content}"
                                f"\n\n-----\n\n# Researcher Comment"
                                f"\n\n{research_response_comment}")

    return Command(
        update={
            "messages": [HumanMessage(content=research_message_content, name="researcher")]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="writer",
    )


async def writer_node(state: VideoScriptState) -> Command[Literal["reviewer"]]:
    """
    The Writer composes or updates the script for the current chapter using the research input.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter[0]
    message_content = f"Draft the script for chapter '{chapter[0]}'"
    human_message = HumanMessage(content=message_content, name="user")
    # text = f"Writer: Here is a draft for {chapter}, integrating research bullet points..."
    messages = state["messages"] + [human_message]

    res = await write.ainvoke(input={"messages": messages,
                                     "team": team,
                                     "script_guidelines": script_guidelines
                                     })
    # Check if 'comment' is in the response
    writer_chapter_content = res['chapter']
    writer_response_comment = res.get('comment', 'No comment provided.')

    writer_message_content = (f"# Draft for {chapter_title}"
                              f"\n\n{writer_chapter_content}\n\n-----"
                              f"\n\n# Writer Comment"
                              f"\n\n{writer_response_comment}")

    # state["messages"].append(AIMessage(content=content, name="writer"))
    # state["chapter_versions"][state["current_chapter"]] = res['chapter']
    return Command(
        update={
            "messages": [HumanMessage(content=writer_message_content, name="writer")]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="reviewer",
    )


async def reviewer_node(state: VideoScriptState) -> Command[Literal["supervisor"]]:
    """
    The 'Reviewer' agent checks the current draft:
      - If acceptable, we finalize the chapter.
      - If not acceptable, we request changes => 'draft_node' or 'researcher_node' again.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter[0]
    revision = state["current_chapter_index"]
    human_message = HumanMessage(content=f"Review the draft for chapter '{chapter_title}'", name="user")
    messages = state["messages"] + [human_message]

    res = await review.ainvoke(input={"messages": messages,
                                      "team": team,
                                      "script_guidelines": script_guidelines
                                      })
    # review_feedback = res.content
    reviewer_message_content = (
        f"# Feedback for {chapter_title}\n\n"
        f"Good Points:\n {res['GoodPoints']}\n\n"
        f"Missing or Needs Research:\n {res['MissingOrNeedsResearch']}\n\n"
        f"Superfluous Content:\n {res['SuperfluousContent']}\n\n"
        f"Style Refinement:\n {res['StyleRefinement']}\n\n"
        f"NextNode: {res['NextNode']}\n\n"
        f"Revision: {revision}\n\n"
    )

    # Append the feedback to the state
    # state["feedbacks"][state["current_chapter"]] = feedback_message
    # state["messages"].append(HumanMessage(content=feedback_message, name="reviewer"))
    # state["revisions"][state["current_chapter"]] = revision

    return Command(
        update={
            "messages": [HumanMessage(content=reviewer_message_content, name="reviewer")],
            "next_node": res["NextNode"]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )



# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
members = ["researcher", "writer", "reviewer"]
# options = members + ["approved"]


async def approval_node(state: VideoScriptState) -> Command[Literal[*members, END]]:
    current_chapter = state["current_chapter_index"]
    revision_count = state["current_chapter_revision"]
    messages = state["messages"]
    print(f"***** approval_node STEP 1 chapter='{current_chapter}', revision='{revision_count}', members='{members}")
    # Check if maximum revisions have been reached
    if revision_count >= MAX_REVISION:
        message = ("Maximum revisions reached for this chapter."
                   "Moving to next chapter or ending workflow.")
        # goto = state["next_node"] if state["next_node"] == "writer" else "researcher"
        goto = "researcher"
        current_chapter += 1  # Move to next chapter
        revision_count = 0
        #_move_to_next_chapter(state)
        #     state["current_chapter_index"] += 1
        #     state["current_chapter_content"] = ""
        #     state["current_chapter_feedback"] = ""
        #     state["current_chapter_revision"] = 0
        print(f"***** approval_node STEP 2 (MAX_REVISION) chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")

    else:
        if revision_count == 0:
            goto = "researcher"
            message = "Let's make it, Team!"
            revision_count += 1  # Increment the revision count
            print(f"***** approval_node STEP 5 FIRST REVISION chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
        else:
            messages += [HumanMessage(content="Do you approve the draft for the last chapter?", name="host-producer")]
            try:
                res = await approve_video.ainvoke(input={"messages": messages, "team": team})

                if res['status'] != 'approved':
                    goto = state["next_node"]
                    message = f"Revisions needed. Returning to the {goto}."
                    revision_count += 1  # Increment the revision count
                else:
                    message = "Chapter approved. Moving to next."
                    #current_chapter += 1
                    goto = "researcher"
                    current_chapter += 1  # Move to next chapter
                    revision_count = 0
                    #_move_to_next_chapter(state)

                print(f"***** approval_node STEP 3 {res['status']} chapter='{current_chapter}',"
                      f" revision='{revision_count}', goto='{goto}'")

            except Exception as e:
                # Handle the exception appropriately
                print(f"Error invoking approve_video: {e}")
                goto = END

        print(f"***** approval_node STEP 4 (conclusion) chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
    return Command(
        update={
            "messages": HumanMessage(content=message, name="host-producer"),
            "next_node": "researcher" if goto == END else goto,
            "current_chapter_index": current_chapter,
            "current_chapter_revision": revision_count
        },
        goto=goto,
    )


script_writing_supervisor_node = make_supervisor_node(
    llm, members=members
)


#
# 3. Condition to see if we should loop or end
#
async def _should_next_chapter(state: VideoScriptState) -> Literal[*members, END]:
    """
    If there's another chapter left, return 'researcher' to gather new facts for the next chapter.
    Otherwise, 'END' if the entire script is complete.
    """
    print(f"*****_should_next_chapter STEP 1 remaining_steps='{state["remaining_steps"]}',"
          f" chapter_index='{state["current_chapter_index"]}', members='{members}")
    if state["remaining_steps"] <= MIN_REMAINING_STEP:
        return END

    next_idx = state["current_chapter_index"]
    chapter_length = len(state["chapters"])
    if next_idx >= chapter_length:
        print(
            f"*****_should_next_chapter STEP 2 current_chapter_index='{next_idx}' >= {chapter_length} 'END'")
        return END
    else:
        goto = state["next_node"]
        print(
            f"*****_should_next_chapter STEP 3 current_chapter_index='{next_idx}' < {chapter_length} '{goto}'")
        return goto


def create_video_script_agent() -> CompiledStateGraph:
    """
    Build and Compile the Video Script Graph
    """
    workflow = StateGraph(VideoScriptState)

    # NODES
    workflow.add_node("planning", planning_node)
    workflow.add_node("supervisor", approval_node)  # script_writing_supervisor_node
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("reviewer", reviewer_node)

    # EDGES
    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "supervisor")
    # workflow.add_edge("research", "writer")
    # workflow.add_edge("writer", "review")

    # workflow.add_edge("review", "supervisor")

    # After reviewing a chapter, decide if we do the next chapter or end.
    workflow.add_conditional_edges("supervisor",
                                   _should_next_chapter, ["researcher", 'writer', 'reviewer', END])

    # Compile the graph
    memory = MemorySaver()
    video_script_app = workflow.compile(checkpointer=memory)
    return video_script_app

