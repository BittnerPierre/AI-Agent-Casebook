"""Response formatting for Evernote chatbot with rich console output."""

import re

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from .config import ChatbotConfig
from .evernote_handler import NoteMetadata, SearchResult


class ResponseFormatter:
    """Formats responses with rich console output and proper citations."""

    def __init__(self, config: ChatbotConfig, console: Console | None = None):
        self.config = config
        self.console = console or Console()

    def format_search_results(
        self,
        search_result: SearchResult,
        notes_with_content: dict[str, tuple[NoteMetadata, str]] | None = None,
    ) -> str:
        """
        Format search results with citations and metadata.

        Args:
            search_result: Search result containing note metadata
            notes_with_content: Optional dict of note GUID -> (metadata, content)

        Returns:
            Formatted string for display
        """
        if search_result.total_notes == 0:
            return self._format_no_results(search_result.query)

        # Create summary text
        summary_parts = []

        # Header
        summary_parts.append(f"## Found {search_result.total_notes} notes for: '{search_result.query}'")
        summary_parts.append("")

        # Process each note
        for i, note in enumerate(search_result.notes, 1):
            note_summary = self._format_note_summary(
                note, i, notes_with_content.get(note.guid) if notes_with_content else None
            )
            summary_parts.append(note_summary)
            summary_parts.append("")

        # Add search tips if no content was retrieved
        if not notes_with_content:
            summary_parts.append("---")
            summary_parts.append("💡 **Tip**: For detailed summaries, ask me to analyze specific notes by title or ask follow-up questions about the content.")

        return "\\n".join(summary_parts)

    def format_note_content(
        self,
        metadata: NoteMetadata,
        content: str,
        include_metadata: bool = True,
    ) -> str:
        """
        Format a single note's content with metadata.

        Args:
            metadata: Note metadata
            content: Note content
            include_metadata: Whether to include metadata header

        Returns:
            Formatted string for display
        """
        parts = []

        if include_metadata:
            parts.append(f"# {metadata.title}")
            parts.append("")
            parts.append(self._format_note_metadata_line(metadata))
            parts.append("")
            parts.append("---")
            parts.append("")

        # Clean and format content
        cleaned_content = self._clean_note_content(content)
        parts.append(cleaned_content)

        return "\\n".join(parts)

    def format_summary_with_citations(
        self,
        summary: str,
        notes: list[NoteMetadata],
    ) -> str:
        """
        Format a summary with proper citations.

        Args:
            summary: Generated summary text
            notes: List of notes that were referenced

        Returns:
            Summary with citation footer
        """
        parts = [summary]

        if notes:
            parts.append("")
            parts.append("---")
            parts.append("## Sources")
            parts.append("")

            for i, note in enumerate(notes, 1):
                citation = self._format_citation(note, i)
                parts.append(citation)

        return "\\n".join(parts)

    def display_search_results_table(self, search_result: SearchResult) -> None:
        """Display search results as a rich table."""
        if search_result.total_notes == 0:
            self.console.print(f"[yellow]No notes found for: '{search_result.query}'[/yellow]")
            self._display_search_tips()
            return

        table = Table(title=f"Search Results for '{search_result.query}'")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="bold")

        if self.config.show_notebook:
            table.add_column("Notebook", style="blue")

        if self.config.show_timestamps:
            table.add_column("Updated", style="dim")

        if self.config.show_tags:
            table.add_column("Tags", style="green")

        # Add rows
        for i, note in enumerate(search_result.notes, 1):
            row = [str(i), note.title]

            if self.config.show_notebook:
                row.append(note.notebook_name or "Default")

            if self.config.show_timestamps:
                updated = note.updated or note.created
                if updated:
                    row.append(updated.strftime("%Y-%m-%d %H:%M"))
                else:
                    row.append("Unknown")

            if self.config.show_tags:
                tags_str = ", ".join(note.tags) if note.tags else "None"
                row.append(tags_str)

            table.add_row(*row)

        self.console.print(table)

    def display_config(self) -> None:
        """Display current configuration."""
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="bold")
        table.add_column("Value", style="blue")

        config_dict = self.config.to_display_dict()
        for key, value in config_dict.items():
            table.add_row(key, value)

        self.console.print(table)

    def display_error(self, error: Exception, context: str = "") -> None:
        """Display an error message."""
        error_text = f"[red]Error{f' ({context})' if context else ''}: {error!s}[/red]"
        self.console.print(error_text)

    def display_info(self, message: str) -> None:
        """Display an info message."""
        self.console.print(f"[blue]ℹ {message}[/blue]")

    def display_success(self, message: str) -> None:
        """Display a success message."""
        self.console.print(f"[green]✓ {message}[/green]")

    def display_warning(self, message: str) -> None:
        """Display a warning message."""
        self.console.print(f"[yellow]⚠ {message}[/yellow]")

    def _format_no_results(self, query: str) -> str:
        """Format message when no results are found."""
        parts = [
            f"## No notes found for: '{query}'",
            "",
            "### Suggestions:",
            "- Try different search terms or keywords",
            "- Check if your query matches note titles, content, or tags",
            "- Consider using broader terms or partial matches",
        ]

        if self.config.allowed_notebooks:
            parts.extend([
                "",
                f"**Note**: Search is limited to notebooks: {', '.join(sorted(self.config.allowed_notebooks))}",
            ])

        return "\\n".join(parts)

    def _format_note_summary(
        self,
        note: NoteMetadata,
        index: int,
        content_data: tuple[NoteMetadata, str] | None = None,
    ) -> str:
        """Format a single note summary."""
        parts = [f"### {index}. {note.title}"]

        # Add metadata line
        metadata_line = self._format_note_metadata_line(note)
        if metadata_line:
            parts.append(f"*{metadata_line}*")

        # Add content preview if available
        if content_data:
            _, content = content_data
            preview = self._create_content_preview(content)
            if preview:
                parts.append("")
                parts.append(preview)

        return "\\n".join(parts)

    def _format_note_metadata_line(self, note: NoteMetadata) -> str:
        """Format metadata line for a note."""
        parts = []

        if self.config.show_notebook and note.notebook_name:
            parts.append(f"📁 {note.notebook_name}")

        if self.config.show_timestamps:
            if note.updated:
                parts.append(f"📅 Updated {note.updated.strftime('%Y-%m-%d %H:%M')}")
            elif note.created:
                parts.append(f"📅 Created {note.created.strftime('%Y-%m-%d %H:%M')}")

        if self.config.show_tags and note.tags:
            tags_str = " ".join(f"#{tag}" for tag in note.tags)
            parts.append(f"🏷️ {tags_str}")

        return " | ".join(parts)

    def _format_citation(self, note: NoteMetadata, index: int) -> str:
        """Format a citation for a note."""
        parts = [f"[{index}] **{note.title}**"]

        citation_parts = []
        if note.notebook_name:
            citation_parts.append(f"Notebook: {note.notebook_name}")

        if note.updated:
            citation_parts.append(f"Updated: {note.updated.strftime('%Y-%m-%d')}")

        if citation_parts:
            parts.append(f"    {' | '.join(citation_parts)}")

        return "\\n".join(parts)

    def _create_content_preview(self, content: str) -> str:
        """Create a preview of note content."""
        if not content or self.config.max_content_preview <= 0:
            return ""

        # Clean content
        cleaned = self._clean_note_content(content)

        # Truncate if needed
        if len(cleaned) > self.config.max_content_preview:
            preview = cleaned[:self.config.max_content_preview].rstrip()
            # Try to end at a word boundary
            last_space = preview.rfind(" ")
            if last_space > self.config.max_content_preview * 0.8:
                preview = preview[:last_space]
            preview += "..."
        else:
            preview = cleaned

        return f"> {preview}" if preview else ""

    def _clean_note_content(self, content: str) -> str:
        """Clean note content for display."""
        if not content:
            return ""

        # Remove HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)

        # Replace HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&amp;', '&')

        # Normalize whitespace
        content = re.sub(r'\\s+', ' ', content)
        content = content.strip()

        return content

    def _display_search_tips(self) -> None:
        """Display search tips when no results are found."""
        tips = [
            "💡 **Search Tips:**",
            "  • Use specific keywords from your notes",
            "  • Try searching for note titles or tag names",
            "  • Use broader terms if your search is too specific",
            "  • Check that your notes are in allowed notebooks",
        ]

        for tip in tips:
            self.console.print(tip)

    def print_markdown(self, text: str) -> None:
        """Print text as markdown."""
        try:
            markdown = Markdown(text)
            self.console.print(markdown)
        except Exception:
            # Fallback to plain text if markdown parsing fails
            self.console.print(text)