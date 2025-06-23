# GenAI Training Transcript Generator

A comprehensive system for generating high-quality training course content from raw transcripts using multi-agent AI systems.

## Overview

This project transforms raw transcript files into polished, pedagogically-sound training materials through a sophisticated pipeline of AI agents:

- **Training Manager**: Preprocesses raw transcripts into clean, structured content
- **Research Team**: Performs knowledge-grounded research for content sections
- **Editing Team**: Creates draft chapters with multi-agent collaboration
- **Editorial Finalizer**: Quality assessment and content refinement
- **Workflow Orchestrator**: Coordinates the entire pipeline

## Prerequisites

- Python 3.12+
- Poetry package manager
- [Node.js](https://nodejs.org/) and [npx](https://www.npmjs.com/package/npx) (for MCP filesystem server)
- OpenAI API key
- LangSmith API key (optional, for evaluation logging)

## Installation

1. Install dependencies using Poetry:

```bash
poetry install
```

2. Set up environment variables (copy from `.env.example`):

```bash
# OpenAI Configuration
export OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration (optional)
export LANGSMITH_API_KEY=your_langsmith_api_key_here
export LANGSMITH_PROJECT=story-ops
```

## Quick Start

### 1. Prepare Training Data

The training manager preprocesses raw transcripts into cleaned content and metadata. It supports two input formats:

#### Single File Mode
Process individual transcript files:

```bash
# Process full course transcripts
poetry run run_training_manager --course-path data/training_courses/full/Course_Name.txt

# Process smoke test transcripts (smaller, faster)
poetry run run_training_manager --course-path data/training_courses/smoke_tests/Course_Smoke_Test.txt

# Process individual chapters
poetry run run_training_manager --course-path data/training_courses/chapters/Course_Chapter1_Topic.txt
```

#### Multi-Module Directory Mode
Process courses with multiple transcript files:

```bash
# Process multi-module courses (expects CourseID - Title/transcripts/*.txt structure)
poetry run run_training_manager --course-path "data/training_courses/CourseID - Course Title"
```

#### Options
- `--overwrite`: Regenerate existing cleaned transcripts and metadata
- `--mcp-endpoint`: MCP server endpoint (default: stdio://)

#### Input Data Structure

The system expects training data organized as follows:

```
data/training_courses/
├── full/                          # Complete course transcripts (single file mode)
│   ├── Course_Name.txt
│   └── Another_Course.txt
├── smoke_tests/                   # Quick test transcripts (single file mode)
│   ├── Course_Smoke_Test.txt
│   └── Another_Smoke_Test.txt
├── chapters/                      # Individual chapter files (single file mode)
│   ├── Course_Chapter1_Topic.txt
│   └── Course_Chapter2_Advanced.txt
└── CourseID - Course Title/       # Multi-module course (directory mode)
    └── transcripts/
        └── module1_en - Course - 1 - Introduction.txt
```

#### Output Structure

The training manager generates:

```
output/
└── <CourseID>/
    ├── cleaned_transcripts/       # Preprocessed Markdown files
    │   └── <module_id>.md
    └── metadata/                  # Course metadata and index
        └── index.json
```

### 2. Generate Training Content

Use the CLI to generate training materials from a syllabus:

```bash
poetry run transcript-generator \
  --syllabus syllabus.md \
  --output-dir output \
  [--dry-run]
```

### 3. Validate Setup

Test your configuration:

```bash
python scripts/validate_langsmith.py
```

## Key Features

### Multi-Agent Pipeline
- **Knowledge-grounded research** using MCP integration
- **Multi-agent editing** with Response API file_search
- **Sophisticated quality assessment** with specialized agents
- **Comprehensive evaluation logging** to LangSmith

### Quality & Evaluation
- **Multi-dimensional quality assessment**: Semantic alignment, pedagogical quality, groundedness, content depth
- **Agent conversation logging** for analysis and improvement
- **Automatic LangSmith integration** for post-execution metadata
- **Comprehensive error handling** and recovery mechanisms

### Flexible Configuration
- **Environment-based configuration** for all AI services
- **Configurable retry logic** and timeout handling
- **Rich console output** with progress tracking
- **Dry-run capability** for validation without execution

## Architecture

```
Raw Transcripts → Training Manager → Knowledge Bridge
                                          ↓
Syllabus → Research Team → Editing Team → Editorial Finalizer → Final Transcript
                ↓              ↓              ↓                    ↓
           Research Notes  Chapter Drafts  Quality Issues    Training Content
```

## Directory Structure

```
├── cli/                    # Command-line interface
├── src/
│   ├── training_manager/   # Transcript preprocessing
│   ├── knowledge_bridge/   # MCP knowledge access
│   ├── transcript_generator/
│   │   ├── tools/         # Research & editing agents
│   │   └── agents/        # Quality assessment agents
│   ├── evaluation/        # LangSmith integration
│   └── common/           # Shared utilities
├── tests/                 # Unit tests
├── integration_tests/     # Integration tests
├── scripts/              # Utility scripts
└── data/                 # Training course data
```

## MCP Filesystem Server

For knowledge access, start the MCP filesystem server:

```bash
npx @modelcontextprotocol/server-filesystem data/training_courses/
```

The system automatically connects to this server for knowledge queries.

## Testing

Run the test suite:

```bash
# Unit tests
poetry run pytest tests/ -v

# Integration tests
poetry run pytest integration_tests/ -v

# LangSmith integration tests
poetry run pytest tests/test_langsmith_integration.py -v
```

## Configuration Files

- `config.yaml`: Main system configuration
- `models_config.yaml`: AI model configuration
- `.env`: Environment variables (create from `.env.example`)
- `pyproject.toml`: Python project configuration

## Output

The system generates:

- **Final transcripts**: Polished training content in Markdown
- **Quality reports**: Detailed quality assessment and issues
- **Research notes**: Knowledge-grounded research findings
- **Execution metadata**: Performance and evaluation data

## Advanced Features

### LangSmith Integration
- Automatic logging of agent conversations
- Post-execution metadata transmission
- Quality metrics collection
- Performance analysis and optimization

### Multi-Agent Quality Assessment
- Semantic alignment verification
- Pedagogical quality evaluation
- Content groundedness analysis
- Guidelines compliance checking

## Troubleshooting

1. **Import errors**: Ensure you're running from the project root with Poetry
2. **API key issues**: Check environment variables and API key validity
3. **MCP connection**: Verify filesystem server is running on correct path
4. **Quality issues**: Review `quality_issues/` directory for detailed reports

## Future Enhancements

- **MCP Evernote integration**: See `MCP_EVERNOTE_SETUP.md` for planned features
- **Multi-model support**: LiteLLM integration for cost optimization
- **Enhanced evaluation**: RAG evaluation and answer relevance metrics

## Related Documentation

- `WORKFLOW_VALIDATION_GUIDE.md`: Comprehensive validation procedures
- `AI_DEVELOPER_GUIDELINES.md`: Development standards and practices
- `MCP_EVERNOTE_SETUP.md`: Future Evernote integration setup
- `specifications/`: Detailed technical specifications

## Integration Testing

### Directory Architecture (Post Issue #92 Fix)

The system now uses **separate directories** to avoid conflicts:

```
knowledge_db/                    ← Training Manager outputs (processed courses)
├── {course_id}/
│   ├── metadata/index.json      ← Course metadata with keywords
│   └── cleaned_transcripts/...  ← Processed transcripts

generated_content/               ← Transcript Generator outputs  
├── research_notes/              ← Research team outputs
├── chapter_drafts/             ← Editing team outputs
├── execution_report.json       ← Workflow tracking
└── final_transcript.json       ← Final generated content
```

### Running Integration Tests

See [INTEGRATION_TEST_GUIDE.md](INTEGRATION_TEST_GUIDE.md) for complete testing instructions.

**Quick Start**:
```bash
# Set up test environment with smoke test data
poetry run python integration_tests/setup_test_data.py

# Quick validation (recommended before full test)
poetry run python integration_tests/test_quick_validation.py

# Full end-to-end CLI integration test
poetry run python integration_tests/integration_test_cli_end_to_end.py
```

**Expected Results**:
- ✅ **Research Phase**: Completes successfully with populated research notes
- ⏱️ **Editing Phase**: May timeout due to OpenAI API calls (expected)
- 📊 **Execution Report**: Generated in `generated_content/execution_report.json`

## License

This project is part of the AI Agent Casebook and follows the same licensing terms.