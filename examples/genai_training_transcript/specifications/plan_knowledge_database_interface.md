# Plan: Knowledge Database Interface for Module Independence

## Problem Statement

The current architecture lacks **true module independence** between `training_manager` and `transcript_generator`. Analysis reveals:

### Current Coupling Issues
1. **Direct Cross-Module Coupling**: `run.py` imports from both modules
2. **Data Format Mismatch**: No standardized interface for knowledge access  
3. **Missing Bridge**: No way for transcript_generator to access training_manager outputs

### Architecture Violation
```python
# src/run.py - COUPLING VIOLATION
from training_manager.tools.transcript_preprocessor import preprocess_transcript  
from transcript_generator.tools.syllabus_loader import load_syllabus
# ... + 6 more transcript_generator imports
```

## Proposed Solution: Knowledge Database Interface

### 1. Long-term Architecture (Future Sprint)

#### Common Data Models
```python
# src/common/models.py
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
```

#### Abstract Interfaces
```python
# src/common/interfaces.py
from abc import ABC, abstractmethod

class KnowledgeDatabase(ABC):
    """Abstract interface for accessing training knowledge base."""
    
    @abstractmethod
    async def get_course_metadata(self, course_id: str) -> Optional[CourseMetadata]:
        pass
    
    @abstractmethod
    async def get_cleaned_transcript(self, module_id: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def search_modules(self, query: SearchQuery) -> SearchResult:
        pass
```

## 2. Temporary Solution: Direct File Access Bridge

### Problem: Immediate Independence Need
Agents working on `transcript_generator` need access to training data **NOW** while the full knowledge database is under development.

### Solution: Standardized File Access Interface

#### File Structure Schema
```
output/
└── <course_id>/
    ├── metadata/
    │   ├── index.json           # Course + modules metadata  
    │   └── modules/
    │       ├── <module_id>.json # Individual module metadata
    │       └── ...
    └── cleaned_transcripts/
        ├── <module_id>.md       # Cleaned transcript content
        └── ...
```

#### Bridge Interface Implementation
```python
# src/common/knowledge_bridge.py
"""Temporary bridge for transcript_generator to access training data."""

import os
import json
from typing import List, Optional
from pathlib import Path
from .models import CourseMetadata, ModuleMetadata

class TrainingDataBridge:
    """Temporary file-based bridge to access training manager outputs."""
    
    def __init__(self, output_base_path: str = "output"):
        self.output_path = Path(output_base_path)
    
    def list_available_courses(self) -> List[str]:
        """List all course IDs with processed data."""
        if not self.output_path.exists():
            return []
        return [
            d.name for d in self.output_path.iterdir() 
            if d.is_dir() and (d / "metadata" / "index.json").exists()
        ]
    
    def get_course_metadata(self, course_id: str) -> Optional[CourseMetadata]:
        """Load course metadata from training manager output."""
        index_path = self.output_path / course_id / "metadata" / "index.json"
        if not index_path.exists():
            return None
            
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
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
                updated_at=datetime.now()
            ))
        
        return CourseMetadata(
            course_id=course_id,
            course_title=data["course_title"],
            course_type="multi-module",  # Temp: infer from module count
            modules=modules,
            total_modules=len(modules),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def get_cleaned_transcript(self, course_id: str, module_id: str) -> Optional[str]:
        """Load cleaned transcript content."""
        transcript_path = self.output_path / course_id / "cleaned_transcripts" / f"{module_id}.md"
        if not transcript_path.exists():
            return None
            
        with open(transcript_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def search_modules_by_keywords(self, keywords: List[str], limit: int = 10) -> List[ModuleMetadata]:
        """Simple keyword search across all courses."""
        results = []
        for course_id in self.list_available_courses():
            course = self.get_course_metadata(course_id)
            if course:
                for module in course.modules:
                    # Simple keyword matching
                    if any(kw.lower() in ' '.join(module.keywords + module.tags + [module.summary]).lower() 
                           for kw in keywords):
                        results.append(module)
                        if len(results) >= limit:
                            return results
        return results
```

#### Usage in Transcript Generator
```python
# src/transcript_generator/tools/knowledge_retriever.py
"""Knowledge retrieval tool for transcript generator."""

from common.knowledge_bridge import TrainingDataBridge
from common.models import ModuleMetadata
from typing import List

class KnowledgeRetriever:
    """Retrieve training data for transcript generation."""
    
    def __init__(self, output_path: str = "output"):
        self.bridge = TrainingDataBridge(output_path)
    
    async def get_related_content(self, topic_keywords: List[str]) -> List[str]:
        """Get relevant transcript content for given topics."""
        modules = self.bridge.search_modules_by_keywords(topic_keywords)
        content = []
        
        for module in modules:
            course_id = module.course_id
            transcript = self.bridge.get_cleaned_transcript(course_id, module.module_id)
            if transcript:
                content.append({
                    "module_id": module.module_id,
                    "title": module.title,
                    "content": transcript[:1000],  # First 1000 chars for context
                    "keywords": module.keywords,
                    "tags": module.tags
                })
        
        return content
    
    async def get_course_outline(self, course_id: str) -> Optional[dict]:
        """Get course structure for planning."""
        course = self.bridge.get_course_metadata(course_id)
        if not course:
            return None
            
        return {
            "course_id": course.course_id,
            "title": course.course_title,
            "modules": [
                {
                    "module_id": m.module_id,
                    "title": m.title,
                    "summary": m.summary,
                    "keywords": m.keywords
                }
                for m in course.modules
            ]
        }
```

