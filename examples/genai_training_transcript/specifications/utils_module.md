# Utils Module Specification

## Purpose
The `src/utils/` directory contains shared utilities that can be used across multiple modules in the project, promoting code reuse and maintaining separation of concerns.

## Current Contents

### transcript_preprocessor.py
- **Function**: `preprocess_transcript(module_filename, mcp_server) -> str`
- **Purpose**: LLM-based preprocessing of raw transcript files
- **Functionality**: 
  - Adds proper punctuation and sentence boundaries
  - Resolves misspellings and automatic translation errors
  - Segments content into coherent paragraphs
  - Outputs cleaned transcript as Markdown
- **Dependencies**: `agents` library for LLM integration

### metadata_extractor.py  
- **Function**: `extract_metadata(module_filename, cleaned_transcript, mcp_server) -> ModuleMetadata`
- **Purpose**: LLM-based metadata extraction from cleaned transcripts
- **Functionality**:
  - Generates concise summaries highlighting key concepts
  - Extracts topic-specific keywords
  - Identifies high-level topic tags
  - Returns structured metadata object
- **Dependencies**: `agents` library for LLM integration

## Usage Guidelines

### Import Pattern
```python
from utils.transcript_preprocessor import preprocess_transcript
from utils.metadata_extractor import extract_metadata
```

### Module Independence
- Utils are shared across modules but don't create circular dependencies
- Each utility function is self-contained and stateless
- MCP server integration allows for flexible storage backends

## Architecture Role

The utils module serves as a shared foundation for:
- **Training Manager**: Uses for data preparation and cleaning workflows
- **Transcript Generator**: Could potentially reuse for preprocessing steps
- **Future Modules**: Any module requiring transcript processing capabilities

## Migration Notes

These utilities were moved from `tools/` to `utils/` to:
1. Maintain training manager independence from transcript generator reorganization
2. Provide clear shared utility location
3. Enable reusability across multiple modules
4. Prevent import conflicts during codebase restructuring