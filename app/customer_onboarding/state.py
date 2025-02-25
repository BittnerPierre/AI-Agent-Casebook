"""Define the shared values."""

from dataclasses import dataclass
from typing import TypedDict, Annotated

from langgraph.graph import add_messages

@dataclass(kw_only=True)
class State(TypedDict):
    """Main graph state."""
    messages: Annotated[list, add_messages]
    """The messages in the conversation."""


__all__ = [
    "State",
]