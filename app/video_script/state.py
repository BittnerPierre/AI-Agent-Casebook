from typing import Annotated, List, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langgraph.managed import RemainingSteps
from typing_extensions import TypedDict

from video_script.agents import Chapter


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
