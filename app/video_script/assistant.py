
from typing import Literal, Optional

from langchain import hub
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import (
    StateGraph,
    START,
    END
)
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, RetryPolicy

from core.base import SupportedModel
from core.commons import initiate_model
from core.logger import logger
from video_script.agents import Planner, Supervisor, Researcher, Writer, Reviewer
from video_script.configuration import Configuration
from video_script.state import VideoScriptState, InputState
from httpx import ReadTimeout

worker_llm = initiate_model(SupportedModel.MISTRAL_SMALL, tags=["worker"])
producer_llm = initiate_model(SupportedModel.MISTRAL_SMALL, tags=["producer"])

# TODO SHOULD BE OUTSIDE CODEBASE AND MANAGE IN CONFIG
SCRIPT_GUIDELINES_FILENAME = "app/video_script/script_guidelines.md"
STORYTELLING_GUIDEBOOK_FILENAME = "app/video_script/storytelling_guidebook.md"

def load_script_guidelines():
    try:
        with open(SCRIPT_GUIDELINES_FILENAME, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"No guidelines available {SCRIPT_GUIDELINES_FILENAME}.")
        return "No script guidelines available."


def load_storytelling_guidebook():
    try:
        with open(STORYTELLING_GUIDEBOOK_FILENAME, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"No guidelines available {STORYTELLING_GUIDEBOOK_FILENAME}.")
        return "No storytelling guidebook available."


script_guidelines = load_script_guidelines()
storytelling_guidebook = load_storytelling_guidebook()


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

planner = Planner(model=producer_llm)

supervisor = Supervisor(model=producer_llm)

##############
# RESEARCHER #
##############

researcher = Researcher(model=worker_llm)

##############
# WRITER     #
##############

writer = Writer(model=worker_llm)

##############
# REVIEWER   #
##############

reviewer = Reviewer(model=worker_llm)


####################
# GRAPH DEFINITION #
####################

# We'll store the conversation state in "messages" to pass from node to node.
# Additional fields: "chapters", "current_chapter_XXX", "final_script", etc.

#
# 1. Define the state of the graph
#


#####################
# TOOLING
#####################

def _format_chapters(chapters):
    formatted_chapters = ""
    for chapter in chapters:
        formatted_chapters += f"{chapter['title']}:\n"
        if 'chapter_brief' in chapter:
            formatted_chapters += f"  - Brief: {chapter['chapter_brief']}\n"
        formatted_chapters += "  - Covered Topics:\n"
        for topic in chapter['covered_topics']:
            formatted_chapters += f"    - {topic}\n"
        formatted_chapters += "\n"
    return formatted_chapters


#####################
# NODE DEFINITION
#####################

#
# 2. Define Node
#
async def planning_node(state: VideoScriptState, config: RunnableConfig) -> VideoScriptState:
    """
    The Host/Producer sets the plan (how many chapters, the overall direction).
    In a real scenario, you'd call host_producer_prompt with the user request to produce an agenda.
    We'll simulate it here.
    """
    # If not already done, let's define chapters in the conversation or from user input
    # Example simulation: The user wants a 3-chapter video, so we store that:
    if not hasattr(state, "chapters") or state.chapters is None:

        planner_prompt = hub.pull("video-script-planner-prompt")
        message_content = planner_prompt.format(storytelling_guidebook= storytelling_guidebook)
        human_message = HumanMessage(content=message_content, name="user")
        messages = list(state.messages) + [ human_message]
        res = await planner.ainvoke(input={"messages": messages, "team": team,
                                              "storytelling_guidebook": storytelling_guidebook,
                                              "prompt": planner_prompt}, config=config)
        chapters = res['plan']
        state.video_title = res['video_title']
        state.chapters = chapters
        state.final_script = ""
        state.current_chapter_index = 0
        state.current_chapter_content = ""
        state.current_chapter_revision = 0
        formatted_chapters = _format_chapters(chapters)
        producer_message = (f"Here's a suggested agenda for your {len(chapters)}-chapter video on {res['video_title']}."
                            f"\n\n{formatted_chapters}")
        host_message = AIMessage(content=producer_message, name="planner")
        state.messages += [host_message]
    return state


