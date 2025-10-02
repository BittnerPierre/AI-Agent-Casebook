"""Configuration management for Evernote Chatbot."""

import os

from pydantic import BaseModel, Field, validator


class ChatbotConfig(BaseModel):
    """Configuration for Evernote Chatbot."""

    # MCP Server Configuration
    container_name: str = Field(
        default="evernote-mcp-server-evernote-mcp-server-1",
        description="Docker container name for MCP server",
    )

    mcp_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
        gt=0,
    )

    # Query Configuration
    max_notes_per_query: int = Field(
        default=20,
        description="Maximum number of notes to retrieve per query",
        gt=0,
        le=100,
    )

    allowed_notebooks: set[str] = Field(
        default_factory=set,
        description="Set of allowed notebook names (empty = all allowed)",
    )

    prefer_html: bool = Field(
        default=False,
        description="Prefer HTML content over plain text",
    )

    # Display Configuration
    show_timestamps: bool = Field(
        default=True,
        description="Show created/updated timestamps in responses",
    )

    show_tags: bool = Field(
        default=True,
        description="Show note tags in responses",
    )

    show_notebook: bool = Field(
        default=True,
        description="Show notebook name in responses",
    )

    max_content_preview: int = Field(
        default=200,
        description="Maximum characters to show in content preview",
        ge=0,
    )

    # Session Configuration
    save_history: bool = Field(
        default=True,
        description="Save conversation history during session",
    )

    history_file: str | None = Field(
        default=None,
        description="File path to save conversation history",
    )


    @validator("allowed_notebooks", pre=True)
    def parse_notebooks(cls, v):
        """Parse notebooks from comma-separated string or set."""
        if isinstance(v, str):
            if not v.strip():
                return set()
            return {nb.strip() for nb in v.split(",") if nb.strip()}
        elif isinstance(v, (list, tuple)):
            return {str(nb).strip() for nb in v if str(nb).strip()}
        return v or set()

    @classmethod
    def from_env(cls) -> "ChatbotConfig":
        """Create configuration from environment variables."""
        return cls(
            container_name=os.getenv("CONTAINER_NAME", "evernote-mcp-server-evernote-mcp-server-1"),
            mcp_timeout=float(os.getenv("MCP_TIMEOUT", "30.0")),
            max_notes_per_query=int(os.getenv("MAX_NOTES_PER_QUERY", "20")),
            allowed_notebooks=os.getenv("ALLOWED_NOTEBOOKS", ""),
            prefer_html=os.getenv("PREFER_HTML", "").lower() in ("true", "1", "yes"),
            show_timestamps=os.getenv("SHOW_TIMESTAMPS", "true").lower() in ("true", "1", "yes"),
            show_tags=os.getenv("SHOW_TAGS", "true").lower() in ("true", "1", "yes"),
            show_notebook=os.getenv("SHOW_NOTEBOOK", "true").lower() in ("true", "1", "yes"),
            max_content_preview=int(os.getenv("MAX_CONTENT_PREVIEW", "200")),
            save_history=os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes"),
            history_file=os.getenv("HISTORY_FILE"),
        )

    def merge_cli_args(self, **kwargs) -> "ChatbotConfig":
        """Create new config by merging CLI arguments."""
        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}

        # Handle special cases
        if "notebooks" in updates:
            notebooks_val = updates.pop("notebooks")
            if isinstance(notebooks_val, str) and notebooks_val.strip():
                updates["allowed_notebooks"] = {nb.strip() for nb in notebooks_val.split(",") if nb.strip()}
            else:
                updates["allowed_notebooks"] = notebooks_val

        return self.model_copy(update=updates)

    def to_display_dict(self) -> dict[str, str]:
        """Convert config to a display-friendly dictionary."""
        return {
            "Container Name": self.container_name,
            "Max Notes": str(self.max_notes_per_query),
            "Allowed Notebooks": ", ".join(sorted(self.allowed_notebooks)) or "All",
            "Prefer HTML": "Yes" if self.prefer_html else "No",
            "Show Timestamps": "Yes" if self.show_timestamps else "No",
            "Show Tags": "Yes" if self.show_tags else "No",
            "Show Notebook": "Yes" if self.show_notebook else "No",
            "Content Preview": f"{self.max_content_preview} chars",
            "Save History": "Yes" if self.save_history else "No",
            "Timeout": f"{self.mcp_timeout}s",
        }