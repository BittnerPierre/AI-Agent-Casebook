"""Temporary bridge for transcript_generator to access training data."""

import json
from datetime import datetime
from pathlib import Path

from .models import CourseMetadata, ModuleMetadata, SearchQuery, SearchResult


class TrainingDataBridge:
    """
    Temporary file-based bridge to access training manager outputs.
    
    Provides a clean interface for transcript_generator to access
    processed training data while the full knowledge database is
    being developed.
    """
    
    def __init__(self, output_base_path: str = "output"):
        self.output_path = Path(output_base_path)
    
    def list_available_courses(self) -> list[str]:
        """List all course IDs with processed data."""
        if not self.output_path.exists():
            return []
        return [
            d.name for d in self.output_path.iterdir() 
            if d.is_dir() and (d / "metadata" / "index.json").exists()
        ]
    
    def get_course_metadata(self, course_id: str) -> CourseMetadata | None:
        """Load course metadata from training manager output."""
        index_path = self.output_path / course_id / "metadata" / "index.json"
        if not index_path.exists():
            return None
            
        try:
            with open(index_path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        
        # Convert to standardized format
        modules = []
        for module_data in data.get("modules", []):
            modules.append(ModuleMetadata(
                module_id=module_data["module_id"],
                title=module_data["title"],
                summary=module_data["summary"],
                keywords=module_data["keywords"],
                tags=module_data["tags"],
                course_id=course_id,
                cleaned_transcript_path=f"output/{course_id}/cleaned_transcripts/{module_data['module_id']}.md",
                created_at=datetime.now(),  # Temp: no timestamp in current format
                updated_at=datetime.now(),
                word_count=module_data.get("word_count"),
                estimated_duration_minutes=module_data.get("estimated_duration_minutes")
            ))
        
        # Infer course type from structure
        course_type = "single-file" if len(modules) == 1 else "multi-module"
        
        return CourseMetadata(
            course_id=course_id,
            course_title=data["course_title"],
            course_type=course_type,
            modules=modules,
            total_modules=len(modules),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def get_module_metadata(self, course_id: str, module_id: str) -> ModuleMetadata | None:
        """Get metadata for a specific module."""
        course = self.get_course_metadata(course_id)
        if not course:
            return None
            
        for module in course.modules:
            if module.module_id == module_id:
                return module
        return None
    
    def get_cleaned_transcript(self, course_id: str, module_id: str) -> str | None:
        """Load cleaned transcript content."""
        transcript_path = self.output_path / course_id / "cleaned_transcripts" / f"{module_id}.md"
        if not transcript_path.exists():
            return None
            
        try:
            with open(transcript_path, encoding='utf-8') as f:
                return f.read()
        except OSError:
            return None
    
    def search_modules_by_keywords(self, keywords: list[str], limit: int = 10) -> list[ModuleMetadata]:
        """Simple keyword search across all courses."""
        results = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for course_id in self.list_available_courses():
            course = self.get_course_metadata(course_id)
            if course:
                for module in course.modules:
                    # Simple keyword matching in module content
                    searchable_text = ' '.join([
                        module.title,
                        module.summary,
                        ' '.join(module.keywords),
                        ' '.join(module.tags)
                    ]).lower()
                    
                    if any(kw in searchable_text for kw in keywords_lower):
                        results.append(module)
                        if len(results) >= limit:
                            return results
        return results
    
    def search_modules(self, query: SearchQuery) -> SearchResult:
        """Structured search for modules."""
        all_modules = []
        
        # Get all modules from specified courses or all courses
        course_ids = query.course_ids or self.list_available_courses()
        
        for course_id in course_ids:
            course = self.get_course_metadata(course_id)
            if course:
                all_modules.extend(course.modules)
        
        # Filter by module IDs if specified
        if query.module_ids:
            all_modules = [m for m in all_modules if m.module_id in query.module_ids]
        
        # Filter by keywords
        if query.keywords:
            keywords_lower = [kw.lower() for kw in query.keywords]
            filtered_modules = []
            for module in all_modules:
                searchable_text = ' '.join([
                    module.title,
                    module.summary,
                    ' '.join(module.keywords),
                    ' '.join(module.tags)
                ]).lower()
                
                if any(kw in searchable_text for kw in keywords_lower):
                    filtered_modules.append(module)
            all_modules = filtered_modules
        
        # Filter by tags
        if query.tags:
            tags_lower = [tag.lower() for tag in query.tags]
            all_modules = [
                m for m in all_modules 
                if any(tag.lower() in tags_lower for tag in m.tags)
            ]
        
        # Apply pagination
        total_count = len(all_modules)
        start_idx = query.offset
        end_idx = start_idx + query.limit
        paginated_modules = all_modules[start_idx:end_idx]
        
        return SearchResult(
            modules=paginated_modules,
            total_count=total_count,
            query=query
        )
    
    def get_related_modules(self, course_id: str, module_id: str, limit: int = 5) -> list[ModuleMetadata]:
        """Find modules related to the given module (simple implementation)."""
        base_module = self.get_module_metadata(course_id, module_id)
        if not base_module:
            return []
        
        # Use module keywords and tags to find related content
        search_keywords = base_module.keywords + base_module.tags
        related = self.search_modules_by_keywords(search_keywords, limit + 1)
        
        # Remove the original module from results
        return [m for m in related if m.module_id != module_id][:limit]