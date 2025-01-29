import json
from typing import List, Literal, Annotated, Optional

from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import (
    StateGraph,
    START,
    END
)
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.managed.is_last_step import RemainingSteps
from langgraph.types import Command, RetryPolicy
from typing_extensions import TypedDict

from core.base import SupportedModel
from core.commons import initiate_model
from core.logger import logger

worker_llm = initiate_model(SupportedModel.MISTRAL_LARGE)
producer_llm = initiate_model(SupportedModel.MISTRAL_LARGE)

MIN_REMAINING_STEP = 2
MAX_REVISION = 1

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


class Chapter(TypedDict):
    title: str
    covered_topics: List[str]
    chapter_brief: str


class Planning(TypedDict):
    video_title: str
    plan: List[Chapter]


producer_prompt = hub.pull("video-script-producer-prompt")

plan_video = producer_prompt | producer_llm.with_structured_output(Planning)


class Approval(TypedDict):
    status: Literal['approved', 'revised']


approve_video = producer_prompt | producer_llm.with_structured_output(Approval)


##############
# RESEARCHER #
##############


class ResearchChapter(TypedDict):
    research: str
    comment: str


researcher_prompt = hub.pull("video-script-researcher-prompt")

researcher = researcher_prompt | worker_llm.with_structured_output(ResearchChapter)

##############
# WRITER     #
##############


class DraftChapter(TypedDict):
    chapter: str
    comment: str


writer_prompt = hub.pull("video-script-writer-prompt")

write = writer_prompt | worker_llm.with_structured_output(DraftChapter)


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

review = review_prompt | worker_llm.with_structured_output(ReviewFeedback)


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
    video_title: str
    chapters: List[Chapter]
    current_chapter_index: int
    current_chapter_content: str
    current_chapter_revision: int
    final_script: str
    next_node: Literal['researcher', 'writer', 'approved']
    remaining_steps: RemainingSteps


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
async def planning_node(state: VideoScriptState) -> VideoScriptState:
    """
    The Host/Producer sets the plan (how many chapters, the overall direction).
    In a real scenario, you'd call host_producer_prompt with the user request to produce an agenda.
    We'll simulate it here.
    """
    # If not already done, let's define chapters in the conversation or from user input
    # Example simulation: The user wants a 3-chapter video, so we store that:
    if not state.get("chapters"):
        message_content = (
            "Elaborate the plan of the video script. \n"
            "Define for each chapter:\n"
            " - Title (words count for chapter in format 'X words')\n"
            " - covered topics (max 3 per chapter).\n"
            " - Brief for the chapter.\n"
            "\n\n"
            "The video plan must follow this template :\n"
            "- Opening Section: Video hook and introduction for [Video Subject].\n"
            "- Main Section: 'Body' of the script where you develop the X chapters.\n"
            "- Closing Section: CTA (call to action) and short conclusion for [Video Subject].\n"
            "\n\n"
            "Opening and Closing section does not count as user 'chapter'. "
            "If user ask for 3 chapters, you must plan for 5 (1: Hook+Introduction, 2,3,4: user chapters, 5: CTA+Conclusion)"
            "\n\n"
            "Here’s a simple, four-step formula for structuring the body of your script:\n"
            "- Step 1: Think about the main idea, the audience and the message you wand to deliver.\n"
            "- Step 2: Select key messages and write down video hook and introduction that presents the principal ideas, "
            "that you want to develop in an engaging way so you don’t overwhelm your audience.\n"
            "- Step 3: Elaborate chapter individually on each ideas using examples from the context.\n"
            "- Step 4. Include the final call to action. Tell your audience what to do next.\n"
            "\n\n"
            "When done define an engaging 'video title' that will set the expectation for the video and create a curiosity gap."
            "The 'plan' and 'video title' must be in the same language as the script."
            f"{storytelling_guidebook}")

        human_message = HumanMessage(content=message_content, name="user")
        messages = state["messages"] + [human_message]
        res = await plan_video.ainvoke(input={"messages": messages, "team": team})
        chapters = res['plan']
        state["video_title"] = res['video_title']
        state["chapters"] = chapters
        state["final_script"] = ""
        state["current_chapter_index"] = 0
        state["current_chapter_content"] = ""
        state["current_chapter_revision"] = 0
        formatted_chapters = _format_chapters(chapters)
        producer_message = (f"Here's a suggested agenda for your {len(chapters)}-chapter video on {res['video_title']}."
                            f"\n\n{formatted_chapters}")
        host_message = AIMessage(content=producer_message, name="host-producer")
        state["messages"].append(host_message)
    return state


async def researcher_node(state: VideoScriptState) -> Command[Literal["writer"]]:
    """
    The Researcher provides factual data/ideas for the current chapter.
    For demonstration, we just append a dummy 'AIMessage' with bullet points.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter['title']
    message_content = f"Provide research for the chapter '{chapter_title}' covering the key topics."
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
            "messages": [AIMessage(content=research_message_content, name="researcher")],
        },
        goto="writer",
    )


async def writer_node(state: VideoScriptState) -> Command[Literal["reviewer"]]:
    """
    The Writer composes or updates the script for the current chapter using the research input.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter['title']
    message_content = f"Write the script for chapter '{chapter_title}' using key topics, word counts and research."
    human_message = HumanMessage(content=message_content, name="user")
    messages = state["messages"] + [human_message]

    res = await write.ainvoke(input={"messages": messages,
                                     "team": team,
                                     "script_guidelines": script_guidelines,
                                     "storytelling_guidebook": storytelling_guidebook
                                     })
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


