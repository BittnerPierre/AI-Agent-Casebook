"""Shared data models for module independence."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ModuleMetadata(BaseModel):
    """Standardized module metadata across all systems."""
    module_id: str
    title: str
    summary: str
    keywords: List[str]
    tags: List[str]
    course_id: str
    cleaned_transcript_path: str
    created_at: datetime
    updated_at: datetime
    word_count: Optional[int] = None
    estimated_duration_minutes: Optional[int] = None


class CourseMetadata(BaseModel):
    """Standardized course metadata across all systems."""
    course_id: str
    course_title: str
    course_type: str  # "single-file" | "multi-module"
    modules: List[ModuleMetadata]
    total_modules: int
    created_at: datetime
    updated_at: datetime


class SearchQuery(BaseModel):
    """Query interface for knowledge database."""
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    course_ids: Optional[List[str]] = None
    module_ids: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0


class SearchResult(BaseModel):
    """Search results from knowledge database."""
    modules: List[ModuleMetadata]
    total_count: int
    query: SearchQuery