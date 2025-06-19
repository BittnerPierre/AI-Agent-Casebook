"""
Operational Training Manager Content Access (US-002)

Provides searchable, accessible processed content from training_manager outputs.
Thread-safe access for concurrent queries with keyword-based search.

This module implements the ContentAccessor class specified in US-002 to bridge
the gap between training_manager preprocessing and Knowledge Bridge MCP interface.

Author: Claude Code - Sprint 1 Week 1
Reference: US-002 Operational Training Manager Content Access (Issue #48)
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


class ContentAccessor:
    """
    Content accessor for processed training manager content.
    
    Provides searchable access to training_manager preprocessed content for
    Knowledge Bridge MCP interface integration. Implements thread-safe access
    with keyword-based search and content retrieval.
    
    Architecture:
    - Local file storage with JSON metadata (Sprint 1 approach)
    - Simple keyword matching and metadata filtering
    - Direct file I/O operations with caching
    - Thread-safe concurrent query support
    """
    
    def __init__(self, output_base_path: str = "output"):
        """
        Initialize ContentAccessor with training_manager output path.
        
        Args:
            output_base_path: Path to training_manager output directory
        """
        self.output_path = Path(output_base_path)
        self._lock = threading.RLock()  # Thread-safe access
        self._content_cache: dict[str, str] = {}  # Content caching
        self._metadata_cache: dict[str, dict] = {}  # Metadata caching
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"[ContentAccessor] Initialized with output path: {output_base_path}")
    
    def get_by_keywords(self, keywords: list[str], max_results: int = 10) -> list[dict[str, Any]]:
        """
        Search content by keywords and return structured results.
        
        Implements keyword-based search across processed training content with
        relevance scoring and metadata enrichment.
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of content matches with metadata and relevance scores
        """
        with self._lock:
            self.logger.info(f"[ContentAccessor] Searching for keywords: {keywords}")
            
            if not keywords:
                self.logger.warning("[ContentAccessor] Empty keywords provided")
                return []
            
            # Get all available content
            all_content = self._get_all_content_metadata()
            
            # Search and score content
            content_matches = []
            keywords_lower = [kw.lower() for kw in keywords]
            
            for content_id, metadata in all_content.items():
                relevance_score = self._calculate_relevance_score(metadata, keywords_lower)
                
                if relevance_score > 0:  # Only include relevant content
                    content_match = {
                        "content_id": content_id,
                        "title": metadata.get("title", "Unknown"),
                        "relevance_score": relevance_score,
                        "content_preview": self._create_content_preview(metadata),
                        "metadata": {
                            "source": metadata.get("course_id", "unknown"),
                            "content_type": "training_transcript",
                            "tags": metadata.get("tags", []),
                            "keywords": metadata.get("keywords", []),
                            "module_id": metadata.get("module_id", "unknown"),
                            "summary": metadata.get("summary", "")[:300] + "..." if len(metadata.get("summary", "")) > 300 else metadata.get("summary", "")
                        }
                    }
                    content_matches.append(content_match)
            
            # Sort by relevance score (descending)
            content_matches.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit results
            content_matches = content_matches[:max_results]
            
            self.logger.info(f"[ContentAccessor] Found {len(content_matches)} content matches")
            return content_matches
    
    def get_content(self, content_id: str) -> dict[str, Any] | None:
        """
        Get full content by content_id.
        
        Retrieves complete processed content including full transcript text
        and comprehensive metadata.
        
        Args:
            content_id: Content identifier in format "course_id:module_id"
            
        Returns:
            Full content data or None if not found
        """
        with self._lock:
            self.logger.info(f"[ContentAccessor] Getting content for ID: {content_id}")
            
            try:
                # Parse content_id
                if ":" not in content_id:
                    self.logger.error(f"[ContentAccessor] Invalid content_id format: {content_id}")
                    return None
                
                course_id, module_id = content_id.split(":", 1)
                
                # Get metadata
                metadata = self._get_module_metadata(course_id, module_id)
                if not metadata:
                    self.logger.error(f"[ContentAccessor] Module metadata not found: {content_id}")
                    return None
                
                # Get full content (with caching)
                full_content = self._get_cleaned_transcript(course_id, module_id)
                if not full_content:
                    self.logger.error(f"[ContentAccessor] Content file not found: {content_id}")
                    return None
                
                content_data = {
                    "content_id": content_id,
                    "full_content": full_content,
                    "metadata": {
                        "title": metadata.get("title", "Unknown"),
                        "summary": metadata.get("summary", ""),
                        "source": course_id,
                        "content_type": "training_transcript",
                        "tags": metadata.get("tags", []),
                        "keywords": metadata.get("keywords", []),
                        "module_id": module_id,
                        "created_at": datetime.now().isoformat(),  # Current timestamp for Sprint 1
                        "updated_at": datetime.now().isoformat()
                    }
                }
                
                self.logger.info(f"[ContentAccessor] Retrieved content: {content_id} ({len(full_content)} chars)")
                return content_data
                
            except Exception as e:
                self.logger.error(f"[ContentAccessor] Error getting content {content_id}: {e!s}")
                return None
    
    def list_available_courses(self) -> list[str]:
        """
        List all available course IDs with processed content.
        
        Returns:
            List of course IDs that have been processed by training_manager
        """
        with self._lock:
            if not self.output_path.exists():
                return []
            
            courses = []
            for course_dir in self.output_path.iterdir():
                if course_dir.is_dir():
                    index_path = course_dir / "metadata" / "index.json"
                    if index_path.exists():
                        courses.append(course_dir.name)
            
            self.logger.info(f"[ContentAccessor] Available courses: {courses}")
            return sorted(courses)
    
    def health_check(self) -> dict[str, Any]:
        """
        Check health and status of ContentAccessor.
        
        Returns:
            Health status information including course count, module count, and cache status
        """
        with self._lock:
            try:
                available_courses = self.list_available_courses()
                total_modules = 0
                
                # Count total modules across all courses
                for course_id in available_courses:
                    course_metadata = self._get_course_index(course_id)
                    if course_metadata:
                        total_modules += len(course_metadata.get("modules", []))
                
                health_data = {
                    "status": "healthy",
                    "available_courses": len(available_courses),
                    "total_modules": total_modules,
                    "content_cache_size": len(self._content_cache),
                    "metadata_cache_size": len(self._metadata_cache),
                    "output_path": str(self.output_path),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.logger.info(f"[ContentAccessor] Health check: {health_data}")
                return health_data
                
            except Exception as e:
                self.logger.error(f"[ContentAccessor] Health check failed: {e!s}")
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    def _get_all_content_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all available content."""
        all_content = {}
        
        for course_id in self.list_available_courses():
            course_index = self._get_course_index(course_id)
            if course_index:
                modules = course_index.get("modules", [])
                for module in modules:
                    content_id = f"{course_id}:{module.get('module_id', 'unknown')}"
                    all_content[content_id] = {
                        **module,
                        "course_id": course_id
                    }
        
        return all_content
    
    def _get_course_index(self, course_id: str) -> dict[str, Any] | None:
        """Get course index from metadata cache or file."""
        cache_key = f"course_index:{course_id}"
        
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]
        
        index_path = self.output_path / course_id / "metadata" / "index.json"
        if not index_path.exists():
            return None
        
        try:
            with open(index_path, encoding='utf-8') as f:
                course_index = json.load(f)
                self._metadata_cache[cache_key] = course_index
                return course_index
        except (OSError, json.JSONDecodeError) as e:
            self.logger.error(f"[ContentAccessor] Error loading course index {index_path}: {e!s}")
            return None
    
    def _get_module_metadata(self, course_id: str, module_id: str) -> dict[str, Any] | None:
        """Get metadata for a specific module."""
        course_index = self._get_course_index(course_id)
        if not course_index:
            return None
        
        modules = course_index.get("modules", [])
        for module in modules:
            if module.get("module_id") == module_id:
                return {**module, "course_id": course_id}
        
        return None
    
    def _get_cleaned_transcript(self, course_id: str, module_id: str) -> str | None:
        """Get cleaned transcript content with caching."""
        cache_key = f"{course_id}:{module_id}"
        
        if cache_key in self._content_cache:
            return self._content_cache[cache_key]
        
        transcript_path = self.output_path / course_id / "cleaned_transcripts" / f"{module_id}.md"
        if not transcript_path.exists():
            self.logger.warning(f"[ContentAccessor] Transcript file not found: {transcript_path}")
            return None
        
        try:
            with open(transcript_path, encoding='utf-8') as f:
                content = f.read()
                self._content_cache[cache_key] = content
                return content
        except OSError as e:
            self.logger.error(f"[ContentAccessor] Error reading transcript {transcript_path}: {e!s}")
            return None
    
    def _calculate_relevance_score(self, metadata: dict[str, Any], keywords_lower: list[str]) -> float:
        """
        Calculate relevance score for content based on keyword matches.
        
        Scoring algorithm:
        - Title matches: 0.4 weight
        - Keywords matches: 0.3 weight  
        - Summary matches: 0.2 weight
        - Tags matches: 0.1 weight
        """
        if not keywords_lower:
            return 0.0
        
        title = metadata.get("title", "").lower()
        keywords = [kw.lower() for kw in metadata.get("keywords", [])]
        summary = metadata.get("summary", "").lower()
        tags = [tag.lower() for tag in metadata.get("tags", [])]
        
        # Calculate match scores for each field
        title_score = sum(1 for kw in keywords_lower if kw in title) / len(keywords_lower)
        keywords_score = sum(1 for kw in keywords_lower if any(kw in mk for mk in keywords)) / len(keywords_lower)
        summary_score = sum(1 for kw in keywords_lower if kw in summary) / len(keywords_lower)
        tags_score = sum(1 for kw in keywords_lower if any(kw in tag for tag in tags)) / len(keywords_lower)
        
        # Weighted relevance score
        relevance = (
            title_score * 0.4 +
            keywords_score * 0.3 +
            summary_score * 0.2 +
            tags_score * 0.1
        )
        
        return min(relevance, 1.0)  # Cap at 1.0
    
    def _create_content_preview(self, metadata: dict[str, Any]) -> str:
        """Create a content preview from metadata."""
        title = metadata.get("title", "Unknown")
        summary = metadata.get("summary", "")
        keywords = metadata.get("keywords", [])
        
        # Create preview
        preview_parts = [f"Title: {title}"]
        
        if summary:
            preview_text = summary[:150] + "..." if len(summary) > 150 else summary
            preview_parts.append(f"Summary: {preview_text}")
        
        if keywords:
            preview_parts.append(f"Keywords: {', '.join(keywords[:5])}")
        
        return " | ".join(preview_parts)
    
    def export_as_markdown(self, content_id: str) -> str | None:
        """
        Export content with metadata as Markdown with YAML frontmatter.
        
        This method provides structured Markdown output for EditingTeam integration
        and file_search workflow compatibility as specified by Codex.
        
        Args:
            content_id: Content identifier in format "course_id/module_id"
            
        Returns:
            Formatted Markdown string with YAML frontmatter and content body,
            or None if content not found
        """
        with self._lock:
            self.logger.info(f"[ContentAccessor] Exporting content as Markdown: {content_id}")
            
            try:
                # Get content and metadata
                content_data = self.get_content(content_id)
                if not content_data:
                    self.logger.warning(f"[ContentAccessor] Content not found for export: {content_id}")
                    return None
                
                # Extract full content and metadata
                full_content = content_data.get("full_content", "")
                content_metadata = content_data.get("metadata", {})
                
                # Get additional metadata for frontmatter
                all_content = self._get_all_content_metadata()
                raw_metadata = all_content.get(content_id, {})
                
                # Extract relevant metadata (combine both sources)
                title = content_metadata.get("title") or raw_metadata.get("title", "Unknown Title")
                course_id = content_metadata.get("source") or raw_metadata.get("course_id", "unknown")
                module_id = content_metadata.get("module_id") or raw_metadata.get("module_id", "unknown")
                keywords = content_metadata.get("keywords") or raw_metadata.get("keywords", [])
                tags = content_metadata.get("tags") or raw_metadata.get("tags", [])
                summary = content_metadata.get("summary") or raw_metadata.get("summary", "")
                word_count = raw_metadata.get("word_count", 0)
                estimated_duration = raw_metadata.get("estimated_duration_minutes", 0)
                created_at = content_metadata.get("created_at", datetime.now().isoformat())
                
                # Build YAML frontmatter with proper escaping
                escaped_title = title.replace('"', '\\"')
                frontmatter_lines = [
                    "---",
                    f"title: \"{escaped_title}\"",
                    f"content_id: \"{content_id}\"",
                    f"course_id: \"{course_id}\"",
                    f"module_id: \"{module_id}\"",
                    "content_type: \"training_transcript\"",
                    f"word_count: {word_count}",
                    f"estimated_duration_minutes: {estimated_duration}",
                    f"created_at: \"{created_at}\"",
                ]
                
                # Add keywords if available
                if keywords:
                    keywords_yaml = "[" + ", ".join(f'"{kw}"' for kw in keywords) + "]"
                    frontmatter_lines.append(f"keywords: {keywords_yaml}")
                
                # Add tags if available
                if tags:
                    tags_yaml = "[" + ", ".join(f'"{tag}"' for tag in tags) + "]"
                    frontmatter_lines.append(f"tags: {tags_yaml}")
                
                # Add summary if available
                if summary:
                    # Escape quotes and handle multiline
                    escaped_summary = summary.replace('"', '\\"').replace('\n', '\\n')
                    frontmatter_lines.append(f"summary: \"{escaped_summary}\"")
                
                frontmatter_lines.append("---")
                
                # Combine frontmatter and content
                markdown_content = "\n".join(frontmatter_lines) + "\n\n" + full_content
                
                self.logger.info(f"[ContentAccessor] Markdown export completed: {content_id} ({len(markdown_content)} chars)")
                return markdown_content
                
            except Exception as e:
                self.logger.error(f"[ContentAccessor] Error exporting Markdown for {content_id}: {e!s}")
                return None