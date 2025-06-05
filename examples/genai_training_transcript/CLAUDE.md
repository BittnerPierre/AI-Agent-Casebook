# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running Tests
```bash
# Run all tests (recommended)
bash test.sh

# Alternative: run directly with poetry
poetry run pytest -q --disable-warnings --maxfail=1
```

### Training Manager (Sprint 0) - Main Application
```bash
# Basic usage
poetry run run_training_manager --course-path data/training_courses/<course_id>\ -\ <course_name>

# With overwrite option
poetry run run_training_manager --course-path data/training_courses/<course_id>\ -\ <course_name> --overwrite

# With custom MCP endpoint
poetry run run_training_manager --course-path data/training_courses/<course_id>\ -\ <course_name> --mcp-endpoint evernote://
```

### Legacy Transcript Generator (Local v1)
```bash
# Run with default config
python run.py

# Run with custom config
python run.py --config custom_config.yaml
```

### MCP Filesystem Server (Manual)
```bash
# Start MCP filesystem server manually
npx @modelcontextprotocol/server-filesystem <path/to/course-directory>
```

## Architecture

This project implements a GenAI Training Transcript Generator with two main operational modes:

### Sprint 0 (Current): Training Manager
- **Entry Point**: `run_training_manager.py` → `training_manager.py`
- **Purpose**: Preprocesses raw `.txt` transcripts into cleaned Markdown files and generates metadata index
- **Key Components**:
  - `tools/transcript_preprocessor.py`: LLM-based transcript cleaning via MCP
  - `tools/metadata_extractor.py`: Extracts summaries, keywords, and tags
  - `agents/mcp.py`: MCP server integration (filesystem and Evernote)
- **Output Structure**: `output/<course_id>/cleaned_transcripts/` and `output/<course_id>/metadata/index.json`

### Local v1 (Legacy): Full Pipeline
- **Entry Point**: `run.py`
- **Purpose**: Complete transcript generation pipeline from syllabus to final output
- **Pipeline**: Syllabus → Planning → Research → Drafting → Generation → Review
- **Key Components**:
  - `tools/syllabus_loader.py`: Loads course syllabus
  - `tools/planner.py`: Refines syllabus into course agenda
  - `tools/research_team.py`: Aggregates research notes
  - `tools/editing_team.py`: Generates chapter drafts
  - `tools/transcript_generator.py`: Produces final transcripts

### MCP Integration
- Uses Model Context Protocol for file system access and external integrations
- Supports both stdio filesystem server and Evernote integration
- Environment variables: `MCP_ENDPOINT`, `EVERNOTE_TOKEN`

### Data Flow
1. **Input**: Raw `.txt` transcripts in `data/training_courses/<course_id> - <course_name>/transcripts/`
2. **Intermediate**: Research notes in `research_notes/`, drafts in `drafts/`
3. **Output**: Cleaned transcripts and metadata in `output/<course_id>/`

### Configuration
- `config.yaml`: Central configuration for paths, directories, and settings
- Course structure follows pattern: `<course_id> - <course_name>`
- Supports overwrite mode to reprocess existing outputs

## Collaboration Rules (with Codex)

### Working Scope
- **Claude Code (me)**: Limited to `examples/genai_training_transcript/` directory only
- **Codex**: Has broader project access but generates code only in `examples/` directory
- **Project context**: This is a sub-project within the larger AI-Agent-Casebook repository
- **Independence**: Do not reference or import code from `app/` or `experiments/` directories

### Spec-First Compliance
- **NEVER implement features without prior specification**: All code changes must be defined in `specifications/plan_*.md` or `sprint_*.md` files first
- **Review specifications before testing**: Check `specifications/` folder for current sprint priorities and architectural decisions
- **Request spec updates**: If testing reveals gaps or issues, request specification updates before code changes

### Division of Responsibilities
- **Codex**: Code generation, implementation, following `AGENTS.md`
- **Claude Code (me)**: Code review, testing, LLM evaluation, GitHub coordination

### Testing Protocol
- **Follow sprint order**: Test implementations in the order defined by `sprint_*.md` files
- **Specification alignment**: Ensure tests validate requirements defined in specifications
- **Report gaps**: Flag any deviations between implementation and specifications

### GitHub Workflow
- **PR reviews**: Review Codex's code before merging
- **Bug reporting**: When code review identifies issues, create GitHub issues with:
  ```bash
  gh issue create --title "Bug: [Component] Description" --body "Details, reproduction steps, expected behavior"
  ```
- **Issue tracking**: Create issues for bugs, evaluation failures, or spec misalignments
- **Branch coordination**: Coordinate with Codex on feature branches and releases
- **Repository access**: Full access to BittnerPierre/AI-Agent-Casebook via GitHub CLI
- **Agent identification**: ALWAYS identify as "Claude Code" in GitHub comments, issues, and PRs to distinguish from other agents (Codex) working on the repository. Use signatures like:
  ```
  ---
  *Created by Claude Code*
  ```

### Package Management
- **Use Poetry**: All commands must use `poetry run` prefix
- **MCP fast execution**: Use `uv` or `uvx` for MCP clients/servers where applicable

### Evaluation Standards
- **LangSmith integration**: Set up LLM evaluation pipelines for agent performance
- **Test-driven development**: Write tests before reviewing implementations
- **Integration testing**: Focus on clean interfaces between components (MCP, function calls, REST API)