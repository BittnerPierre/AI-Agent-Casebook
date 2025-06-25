"""
Common type definitions for the transcript generator.

This module defines shared data structures used across the editorial finalizer
and related modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IssueSeverity(Enum):
    """Issue severity levels for misconduct tracking"""
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"


@dataclass
class QualityIssue:
    """Represents a quality issue detected in content"""
    description: str
    severity: IssueSeverity
    section_id: str | None = None
    misconduct_category: str | None = None


@dataclass
class ChapterDraft:
    """Chapter draft data structure"""
    section_id: str
    content: str
    title: str | None = None


@dataclass
class QualityIssues:
    """Quality issues data structure for JSON export"""
    section_id: str
    issues: list[dict[str, str]]
    approved: bool


@dataclass
class FinalTranscript:
    """Final transcript data structure"""
    course_title: str
    sections: list[dict[str, str]] 