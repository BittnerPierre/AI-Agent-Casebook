# Sprint 0 - US0: Training Course Manager Data Preparation

## User Story US0

**As** a content engineer  
**I want** to preprocess raw `.txt` training transcripts into cleaned, paragraph‑segmented module files and generate a metadata index  
**So that** the research team can quickly lookup modules by keyword and perform late chunking on coherent content segments.

### Acceptance Criteria

- Load all `.txt` files under `data/training_courses/<course_id> - <course_name>/transcripts/` via the MCP filesystem (stdio transport via `npx @modelcontextprotocol/server-filesystem`). Raw transcript filenames must follow `<course_id>_<module_index>_<language> - <course_name> - <module_index> - <module_name>.txt`.
- Produce cleaned Markdown files per module with punctuation, sentence boundaries, and paragraph segmentation.
- Generate a JSON index file per course (`output/<course_id>/metadata/index.json`) matching the defined schema.
- Write outputs to `output/<course_id>/cleaned_transcripts/` and `output/<course_id>/metadata/` via the MCP filesystem (stdio transport via `npx @modelcontextprotocol/server-filesystem`).

## Tasks

- [ ] Finalize US0 specification and file hierarchy in `../plan_training_manager.md`.
- [ ] Rename entrypoint and manager modules:
  - `run_agents.py` → `run_training_manager.py`
  - `manager.py` → `training_manager.py`
- [ ] Scaffold TrainingManager flow in `run_training_manager.py` and `training_manager.py` to invoke transcript cleaning and metadata generation.
- [ ] Implement `TranscriptPreprocessor` tool for punctuation, sentence splitting, and paragraph segmentation.
- [ ] Implement summarization, keyword extraction, and tag detection component for module metadata.
- [ ] Integrate MCP FileClient in `training_manager.py` for all file I/O.
- [ ] Generate cleaned transcript `.md` files and course `index.json` metadata as defined.
- [ ] Write unit tests for preprocessing and metadata-generation logic.

- [ ] Provide mock raw `.txt` transcripts (e.g. based on the Chroma course) under `data/training_courses/` for end-to-end and unit test fixtures.
- [ ] Implement CLI flags `--course-path`, `--mcp-endpoint`, and `--overwrite` in `run_training_manager.py` and document their behavior.
- [ ] Add a `README.md` in `examples/genai_training_transcript/` explaining how to launch the MCP filesystem server (`npx @modelcontextprotocol/server-filesystem`) and run the Training Course Manager, including CLI usage and overwrite behavior.