async def researcher_node(state: VideoScriptState, config: RunnableConfig) -> Command[Literal["writer"]]:
    """
    The Researcher provides factual data/ideas for the current chapter.
    For demonstration, we just append a dummy 'AIMessage' with bullet points.
    """
    chapter = state.chapters[state.current_chapter_index]
    chapter_title = chapter['title']
    message_content = f"Provide research for the chapter '{chapter_title}' covering the key topics."
    human_message = HumanMessage(content=message_content, name="user")
    messages = list(state.messages) + [human_message]
    res = await researcher.ainvoke(input={"messages": messages, "team": team}, config=config)

    research_response_comment = res.get('comment', 'No comment provided.')
    research_chapter_content = res['research']
    research_message_content = (f"# Research for {chapter_title}"
                                f"\n\n{research_chapter_content}"
                                f"\n\n-----\n\n# Researcher Comment"
                                f"\n\n{research_response_comment}")

    return Command(
        update={
            "messages": [AIMessage(content=research_message_content, name="researcher")],
        },
        goto="writer",
    )


async def writer_node(state: VideoScriptState, config: RunnableConfig) -> Command[Literal["reviewer"]]:
    """
    The Writer composes or updates the script for the current chapter using the research input.
    """
    chapter = state.chapters[state.current_chapter_index]
    chapter_title = chapter['title']
    message_content = f"Write the script for chapter '{chapter_title}' using key topics, word counts and research."
    human_message = HumanMessage(content=message_content, name="user")
    messages = list(state.messages) + [human_message]

    res = await writer.ainvoke(input={"messages": messages,
                                     "team": team,
                                     "script_guidelines": script_guidelines,
                                     "storytelling_guidebook": storytelling_guidebook
                                     }, config=config)

    # Check if 'comment' is in the response
    writer_chapter_content = res['chapter']
    writer_response_comment = res.get('comment', 'No comment provided.')

    writer_message_content = (f"# Draft for {chapter_title}"
                              f"\n\n{writer_chapter_content}\n\n-----"
                              f"\n\n# Writer Comment"
                              f"\n\n{writer_response_comment}")

    return Command(
        update={
            "messages": [AIMessage(content=writer_message_content, name="writer")],
            "current_chapter_content": writer_chapter_content
        },
        goto="reviewer",
    )


async def reviewer_node(state: VideoScriptState, config: RunnableConfig) -> Command[Literal["supervisor"]]:
    """
    The 'Reviewer' agent checks the current draft:
      - If acceptable, we finalize the chapter.
      - If not acceptable, we request changes => 'draft_node' or 'researcher_node' again.
    """
    chapter = state.chapters[state.current_chapter_index]
    chapter_title = chapter['title']
    revision = state.current_chapter_index
    human_message = HumanMessage(content=f"Review the draft for chapter '{chapter_title}'", name="user")
    messages = list(state.messages) + [human_message]

    res = await reviewer.ainvoke(input={"messages": messages,
                                      "team": team,
                                      "script_guidelines": script_guidelines
                                        }, config=config)

    reviewer_message_content = (
        f"# Feedback for {chapter_title}\n\n"
        f"Good Points:\n {res['GoodPoints']}\n\n"
        f"Missing or Needs Research:\n {res['MissingOrNeedsResearch']}\n\n"
        f"Superfluous Content:\n {res['SuperfluousContent']}\n\n"
        f"Style Refinement:\n {res['StyleRefinement']}\n\n"
        f"NextNode: {res['NextNode']}\n\n"
        f"Revision: {revision}\n\n"
    )

    return Command(
        update={
            "messages": [AIMessage(content=reviewer_message_content, name="reviewer")],
            "next_node": res["NextNode"],
        },
        goto="supervisor",
    )



# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
members = ["researcher", "writer"]


def finalize_script(state: VideoScriptState, current_chapter: int, chapter_title: str,
                    final_script: str, chapter_content: str, reason: str = "") -> Command:
    """
    Helper function to finalize the script and prepare the completion message.
    Arguments maintain the current state values to avoid any indexing issues.
    """
    # Add current chapter if content exists
    if chapter_content:
        final_script += f"## CHAPTER {current_chapter + 1} - {chapter_title}\n\n{chapter_content}\n\n"

    reason_text = f" ({reason})" if reason else ""
    message = (f"Here is your final script{reason_text}.\n\n########\n\n"
               f"# {state.video_title}\n\n"
               f"{final_script}")

    return Command(
        goto=END,
        update={
            "final_script": "",
            "current_chapter_content": "",
            "messages": [AIMessage(content=message, name="host-producer")],
        }
    )