async def reviewer_node(state: VideoScriptState) -> Command[Literal["supervisor"]]:
    """
    The 'Reviewer' agent checks the current draft:
      - If acceptable, we finalize the chapter.
      - If not acceptable, we request changes => 'draft_node' or 'researcher_node' again.
    """
    chapter = state["chapters"][state["current_chapter_index"]]
    chapter_title = chapter['title']
    revision = state["current_chapter_index"]
    human_message = HumanMessage(content=f"Review the draft for chapter '{chapter_title}'", name="user")
    messages = state["messages"] + [human_message]

    res = await review.ainvoke(input={"messages": messages,
                                      "team": team,
                                      "script_guidelines": script_guidelines
                                      })
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


async def supervisor_node(state: VideoScriptState) -> Command[Literal[*members, END]]:
    current_chapter = state["current_chapter_index"]
    revision_count = state["current_chapter_revision"]
    messages = state["messages"]
    chapters_length = len(state["chapters"]) - 1
    logger.debug(f"Start approval chapter='{current_chapter}/{chapters_length}', revision='{revision_count}/{MAX_REVISION}', members='{members}")

    final_script = state["final_script"]
    chapter_content = state["current_chapter_content"]

    message: Optional[str] = None

    # Check if remaining steps are below the minimum threshold
    if state["remaining_steps"] <= MIN_REMAINING_STEP:
        logger.info(f"Ending due to insufficient remaining steps ({state["remaining_steps"]})")
        final_script += f"## CHAPTER {current_chapter}\n\n" + chapter_content + "\n\n"
        message = (f"Here is the script as it is (ended due to remaining step)."
                   f"\n\n# {state["video_title"]}\n\n"
                   f"{final_script}\n")
        return Command(goto=END,
                       update={# "final_script": final_script,
                               "messages": AIMessage(content=message, name="host-producer")})

    # Check if the current chapter index is greater than or equal to available chapters
    if current_chapter > chapters_length:
        logger.info(f"Ending as all chapters are completed")
        # final_script += f"## CHAPTER {current_chapter}\n\n" + chapter_content + "\n\n"
        message = (f"Here is the final script.\n\n########\n\n"
                   f"\n\n# {state["video_title"]}\n\n"
                   f"{final_script}")
        return Command(goto=END,
                       update={# "final_script": final_script,
                               "messages": AIMessage(content=message, name="host-producer"),})

    # Check if maximum revisions have been reached
    if revision_count >= MAX_REVISION:
        message = "Maximum revisions reached for this chapter. Moving to next chapter or ending workflow."
        goto = "researcher"
        current_chapter += 1  # Move to next chapter
        revision_count = 0
        final_script += f"## CHAPTER {current_chapter}\n\n" + chapter_content + "\n\n"
        logger.info(f"Maximum revisions reached for this chapter. chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
    else:
        if revision_count == 0:
            goto = "researcher"
            message = "Let's make it, Team!"
            revision_count += 1  # Increment the revision count
            logger.debug(f"First revision chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
        else:
            messages += [HumanMessage(content="Do you approve the draft for the last chapter?"
                                              "\nFormat: status: ['approved', 'revised']", name="host-producer")]
            try:
                res = await approve_video.ainvoke(input={"messages": messages, "team": team})

                if res['status'] != 'approved':
                    goto = state["next_node"]
                    message = f"Revisions needed. Returning to the {goto}."
                    revision_count += 1  # Increment the revision count
                else:
                    message = "Chapter approved. Moving to next."
                    goto = "researcher"
                    current_chapter += 1  # Move to next chapter
                    revision_count = 0
                    final_script += f"## CHAPTER {current_chapter}\n\n" + chapter_content + "\n\n"
                logger.debug(f"Approbation step {res['status']} chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
            except Exception as e:
                logger.error(f"Error invoking approve_video: {e}", e)
                goto = END

    logger.debug(f"End (conclusion) chapter='{current_chapter}', revision='{revision_count}', goto='{goto}'")
    return Command(
        update={
            "messages": HumanMessage(content=message, name="host-producer"),
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
    workflow = StateGraph(VideoScriptState)

    # NODES
    workflow.add_node("planning", planning_node)
    workflow.add_node("supervisor", supervisor_node)  # script_writing_supervisor_node
    workflow.add_node("researcher", researcher_node, retry=RetryPolicy(retry_on=KeyError, max_attempts=3))
    workflow.add_node("writer", writer_node, retry=RetryPolicy(retry_on=KeyError, max_attempts=3))
    workflow.add_node("reviewer", reviewer_node, retry=RetryPolicy(retry_on=KeyError, max_attempts=3))

    # EDGES
    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "supervisor")

    # Compile the graph
    memory = MemorySaver()
    video_script_app = workflow.compile(checkpointer=memory)
    return video_script_app

