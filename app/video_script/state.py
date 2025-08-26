from dataclasses import field, dataclass
from typing import List, Literal, Optional

from langgraph.managed import RemainingSteps

from app.ai_agents.state import InputState
from app.video_script.agents import Chapter


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