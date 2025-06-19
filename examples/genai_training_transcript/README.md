# Training Course Manager (Sprint 0)

This tool preprocesses raw `.txt` transcripts into cleaned Markdown files and generates a metadata index for modules.

## Prerequisites

- [Node.js](https://nodejs.org/) and [npx](https://www.npmjs.com/package/npx)
- The `@modelcontextprotocol/server-filesystem` package (installed automatically by `npx`)

## Launching the MCP filesystem server

You can manually start the file server:

```bash
npx @modelcontextprotocol/server-filesystem <path/to/course-directory>
```

## Launching the MCP Evernote server (TypeScript)

Set the environment variable `EVERNOTE_TOKEN` to a valid Evernote developer token and ensure Node.js is installed.

Clone the MCP servers repository and install dependencies:

```bash
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/filesystem
npm install
```

Start the Evernote plugin:

```bash
npm run start -- --plugin evernote --token "$EVERNOTE_TOKEN"
```

## Usage

```bash
poetry run python run_training_manager.py \
  --course-path <path/to/data/training_courses/<course_id> - <course_name>> \
  [--mcp-endpoint <uri>] [--overwrite]
```

- `--course-path`: Path to the course directory (e.g. `data/training_courses/<course_id> - <course_name>`).
- `--mcp-endpoint`: URI for the MCP server endpoint (defaults to `stdio://` or reads `MCP_ENDPOINT`).
  To use Evernote, specify `evernote://` and ensure `EVERNOTE_TOKEN` is set.
- `--overwrite`: Overwrite existing cleaned transcripts and metadata files; skip them by default.

Original `.txt` source files are never modified or deleted.

## Running Tests

Unit tests for transcript preprocessing and metadata extraction require only dummy LLM invocations and do not depend on actual transcript files.
Run tests with:

```bash
poetry run pytest -q --disable-warnings --maxfail=1
```

Or, to scope testing to this project directory, use the bundled script:

```bash
bash test.sh
```

# GenAI Training Transcript Generator

A multi-agent system for generating comprehensive training course transcripts using LLMs, MCP (Model Context Protocol), and Response API integration.

## Architecture Overview

This project implements a hierarchical multi-agent approach for course content generation:

- **Research Team**: Aggregates knowledge from existing training materials
- **EditingTeam**: Synthesizes content using Response API file_search ✨ **NEW: US-004**
- **Editorial Finalizer**: Quality control and final content polishing
- **Course Authoring**: Final assembly and review

## Recent Updates

### 🚀 US-004: Response API Content Synthesis (Sprint 1 - Week 2)

**New EditingTeam Implementation** - Multi-agent editing team using OpenAI Response API file_search for advanced content synthesis.

#### Key Features:

- **Multi-step synthesis workflow**: Documentalist → Writer → Reviewer → Script Strategist
- **Response API file_search integration**: Combines syllabus + agenda + research notes for context-aware generation
- **Agent feedback loops**: Iterative improvement through agent collaboration
- **Training course guidelines**: Applies pedagogical best practices automatically
- **Robust error handling**: Graceful fallback and resource cleanup

#### Interface:

```python
from transcript_generator.tools.editing_team import EditingTeam

# Initialize with OpenAI API key
editing_team = EditingTeam(
    api_key="your-openai-api-key",
    model="gpt-4o-mini",
    max_revisions=2
)

# Prepare research data
research_data = {
    'target_section': 'Introduction to Machine Learning',
    'syllabus': {...},
    'agenda': [...],
    'research_notes': {...}
}

# Synthesize chapter content
chapter_draft = editing_team.synthesize_chapter(research_data)
print(f"Generated: {chapter_draft.section_id}")
print(f"Content length: {len(chapter_draft.content)} characters")
```

#### Integration Points:

- **Consumes**: `research_notes/` from Research Team (US-003)
- **Produces**: `chapter_drafts/` for Editorial Finalizer (US-005)
- **Uses**: Response API file_search for multi-step RAG synthesis

#### Testing:

```bash
# Unit tests
python -m pytest tests/test_editing_team.py -v

# Integration test (simulation mode)
python integration_test_editing_team.py

# Full integration test (requires OPENAI_API_KEY)
export OPENAI_API_KEY="your-key"
python integration_test_editing_team.py
```

## Project Structure

```
src/
├── transcript_generator/
│   ├── tools/
│   │   ├── editing_team.py          # 🆕 US-004 EditingTeam implementation
│   │   ├── research_team.py         # Research aggregation
│   │   ├── planner.py              # Syllabus refinement
│   │   └── transcript_generator.py  # Final generation
│   ├── guidelines/
│   │   └── training_course_guidelines.md  # Pedagogical guidelines
│   └── editorial_finalizer.py       # Quality control
├── knowledge_bridge/
│   ├── mcp_interface.py            # MCP client interface
│   └── content_accessor.py         # Content retrieval
└── training_manager/
    └── core.py                     # Main orchestration

tests/
├── test_editing_team.py            # 🆕 US-004 comprehensive tests
├── test_response_api_file_search.py # Response API integration patterns
└── integration_test_editing_team.py # 🆕 End-to-end workflow test

examples/
└── response_api_file_search_example.py # US-011 implementation patterns
```

## Configuration

Copy and customize the configuration:

```bash
cp config.yaml.example config.yaml
```

Key settings:

```yaml
# Input paths
syllabus_path: syllabus.md
raw_transcripts_dir: data/training_courses

# Output directories
research_notes_dir: research_notes
chapter_drafts_dir: chapter_drafts # 🆕 US-004 output
drafts_dir: drafts
output_dir: output

# EditingTeam settings
max_revisions: 2
openai_model: gpt-4o-mini
```

## Environment Variables

Required environment variables:

```bash
# OpenAI API (for EditingTeam US-004)
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Custom project ID
export OPENAI_PROJECT_ID="proj_UWuOPp9MOKrOCtZABSCTY4Um"
```

## Usage Examples

### Basic Usage (Legacy Compatible)

```python
from transcript_generator.tools.editing_team import edit_chapters

# Legacy function still works with new implementation
research_notes = {"Module 1": "Research content..."}
config = {"max_revisions": 2}

drafts = edit_chapters(research_notes, config)
print(f"Generated {len(drafts)} chapter drafts")
```

### Advanced Usage (New EditingTeam Class)

```python
from transcript_generator.tools.editing_team import EditingTeam

# Initialize with custom settings
editing_team = EditingTeam(
    model="gpt-4o-mini",
    max_revisions=3,
    expires_after_days=7
)

# Comprehensive research data structure
research_data = {
    'target_section': 'Advanced Topics',
    'syllabus': {
        'title': 'Course Title',
        'learning_objectives': ['Objective 1', 'Objective 2'],
        'key_topics': ['Topic A', 'Topic B']
    },
    'agenda': [
        {
            'title': 'Module Title',
            'duration_minutes': 90,
            'topics': ['Subtopic 1', 'Subtopic 2']
        }
    ],
    'research_notes': {
        'Module Title': {
            'section1': 'Content for section 1',
            'section2': 'Content for section 2'
        }
    }
}

# Generate high-quality chapter content
chapter_draft = editing_team.synthesize_chapter(research_data)

# Access results
print(f"Section: {chapter_draft.section_id}")
print(f"Content: {chapter_draft.content}")

# Save to JSON for next pipeline stage
output_data = chapter_draft.to_dict()
```

### Integration Test

```bash
# Run comprehensive integration test
python integration_test_editing_team.py
```

Expected output:

```
🚀 Running full integration test with OpenAI API

1️⃣ Creating Comprehensive Research Data
   ✅ Research data created
   📚 Syllabus: Advanced Machine Learning for Practitioners

2️⃣ Initializing EditingTeam
   ✅ EditingTeam initialized with OpenAI API

3️⃣ Executing Chapter Synthesis
   ✅ Chapter synthesis completed
   ⏱️  Processing time: 45.23 seconds

4️⃣ Validating Chapter Draft Structure
   ✅ All expected content elements present
   ✅ Schema compliance verified

5️⃣ Simulating File Operations MCP Integration
   ✅ Chapter draft saved to: chapter_drafts/introduction_to_machine_learning.json
   🔗 Integration point validated for Editorial Finalizer

🎉 EditingTeam Integration Test PASSED
   ✅ US-004 implementation fully validated
```

## Sprint Planning Status

### ✅ Completed (Sprint 1 - Week 2)

- **US-004**: Response API Content Synthesis - EditingTeam implementation with multi-step synthesis
- **US-011**: Response API File_Search Integration Pattern - Working examples and test patterns

### 🔄 In Progress (Sprint 1 - Week 2)

- **US-003**: Research Team Knowledge Integration - Research aggregation with MCP
- **US-005**: Editorial Finalizer Misconduct Tracking - Quality control system

### 📋 Planned (Sprint 1 - Week 3+)

- **US-006**: Component Integration Orchestrator - End-to-end workflow management
- **US-012**: LangSmith Post-Execution Metadata Integration - Evaluation and monitoring

## Dependencies

### Required Python Packages

```bash
pip install openai>=1.0.0
pip install python-dotenv
pip install pydantic
pip install pytest  # for testing
```

### External Services

- **OpenAI API**: Required for EditingTeam Response API file_search
- **MCP Servers**: Knowledge Bridge and File Operations (optional for basic usage)

## Development

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# EditingTeam specific tests
python -m pytest tests/test_editing_team.py -v

# Integration tests
python integration_test_editing_team.py
python integration_test_response_api_file_search.py
```

### Adding New Features

1. Follow the multi-agent pattern established in `editing_team.py`
2. Use structured logging with `logger.info()`, `logger.error()`, etc.
3. Include comprehensive error handling and resource cleanup
4. Write both unit tests and integration tests
5. Update this README with new features

## Architecture Decisions

### Why Response API file_search?

- **Multi-document context**: Combines syllabus + agenda + research notes seamlessly
- **Semantic search**: Finds relevant information across large document sets
- **Scalable**: Handles varying amounts of research material efficiently
- **Quality**: Leverages OpenAI's advanced reasoning for content synthesis

### Why Multi-Agent Approach?

- **Separation of concerns**: Each agent has a specific role (Documentalist, Writer, Reviewer, Script Strategist)
- **Quality through iteration**: Agent feedback loops improve content quality
- **Modularity**: Easy to modify or replace individual agents
- **Pedagogical focus**: Each agent applies specific educational best practices

### Why File-based Integration?

- **MCP compatibility**: Integrates with File Operations MCP for production deployment
- **Debugging**: Easy to inspect intermediate outputs
- **Resilience**: Pipeline can recover from partial failures
- **Monitoring**: Clear visibility into each processing stage

## Troubleshooting

### Common Issues

**OpenAI API Key Error**

```
ValueError: OPENAI_API_KEY environment variable required
```

Solution: Set the environment variable or pass it explicitly:

```bash
export OPENAI_API_KEY="your-key"
```

**File Upload Errors**

```
File upload failed: <error details>
```

Solution: Check internet connection and API quotas. The system will automatically retry and clean up resources.

**Content Quality Issues**

- Increase `max_revisions` parameter for more agent feedback loops
- Verify research notes contain sufficient detail
- Check that training guidelines are loaded correctly

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('transcript_generator.tools.editing_team').setLevel(logging.DEBUG)
```

### Performance Optimization

- Use `gpt-4o-mini` for faster processing with good quality
- Adjust `expires_after_days` to balance cost and performance
- Monitor token usage with longer research documents

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/us-xxx-description`)
3. Implement changes following the established patterns
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

[Include your license information here]

---

**🤖 Generated and maintained by the Sprint 1 Development Team**  
_Last updated: December 2024 - US-004 Implementation_
