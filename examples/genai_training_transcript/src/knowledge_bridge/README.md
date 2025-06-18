# Knowledge Bridge MCP Interface

**Implementation of US-001: Knowledge Database MCP Interface**

## Overview

The Knowledge Bridge MCP Interface provides a standardized Model Context Protocol (MCP) server for accessing processed training content from the training_manager. This implementation enables Research Team agents to query the knowledge base using structured operations.

## Architecture

```
Research Agent → KnowledgeMCPServer → ContentAccessor → TrainingDataBridge → Local Files
```

### Components

1. **KnowledgeMCPServer** (`mcp_interface.py`)
   - Main MCP server implementing the protocol operations
   - Thread-safe for concurrent agent queries
   - Provides structured JSON schemas for all operations

2. **ContentAccessor** (`content_accessor.py`) 
   - Searchable access layer for processed training content
   - Keyword-based search with relevance scoring
   - Content caching for improved performance

3. **TrainingDataBridge** (from `common/knowledge_bridge.py`)
   - File-based access to training_manager output
   - Existing bridge for backward compatibility

## MCP Operations

### `lookup_content(keywords, learning_objectives, max_results)`
Searches knowledge base using keywords and optional learning objectives.

**Input:**
```json
{
  "keywords": ["machine learning", "algorithms"],
  "learning_objectives": ["Learn basic ML concepts"],
  "max_results": 10
}
```

**Output:**
```json
{
  "query_id": "query_1_1703123456",
  "total_matches": 2,
  "content_matches": [
    {
      "content_id": "course_id:module_id",
      "title": "Introduction to Machine Learning",
      "relevance_score": 0.85,
      "content_preview": "Machine learning is a subset of AI...",
      "metadata": {
        "source": "course_id",
        "content_type": "training_transcript",
        "tags": ["beginner", "ml"],
        "keywords": ["machine learning", "algorithms"]
      }
    }
  ]
}
```

### `read_content(content_id)`
Retrieves full content by content_id.

**Input:**
```json
{
  "content_id": "course_id:module_id"
}
```

**Output:**
```json
{
  "content_id": "course_id:module_id",
  "full_content": "# Module Title\n\nFull transcript content...",
  "metadata": {
    "title": "Module Title",
    "summary": "Module summary",
    "word_count": 2500,
    "duration_minutes": 45
  }
}
```

### `health_check()`
Returns server health status and statistics.

**Output:**
```json
{
  "server_status": "healthy",
  "mcp_protocol": "1.0",
  "total_queries": 42,
  "content_accessor": {
    "available_courses": 3,
    "total_modules": 15
  }
}
```

## Usage Examples

### Basic MCP Server Usage
```python
from knowledge_bridge.mcp_interface import create_knowledge_mcp_server

# Initialize MCP server
mcp_server = create_knowledge_mcp_server("output")

# Search for content
response = mcp_server.lookup_content(
    keywords=["machine learning", "algorithms"],
    learning_objectives=["Learn basic ML concepts"],
    max_results=5
)

# Get full content
content_data = mcp_server.read_content("course_id:module_id")
```

### Research Team Integration Pattern
```python
def research_syllabus_section(mcp_server, syllabus_section):
    """Example Research Team usage pattern"""
    
    # Extract search criteria from syllabus
    keywords = syllabus_section.get('key_topics', [])
    learning_objectives = syllabus_section.get('learning_objectives', [])
    
    # Query knowledge base
    response = mcp_server.lookup_content(
        keywords=keywords,
        learning_objectives=learning_objectives,
        max_results=10
    )
    
    # Process results into research notes
    research_notes = {
        "section_id": syllabus_section['section_id'],
        "topic": syllabus_section['title'],
        "knowledge_references": [],
        "research_summary": ""
    }
    
    for match in response.get('content_matches', []):
        # Get full content for high-relevance matches
        if match.get('relevance_score', 0) > 0.7:
            content_data = mcp_server.read_content(match['content_id'])
            if content_data:
                research_notes['knowledge_references'].append({
                    "content_id": match['content_id'],
                    "key_points": extract_key_points(content_data['full_content'])
                })
    
    return research_notes
```

## Integration Points

### With Training Manager
- Reads processed content from training_manager output directory
- Uses existing `TrainingDataBridge` for file access
- Maintains compatibility with current preprocessing pipeline

### With Research Team (US-003)
- Provides structured knowledge queries for content research
- Returns relevance-scored content matches
- Supports research note generation workflow

### With MCP Protocol
- Implements standard MCP server operations
- Provides JSON schemas for all data types
- Thread-safe for concurrent agent access

## Configuration

The MCP server requires the training_manager output directory:

```python
# Default configuration
mcp_server = create_knowledge_mcp_server("output")

# Custom output path
mcp_server = create_knowledge_mcp_server("/path/to/training/data")
```

## Testing

Run the test suite:
```bash
pytest examples/genai_training_transcript/tests/test_knowledge_mcp.py -v
```

Run the example demo:
```bash
python examples/genai_training_transcript/examples/knowledge_mcp_example.py
```

## Sprint 1 Scope

**Current Implementation:**
- ✅ File-based knowledge storage
- ✅ Keyword-based search with relevance scoring
- ✅ MCP protocol operations (lookup_content, read_content, health_check)
- ✅ Thread-safe concurrent access
- ✅ JSON schemas for all operations
- ✅ Integration with existing training_manager output

**Future Enhancements (Sprint 2+):**
- Vector embeddings for semantic search
- Graph-based knowledge relationships (GraphRAG)
- Real-time content indexing
- Advanced relevance algorithms
- Content versioning and updates

## Dependencies

- **Training Manager**: Requires preprocessed content in output directory
- **MCP Protocol**: Standard Model Context Protocol compliance
- **Thread Safety**: Uses threading.RLock for concurrent access
- **JSON Schemas**: Structured data validation and documentation

---

This implementation provides the foundation for knowledge-based content research while maintaining KISS principles for Sprint 1 execution.