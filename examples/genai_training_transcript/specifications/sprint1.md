# Sprint 1 (MVP v1): Scaffold & Basic Workflow with MCP FileClient

**Goal:** Scaffold and implement a hierarchical local-only workflow using the MCP FileClient (no RAG or Evernote integration), including transcript preprocessing, syllabus ingestion, planning, research, editing, and final transcript assembly.

**Refer to plan.md (section “Short-Term Execution Plan (Sprints)” – Sprint 1 (MVP v1)).**

## Acceptance Criteria
- TranscriptPreprocessor cleans raw `.txt` transcripts into Markdown files with punctuation, paragraph segmentation, and outputs a `manifest.json` metadata file.
- SyllabusLoader reads and parses a local `syllabus.md` file to extract chapter titles and objectives.
- MCP FileClient lists and loads preprocessed transcripts from `data/training_courses/`.
- Planner produces a detailed course agenda (`research_agenda/course_agenda.md`).
- Research Team aggregates cross-course context based on the agenda.
- Editing Team (Documentalist, Writer, Reviewer) generates `research_notes/` and `drafts/` artifacts under supervision.
- Course Authoring Agent stitches approved chapter drafts into final per-chapter transcripts and writes them under `output/`.
- Reviewer stub to enforce alignment: research notes and transcripts must mention syllabus module titles, and any misalignment should abort the workflow.

## Tasks
- [ ] Implement `TranscriptPreprocessor` tool (`transcript_preprocessor.py`) for formatting and metadata generation.
- [ ] Implement `syllabus_loader.py` to parse local syllabus Markdown.
- [ ] Integrate MCP FileClient (`file_client_loader.py`) to load and list transcripts (US2).
- [ ] Stub Planner, Research Team, Editing Team, and Course Authoring flows in `run.py` orchestration.
- [ ] Add error handling in `research_team.aggregate_research` to abort when no transcript source is available.
- [ ] Add error handling in `editing_team.edit_chapters` to abort when no research notes are provided.
- [ ] Create `reviewer.py` stub for transcript alignment checks and integrate it at end of `run.py`.
- [ ] Define directory structure for `research_agenda/`, `research_notes/`, `drafts/`, and `output/`.
- [ ] Add sample transcripts under `data/training_courses/` for end-to-end test coverage.
- [ ] Write unit tests and an end-to-end smoke test for the MVP v1 workflow.