async def supervisor_node(state: VideoScriptState, config: RunnableConfig) -> Command[Literal[*members, END]]:

    configuration = Configuration.from_runnable_config(config)

    current_chapter = state.current_chapter_index
    revision_count = state.current_chapter_revision
    chapter_title = state.chapters[current_chapter]['title']

    messages = state.messages
    chapters_length = len(state.chapters)
    logger.debug(f"Start approval chapter='{current_chapter}/{chapters_length}',"
                 f" revision='{revision_count}/{configuration.max_revision}', members='{members}")

    final_script = state.final_script
    chapter_content = state.current_chapter_content

    message: Optional[str] = None

    # Check if remaining steps are below the minimum threshold
    if state.remaining_steps <= configuration.min_remaining_step:
        logger.info(f"Ending due to insufficient remaining steps ({state.remaining_steps})")
        return finalize_script(
            state, current_chapter, chapter_title, final_script, chapter_content,
            reason="ended due to remaining steps"
        )

    # Check if the current chapter index is greater than or equal to available chapters
    if current_chapter >= chapters_length:
        logger.info(f"Ending as all chapters are completed")
        return finalize_script(state, current_chapter, chapter_title, final_script, chapter_content)

    # Check if maximum revisions have been reached
    if revision_count >= configuration.max_revision:
        goto = "researcher"
        logger.info(f"Maximum revisions reached for chapter {chapter_title}. chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")

        if current_chapter >= chapters_length:
            logger.info("Ending as all chapters are completed")
            return finalize_script(state, current_chapter, chapter_title, final_script, chapter_content)

        current_chapter += 1  # Move to next chapter
        revision_count = 0
        message = f"Maximum revisions reached for chapter {chapter_title}. Moving to next chapter or ending workflow."
        final_script += f"## CHAPTER {current_chapter} - {chapter_title}\n\n" + chapter_content + "\n\n"

    else:
        if revision_count == 0:
            goto = "researcher"
            logger.debug(f"First revision chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
            message = "Let's make it, Team!"
            revision_count += 1  # Increment the revision count
        else:

            messages = (list(state.messages) +
                        [HumanMessage(content="Based on the last 'reviewer' feedback,"
                                              " do you approve the latest draft for the current chapter?"
                                              " Your goal is to optimize the editing process."
                                              " Request a revision only if the content does not align with the writing guidebook."
                                              "\nFormat: status: ['approved', 'revised']", name="supervisor")])

            try:

                res = await supervisor.ainvoke(input={"messages": messages, "team": team}, config=config)

                if res['status'] != 'approved':
                    # Ensure next_node is valid, default to "researcher" if not
                    goto = "researcher" if state.next_node not in members else state.next_node
                    message = f"Revisions needed. Returning to the {goto}."
                    revision_count += 1  # Increment the revision count
                else:
                    # First, append current chapter to final script before any index changes
                    current_chapter += 1  # Move to next chapter
                    revision_count = 0

                    # Check if this was the last chapter
                    if current_chapter >= chapters_length:
                        logger.info("Last chapter approved. Finalizing script.")
                        return finalize_script(state, current_chapter - 1, chapter_title, final_script, chapter_content)
                    message = "Chapter approved. Moving to next."
                    final_script += f"## CHAPTER {current_chapter} - {chapter_title}\n\n" + chapter_content + "\n\n"
                    goto = "researcher"
                logger.debug(f"Approbation step {res['status']} chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
            except Exception as e:
                logger.error(f"Error invoking approve_video: {e}", e)
                goto = END

    logger.debug(f"End (conclusion) chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
    return Command(
        update={
            "messages": AIMessage(content=message, name="supervisor"),
            "next_node": "researcher" if goto == END else goto,
            "current_chapter_index": current_chapter,
            "current_chapter_revision": revision_count,
            "current_chapter_content": "",
            "final_script": final_script,
        },
        goto=goto,
    )


def create_video_script_agent() -> CompiledStateGraph:
    """
    Build and Compile the Video Script Graph
    """
    workflow = StateGraph(VideoScriptState, input=InputState, config_schema=Configuration)

    # NODES
    workflow.add_node("planning", planning_node)
    workflow.add_node("supervisor", supervisor_node)  # script_writing_supervisor_node
    workflow.add_node("researcher", researcher_node,
                      retry=RetryPolicy(retry_on=[KeyError, AttributeError, ReadTimeout], max_attempts=3))
    workflow.add_node("writer", writer_node,
                      retry=RetryPolicy(retry_on=[KeyError, AttributeError], max_attempts=3))
    workflow.add_node("reviewer", reviewer_node,
                      retry=RetryPolicy(retry_on=[KeyError, AttributeError], max_attempts=3))

    # EDGES
    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "supervisor")

    # Compile the graph
    memory = MemorySaver()
    video_script_app = workflow.compile(checkpointer=memory)
    return video_script_app


video_script = create_video_script_agent()
video_script.name = "video-script"  # This defines the custom name in LangSmith

__all__ = ["video_script"]

