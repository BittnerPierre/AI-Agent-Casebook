"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig, ensure_config



@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""


    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=3,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    recursion_limit: int = field(
        default=99,
        metadata={
            "description": "The maximum number of super-steps the graph can execute during a single execution."
        },
    )

    min_remaining_step: int = field(
        default=2,
        metadata={
            "description": "The number of remaining steps which indicates the supervisor have to finalized the entire works."
        },
    )
    max_revision: int = field(
        default=2,
        metadata={
            "description": "The maximum number of revision that the supervisor can accept for a chapter."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
