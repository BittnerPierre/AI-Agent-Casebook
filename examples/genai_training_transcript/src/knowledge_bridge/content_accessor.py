"""
Content Accessor for Knowledge Bridge

Provides searchable access to processed content from training_manager.
Implements the interface for US-002 Operational Training Manager Content Access.

Author: Sprint 1 Development Team
Reference: US-002 Operational Training Manager Content Access
"""

import threading
from datetime import datetime
from typing import Any

from common.knowledge_bridge import TrainingDataBridge
from common.models import ModuleMetadata


class ContentAccessor:
    """
    Content accessor for processed training manager content.
    
    Provides searchable, accessible processed content for Knowledge Bridge MCP interface.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, output_base_path: str = "output"):
        """Initialize content accessor with training manager output path"""
        self.bridge = TrainingDataBridge(output_base_path)
        self._lock = threading.RLock()  # Thread-safe access
        self._content_cache: dict[str, str] = {}  # Simple content caching
        print(f"[ContentAccessor] Initialized with base path: {output_base_path}")
    
    def get_by_keywords(self, keywords: list[str], max_results: int = 10) -> list[dict[str, Any]]:
        """
        Search content by keywords and return structured results.
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of content matches with metadata
        """
        with self._lock:
            print(f"[ContentAccessor] Searching for keywords: {keywords}")
            
            # Use bridge to search modules
            modules = self.bridge.search_modules_by_keywords(keywords, max_results)
            
            # Convert to ContentMatch format for MCP interface
            content_matches = []
            for module in modules:
                # Calculate relevance score based on keyword matches
                relevance_score = self._calculate_relevance(module, keywords)
                
                content_match = {
                    "content_id": f"{module.course_id}:{module.module_id}",
                    "title": module.title,
                    "relevance_score": relevance_score,
                    "content_preview": self._create_preview(module),
                    "metadata": {
                        "source": module.course_id,
                        "content_type": "training_transcript",
                        "tags": module.tags,
                        "keywords": module.keywords,
                        "module_id": module.module_id,
                        "word_count": module.word_count,
                        "duration_minutes": module.estimated_duration_minutes
                    }
                }
                content_matches.append(content_match)
            
            print(f"[ContentAccessor] Found {len(content_matches)} content matches")
            return content_matches
    
    def get_content(self, content_id: str) -> dict[str, Any] | None:
        """
        Get full content by content_id.
        
        Args:
            content_id: Content identifier in format "course_id:module_id"
            
        Returns:
            Full content data or None if not found
        """
        with self._lock:
            print(f"[ContentAccessor] Getting content for ID: {content_id}")
            
            try:
                # Parse content_id
                if ":" not in content_id:
                    print(f"[ContentAccessor] Invalid content_id format: {content_id}")
                    return None
                
                course_id, module_id = content_id.split(":", 1)
                
                # Get module metadata
                module = self.bridge.get_module_metadata(course_id, module_id)
                if not module:
                    print(f"[ContentAccessor] Module not found: {content_id}")
                    return None
                
                # Get full content (with caching)
                cache_key = content_id
                if cache_key in self._content_cache:
                    full_content = self._content_cache[cache_key]
                else:
                    full_content = self.bridge.get_cleaned_transcript(course_id, module_id)
                    if full_content:
                        self._content_cache[cache_key] = full_content
                
                if not full_content:
                    print(f"[ContentAccessor] Content not found: {content_id}")
                    return None
                
                content_data = {
                    "content_id": content_id,
                    "full_content": full_content,
                    "metadata": {
                        "title": module.title,
                        "summary": module.summary,
                        "source": course_id,
                        "content_type": "training_transcript",
                        "tags": module.tags,
                        "keywords": module.keywords,
                        "module_id": module_id,
                        "word_count": module.word_count,
                        "duration_minutes": module.estimated_duration_minutes,
                        "created_at": module.created_at.isoformat(),
                        "updated_at": module.updated_at.isoformat()
                    }
                }
                
                print(f"[ContentAccessor] Retrieved content: {content_id} ({len(full_content)} chars)")
                return content_data
                
            except Exception as e:
                print(f"[ContentAccessor] Error getting content {content_id}: {e!s}")
                return None
    
    def _calculate_relevance(self, module: ModuleMetadata, keywords: list[str]) -> float:
        """Calculate relevance score for a module based on keyword matches"""
        keywords_lower = [kw.lower() for kw in keywords]
        
        # Create searchable text from module
        searchable_text = ' '.join([
            module.title,
            module.summary,
            ' '.join(module.keywords),
            ' '.join(module.tags)
        ]).lower()
        
        # Count keyword matches
        matches = sum(1 for kw in keywords_lower if kw in searchable_text)
        
        # Calculate relevance as percentage of keywords found
        relevance = matches / len(keywords) if keywords else 0.0
        
        # Boost relevance for title matches
        title_lower = module.title.lower()
        title_matches = sum(1 for kw in keywords_lower if kw in title_lower)
        if title_matches > 0:
            relevance += 0.2 * (title_matches / len(keywords))
        
        # Cap at 1.0
        return min(relevance, 1.0)
    
    def _create_preview(self, module: ModuleMetadata) -> str:
        """Create a content preview from module metadata"""
        preview_parts = [
            f"Title: {module.title}",
            f"Summary: {module.summary[:200]}..." if len(module.summary) > 200 else f"Summary: {module.summary}"
        ]
        
        if module.keywords:
            preview_parts.append(f"Keywords: {', '.join(module.keywords[:5])}")
        
        if module.word_count:
            preview_parts.append(f"Length: ~{module.word_count} words")
        
        if module.estimated_duration_minutes:
            preview_parts.append(f"Duration: ~{module.estimated_duration_minutes} minutes")
        
        return " | ".join(preview_parts)
    
    def health_check(self) -> dict[str, Any]:
        """Check health of content accessor"""
        with self._lock:
            available_courses = self.bridge.list_available_courses()
            total_modules = 0
            
            for course_id in available_courses:
                course = self.bridge.get_course_metadata(course_id)
                if course:
                    total_modules += len(course.modules)
            
            return {
                "status": "healthy",
                "available_courses": len(available_courses),
                "total_modules": total_modules,
                "cache_size": len(self._content_cache),
                "timestamp": datetime.now().isoformat()
            }