## 3. Enhanced Training Manager Output Format

### Current Format Issues
The current `index.json` format needs enhancement for better compatibility:

#### Enhanced Schema
```json
{
  "course_id": "COURSE001",
  "course_title": "Advanced AI Training",
  "course_type": "multi-module",
  "created_at": "2025-06-06T14:30:00Z",
  "updated_at": "2025-06-06T14:30:00Z",
  "total_modules": 3,
  "modules": [
    {
      "module_id": "module1",
      "title": "Introduction to AI",
      "summary": "Basic concepts and foundations",
      "keywords": ["AI", "machine learning", "neural networks"],
      "tags": ["beginner", "foundational"],
      "course_id": "COURSE001",
      "cleaned_transcript_path": "output/COURSE001/cleaned_transcripts/module1.md",
      "created_at": "2025-06-06T14:30:00Z",
      "updated_at": "2025-06-06T14:30:00Z",
      "word_count": 2500,
      "estimated_duration_minutes": 15
    }
  ],
  "statistics": {
    "total_word_count": 7500,
    "total_estimated_duration_minutes": 45,
    "most_common_keywords": ["AI", "learning", "data"],
    "coverage_tags": ["beginner", "intermediate"]
  }
}
```

### Migration Path Benefits
1. **Forward Compatibility**: Bridge interface matches future KnowledgeDatabase API
2. **Gradual Migration**: Can swap bridge for MCP implementation later
3. **Testing Independence**: Each module can be tested separately
4. **Agent Autonomy**: transcript_generator agent can work independently

## 4. Implementation Roadmap

### Phase 1: Immediate (Current Sprint)
- [ ] Create `src/common/knowledge_bridge.py` - Temporary file access bridge
- [ ] Create `src/common/models.py` - Shared data models  
- [ ] Update training_manager to output enhanced JSON format
- [ ] Create `transcript_generator/tools/knowledge_retriever.py`

### Phase 2: Independence (Next Sprint)
- [ ] Update transcript_generator tools to use KnowledgeRetriever
- [ ] Remove direct imports between modules in `run.py`
- [ ] Add integration tests for bridge interface
- [ ] Validate each module works independently

### Phase 3: Full Knowledge Database (Future Sprint)
- [ ] Implement MCP-based knowledge server
- [ ] Create abstract interfaces in `src/common/interfaces.py`
- [ ] Migrate bridge to use MCP protocol
- [ ] Add search and indexing capabilities

## 5. Agent Collaboration Benefits

### Immediate Independence
- **Training Manager Agent**: Can work on data preparation features
- **Transcript Generator Agent**: Can work on content generation with bridge access
- **Architecture Agent**: Can work on knowledge database design

### Clean Handoff Protocol
```python
# Training Manager → Knowledge Database
training_manager.run() → Enhanced index.json + cleaned transcripts

# Knowledge Database ← Transcript Generator  
bridge.get_course_metadata() ← transcript_generator tools
```

### Testing Strategy
- **Unit Tests**: Each bridge method tested independently
- **Integration Tests**: End-to-end workflow via bridge
- **Mock Tests**: transcript_generator with mock bridge data

## Acceptance Criteria

### Phase 1 (Immediate)
1. ✅ `TrainingDataBridge` provides clean file access interface
2. ✅ Enhanced JSON schema with timestamps and metadata
3. ✅ `transcript_generator` can access training data via bridge
4. ✅ No direct imports between training_manager and transcript_generator
5. ✅ Each module can run and test independently

### Phase 2 (Independence)
1. ✅ `run.py` uses bridge interface instead of direct imports
2. ✅ All transcript_generator tools use KnowledgeRetriever
3. ✅ Integration tests validate full workflow
4. ✅ Agents can work on modules without conflicts

### Phase 3 (Full Solution)
1. ✅ MCP-based knowledge database replaces file bridge
2. ✅ Abstract interfaces allow multiple implementations
3. ✅ Search and indexing provide advanced retrieval
4. ✅ Performance and scalability requirements met

This plan provides **immediate module independence** while building toward the full knowledge database architecture!