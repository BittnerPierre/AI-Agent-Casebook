"""Shared data models for module independence."""

from datetime import datetime

from pydantic import BaseModel


class ModuleMetadata(BaseModel):
    """Standardized module metadata across all systems."""
    module_id: str
    title: str
    summary: str
    keywords: list[str]
    tags: list[str]
    course_id: str
    cleaned_transcript_path: str
    created_at: datetime
    updated_at: datetime
    word_count: int | None = None
    estimated_duration_minutes: int | None = None


class CourseMetadata(BaseModel):
    """Standardized course metadata across all systems."""
    course_id: str
    course_title: str
    course_type: str  # "single-file" | "multi-module"
    modules: list[ModuleMetadata]
    total_modules: int
    created_at: datetime
    updated_at: datetime


class SearchQuery(BaseModel):
    """Query interface for knowledge database."""
    keywords: list[str] | None = None
    tags: list[str] | None = None
    course_ids: list[str] | None = None
    module_ids: list[str] | None = None
    limit: int = 50
    offset: int = 0


class SearchResult(BaseModel):
    """Search results from knowledge database."""
    modules: list[ModuleMetadata]
    total_count: int
    query: SearchQuery