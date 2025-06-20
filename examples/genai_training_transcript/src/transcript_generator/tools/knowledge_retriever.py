"""Knowledge retrieval tool for transcript generator."""

import os
import sys
from typing import Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.knowledge_bridge import TrainingDataBridge
from common.models import SearchQuery


class KnowledgeRetriever:
    """
    Retrieve training data for transcript generation.
    
    Provides clean interface for transcript_generator tools to access
    processed training data without direct coupling to training_manager.
    """
    
    def __init__(self, knowledge_db_path: str = "knowledge_db"):
        self.bridge = TrainingDataBridge(knowledge_db_path)
    
    async def get_related_content(self, topic_keywords: list[str], limit: int = 5) -> list[dict[str, Any]]:
        """Get relevant transcript content for given topics."""
        modules = self.bridge.search_modules_by_keywords(topic_keywords, limit)
        content = []
        
        for module in modules:
            transcript = self.bridge.get_cleaned_transcript(module.course_id, module.module_id)
            if transcript:
                content.append({
                    "module_id": module.module_id,
                    "course_id": module.course_id,
                    "title": module.title,
                    "summary": module.summary,
                    "content_preview": transcript[:1000],  # First 1000 chars for context
                    "full_content": transcript,
                    "keywords": module.keywords,
                    "tags": module.tags,
                    "word_count": module.word_count,
                    "estimated_duration": module.estimated_duration_minutes
                })
        
        return content
    
    async def get_course_outline(self, course_id: str) -> dict[str, Any] | None:
        """Get course structure for planning."""
        course = self.bridge.get_course_metadata(course_id)
        if not course:
            return None
            
        return {
            "course_id": course.course_id,
            "title": course.course_title,
            "type": course.course_type,
            "total_modules": course.total_modules,
            "modules": [
                {
                    "module_id": m.module_id,
                    "title": m.title,
                    "summary": m.summary,
                    "keywords": m.keywords,
                    "tags": m.tags,
                    "word_count": m.word_count,
                    "estimated_duration": m.estimated_duration_minutes
                }
                for m in course.modules
            ]
        }
    
    async def search_by_topic(self, 
                             keywords: list[str] | None = None,
                             tags: list[str] | None = None,
                             course_ids: list[str] | None = None,
                             limit: int = 10) -> list[dict[str, Any]]:
        """Advanced search for relevant training content."""
        query = SearchQuery(
            keywords=keywords,
            tags=tags,
            course_ids=course_ids,
            limit=limit
        )
        
        result = self.bridge.search_modules(query)
        
        # Enrich results with transcript content
        enriched_results = []
        for module in result.modules:
            transcript = self.bridge.get_cleaned_transcript(module.course_id, module.module_id)
            enriched_results.append({
                "module_id": module.module_id,
                "course_id": module.course_id,
                "title": module.title,
                "summary": module.summary,
                "keywords": module.keywords,
                "tags": module.tags,
                "content_available": transcript is not None,
                "content_preview": transcript[:500] if transcript else None,
                "word_count": module.word_count,
                "estimated_duration": module.estimated_duration_minutes
            })
        
        return enriched_results
    
    async def get_full_transcript(self, course_id: str, module_id: str) -> str | None:
        """Get full cleaned transcript for a specific module."""
        return self.bridge.get_cleaned_transcript(course_id, module_id)
    
    async def get_similar_modules(self, course_id: str, module_id: str, limit: int = 3) -> list[dict[str, Any]]:
        """Find modules with similar content or topics."""
        related_modules = self.bridge.get_related_modules(course_id, module_id, limit)
        
        results = []
        for module in related_modules:
            transcript = self.bridge.get_cleaned_transcript(module.course_id, module.module_id)
            results.append({
                "module_id": module.module_id,
                "course_id": module.course_id,
                "title": module.title,
                "summary": module.summary,
                "keywords": module.keywords,
                "tags": module.tags,
                "similarity_reason": f"Shares keywords: {', '.join(module.keywords[:3])}",
                "content_preview": transcript[:300] if transcript else None
            })
        
        return results
    
    async def list_available_courses(self) -> list[dict[str, Any]]:
        """List all courses with processed training data."""
        course_ids = self.bridge.list_available_courses()
        courses = []
        
        for course_id in course_ids:
            course = self.bridge.get_course_metadata(course_id)
            if course:
                courses.append({
                    "course_id": course.course_id,
                    "title": course.course_title,
                    "type": course.course_type,
                    "total_modules": course.total_modules,
                    "module_count": len(course.modules),
                    "available_keywords": list(set([
                        kw for module in course.modules for kw in module.keywords
                    ])),
                    "available_tags": list(set([
                        tag for module in course.modules for tag in module.tags
                    ]))
                })
        
        return courses
    
    async def get_knowledge_statistics(self) -> dict[str, Any]:
        """Get overview statistics of available training knowledge."""
        courses = await self.list_available_courses()
        
        total_modules = sum(course["module_count"] for course in courses)
        all_keywords = set()
        all_tags = set()
        
        for course in courses:
            all_keywords.update(course["available_keywords"])
            all_tags.update(course["available_tags"])
        
        return {
            "total_courses": len(courses),
            "total_modules": total_modules,
            "unique_keywords": len(all_keywords),
            "unique_tags": len(all_tags),
            "most_common_keywords": sorted(list(all_keywords))[:20],
            "available_tags": sorted(list(all_tags)),
            "courses_by_type": {
                course_type: len([c for c in courses if c["type"] == course_type])
                for course_type in set(course["type"] for course in courses)
            }
        }