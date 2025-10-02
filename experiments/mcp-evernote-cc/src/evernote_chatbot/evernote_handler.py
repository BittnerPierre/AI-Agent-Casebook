"""Evernote tool handlers for processing queries and managing note data."""

import asyncio
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NoteMetadata(BaseModel):
    """Metadata for an Evernote note."""
    guid: str
    title: str
    created: datetime | None = None
    updated: datetime | None = None
    tags: list[str] = []
    notebook_name: str | None = None
    content_length: int | None = None


class SearchResult(BaseModel):
    """Search result containing note metadata."""
    query: str
    total_notes: int
    notes: list[NoteMetadata]
    search_id: str | None = None


class EvernoteHandler:
    """Handler for Evernote operations through MCP client."""

    def __init__(
        self,
        mcp_client,  # Any MCP client
        max_notes_per_query: int = 20,
        allowed_notebooks: set[str] | None = None,
        prefer_html: bool = False,
    ):
        self.mcp_client = mcp_client
        self.max_notes_per_query = max_notes_per_query
        self.allowed_notebooks = allowed_notebooks or set()
        self.prefer_html = prefer_html

    async def search_notes(self, query: str) -> SearchResult:
        """
        Search for notes using natural language query.

        Args:
            query: Natural language search query

        Returns:
            SearchResult containing matching notes metadata

        Raises:
            MCPClientError: If search operation fails
        """
        try:
            # Create the search
            search_response = await self.mcp_client.create_search(query)

            if not search_response.content:
                return SearchResult(query=query, total_notes=0, notes=[])

            # Extract search ID if available for caching
            search_id = None
            search_data = {}
            if search_response.content and len(search_response.content) > 0:
                search_data = search_response.content[0].text

            if isinstance(search_data, str):
                try:
                    import json
                    search_data = json.loads(search_data)
                except json.JSONDecodeError:
                    search_data = {}

            if isinstance(search_data, dict):
                search_id = search_data.get("searchId") or search_data.get("id")

            # Parse note metadata from response
            notes = self._parse_note_metadata(search_response, query)

            # Filter by allowed notebooks if specified
            if self.allowed_notebooks:
                notes = [
                    note for note in notes
                    if not note.notebook_name or note.notebook_name in self.allowed_notebooks
                ]

            # Limit results
            notes = notes[:self.max_notes_per_query]

            # Get total count from response if available
            total_found = len(notes)
            if isinstance(search_data, dict) and "data" in search_data:
                total_found = search_data["data"].get("totalFound", len(notes))

            return SearchResult(
                query=query,
                total_notes=total_found,
                notes=notes,
                search_id=search_id,
            )

        except Exception as e:
            raise Exception(f"Search failed for query '{query}': {e}")

    async def get_cached_search(self, search_id: str) -> SearchResult:
        """
        Get cached search results.

        Args:
            search_id: ID from previous search

        Returns:
            SearchResult from cache

        Raises:
            MCPClientError: If retrieval fails
        """
        try:
            search_response = await self.mcp_client.get_search(search_id)

            if not search_response.content:
                return SearchResult(query="cached", total_notes=0, notes=[])

            notes = self._parse_note_metadata(search_response, "cached")

            # Apply filtering and limiting
            if self.allowed_notebooks:
                notes = [
                    note for note in notes
                    if not note.notebook_name or note.notebook_name in self.allowed_notebooks
                ]

            notes = notes[:self.max_notes_per_query]

            return SearchResult(
                query="cached",
                total_notes=len(notes),
                notes=notes,
                search_id=search_id,
            )

        except Exception as e:
            raise Exception(f"Failed to get cached search {search_id}: {e}")

    async def get_note_metadata(self, note_guid: str) -> NoteMetadata | None:
        """
        Get detailed metadata for a specific note.

        Args:
            note_guid: GUID of the note

        Returns:
            NoteMetadata or None if not found

        Raises:
            MCPClientError: If operation fails
        """
        try:
            response = await self.mcp_client.get_note(note_guid)

            if not response.content:
                return None

            # Parse the response
            note_data = {}
            if response.content and len(response.content) > 0:
                note_data = response.content[0].text

            if isinstance(note_data, str):
                try:
                    import json
                    note_data = json.loads(note_data)
                except json.JSONDecodeError:
                    note_data = {}

            return self._parse_single_note_metadata(note_data, note_guid)

        except Exception as e:
            raise Exception(f"Failed to get note metadata for {note_guid}: {e}")

    async def get_note_content(self, note_guid: str) -> str | None:
        """
        Get full content of a specific note.

        Args:
            note_guid: GUID of the note

        Returns:
            Note content as string or None if not found

        Raises:
            MCPClientError: If operation fails
        """
        try:
            response = await self.mcp_client.get_note_content(
                note_guid, prefer_html=self.prefer_html
            )

            if not response.content:
                return None

            # Extract content from response
            content = ""
            if response.content and len(response.content) > 0:
                content = response.content[0].text

            if isinstance(content, str):
                return content

            # If it's structured data, try to extract content
            if isinstance(content, dict):
                return content.get("content", str(content))

            return str(content)

        except Exception as e:
            raise Exception(f"Failed to get note content for {note_guid}: {e}")

    async def get_notes_with_content(
        self, note_guids: list[str]
    ) -> dict[str, tuple[NoteMetadata, str]]:
        """
        Get multiple notes with their content in parallel.

        Args:
            note_guids: List of note GUIDs

        Returns:
            Dict mapping GUID to (metadata, content) tuple
        """
        # Fetch metadata and content in parallel
        metadata_tasks = [self.get_note_metadata(guid) for guid in note_guids]
        content_tasks = [self.get_note_content(guid) for guid in note_guids]

        metadata_results = await asyncio.gather(*metadata_tasks, return_exceptions=True)
        content_results = await asyncio.gather(*content_tasks, return_exceptions=True)

        results = {}
        for i, guid in enumerate(note_guids):
            metadata = metadata_results[i]
            content = content_results[i]

            # Skip if either operation failed
            if isinstance(metadata, Exception) or isinstance(content, Exception):
                continue

            if metadata and content:
                results[guid] = (metadata, content)

        return results

    def _parse_note_metadata(self, response, query: str) -> list[NoteMetadata]:
        """Parse note metadata from MCP response."""
        notes = []

        if not response.content:
            return notes

        try:
            # Extract data from response
            data = {}
            if response.content and len(response.content) > 0:
                data = response.content[0].text

            if isinstance(data, str):
                try:
                    import json
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return notes

            # Handle different response formats
            if isinstance(data, dict):
                # Handle nested data structure from Evernote MCP server
                if "data" in data and "results" in data["data"]:
                    notes_data = data["data"]["results"]
                elif "notes" in data:
                    notes_data = data["notes"]
                elif "results" in data:
                    notes_data = data["results"]
                else:
                    # Single note response
                    notes_data = [data]
            elif isinstance(data, list):
                notes_data = data
            else:
                return notes

            # Parse each note
            for note_data in notes_data:
                if isinstance(note_data, dict):
                    note = self._parse_single_note_metadata(note_data)
                    if note:
                        notes.append(note)

        except Exception:
            # If parsing fails, return empty list
            pass

        return notes

    def _parse_single_note_metadata(
        self, note_data: dict[str, Any], guid: str | None = None
    ) -> NoteMetadata | None:
        """Parse metadata for a single note."""
        try:
            # Extract GUID
            note_guid = guid or note_data.get("guid") or note_data.get("id")
            if not note_guid:
                return None

            # Extract title
            title = note_data.get("title", "Untitled")

            # Extract dates
            created = None
            updated = None

            if "created" in note_data:
                try:
                    created = datetime.fromisoformat(str(note_data["created"]).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            if "updated" in note_data:
                try:
                    updated = datetime.fromisoformat(str(note_data["updated"]).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            # Extract tags
            tags = []
            if "tags" in note_data:
                if isinstance(note_data["tags"], list):
                    tags = [str(tag) for tag in note_data["tags"]]
                elif isinstance(note_data["tags"], str):
                    tags = [note_data["tags"]]

            # Extract notebook
            notebook_name = note_data.get("notebookName") or note_data.get("notebook")

            # Extract content length
            content_length = note_data.get("contentLength")
            if content_length is not None:
                try:
                    content_length = int(content_length)
                except (ValueError, TypeError):
                    content_length = None

            return NoteMetadata(
                guid=note_guid,
                title=title,
                created=created,
                updated=updated,
                tags=tags,
                notebook_name=notebook_name,
                content_length=content_length,
            )

        except Exception:
            return None