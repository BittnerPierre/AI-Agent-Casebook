from dataclasses import field, dataclass
from typing import Annotated, List, Literal, Sequence, Optional

from langchain_core.messages import BaseMessage, AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import RemainingSteps
from typing_extensions import TypedDict

from video_script.agents import Chapter


@dataclass
class InputState:
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    """
    Messages tracking the primary execution state of the agent.

    Typically accumulates a pattern of:
    1. HumanMessage - user input
    2. AIMessage with .tool_calls - agent picking tool(s) to use to collect information
    3. ToolMessage(s) - the responses (or errors) from the executed tools
    4. AIMessage without .tool_calls - agent responding in unstructured format to the user
    5. HumanMessage - user responds with the next conversational turn

    Steps 2-5 may repeat as needed.

    The `add_messages` annotation ensures that new messages are merged with existing ones,
    updating by ID to maintain an "append-only" state unless a message with the same ID is provided.
    """


@dataclass
class VideoScriptState(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """
    video_title: Optional[str] = field(default=None)
    chapters: Optional[List[Chapter]] = field(default=None)
    current_chapter_index: Optional[int] = field(default=None)
    current_chapter_content: Optional[str] = field(default=None)
    current_chapter_revision: Optional[int] = field(default=None)
    final_script: Optional[str] = field(default=None)
    next_node: Optional[Literal['researcher', 'writer', 'approved']] = field(default=None)
    remaining_steps: RemainingSteps = field(default=0)