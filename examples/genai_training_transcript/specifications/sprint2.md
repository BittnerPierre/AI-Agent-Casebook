# GenAI Training Transcript Generator - Agile Roadmap

## MVP v1: Hierarchical Local-Only Workflow

**Goal:** Implement an early hierarchical local-only workflow with two subteams—Research Team and Editing Team—each supervised, plus a Course Authoring agent: load a local Markdown syllabus, Planner produces a course agenda, the Research Team aggregates cross-course content, the Editing Team (Documentalist/Writer/Reviewer) processes chapters under supervision, the Course Authoring agent stitches final chapters, and writes one Markdown file per chapter to disk.

### User Stories (Chapter-by-Chapter)

| ID  | Story                                                                                                                | Acceptance Criteria                                                                                                                                                            |
|-----|----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| US0 | As a content engineer, I want to preprocess raw `.txt` transcripts from `data/training_courses/` to formatted Markdown (`.md`) with punctuation, paragraphs, and chapter splitting, plus generate `manifest.json` metadata, so the agent ingests a clean, indexed knowledge base. | - The preprocessor formats all `.txt` files into `.md` with proper punctuation and sections.
|    |                                                                                                      | - A `manifest.json` is generated capturing metadata (course title, date, topics) for each transcript file.                                                                      |
| US1 | As a course author, I want to load and parse a syllabus from a local `.md` file so the Planner can refine it.        | - The agent reads `syllabus.md` and extracts chapter titles, objectives, and bullets.                                                                                           |
| US2 | As a course author, I want to load existing preprocessed transcripts from a local folder via MCP FileClient so they can serve as context. | - All files under `data/training_courses/` are listed and loaded into context.                                                                                                 |
| US3 | As the Planner, I want to refine the syllabus into a detailed chapter outline and full course agenda so the Research Team can proceed. | - A structured chapter outline and course agenda (`research_agenda/course_agenda.md`) is produced.                                                                             |
| US4 | As the Research Team, I want to retrieve and aggregate cross-course content to populate the full course agenda so the Editing Team has relevant sources. | - The course agenda file references content sources and context snippets for each chapter.                                                                                      |
| US5 | As the Editing Team (Documentalist/Writer/Reviewer) under Editing Supervisor supervision, I want to process each chapter.       | - Documentalist produces `research_notes/<chapter>.md`.<br>- Writer produces `drafts/<chapter>.md`.<br>- Reviewer comments are captured.<br>- Supervisor enforces a max-revision limit per chapter. |
| US6 | As the Course Authoring agent, I want to stitch and review all approved chapter drafts so the course flows cohesively. | - A final review pass generates smooth transitions, eliminates repetition, and ensures all syllabus objectives are covered.                                                         |
| US7 | As a course author, I want the final per-chapter transcripts written to local files so I can review and publish them. | - Each chapter transcript is saved as `output/<chapter_title>.md`.<br>- Existing files are overwritten only after confirmation.                                                      |

### Sprint Planning

#### Sprint 1 (MVP v1)
- Scaffold example directory and config under `examples/genai_training_transcript/`.
- Implement `transcript_preprocessor.py` to fulfill US0 (format raw transcripts and emit metadata).
- Implement `syllabus_loader.py` (US1) and MCP FileClient (`file_client_loader.py`) (US2) to load preprocessed transcripts.
- Implement Planner node to refine syllabus outline and produce course agenda (US3).
- Implement Research Team node to load content and generate the course agenda artifact (US4).
- Implement Editing Team nodes (Documentalist, Writer, Reviewer) and Editing Supervisor orchestration (US5).
- Persist per-chapter `research_agenda/`, `research_notes/`, and `drafts/` outputs and stub test cases.

#### Sprint 2 (MVP v2)
- Implement Course Authoring agent to stitch and review approved chapter drafts (US6).
- Implement final script writer to persist per-chapter transcripts under `output/` (US7).
- Add integration tests for end-to-end local-only flow.

## Next Iteration (v2: Evernote Integration)

| ID  | Story                                                                                                     | Acceptance Criteria                                                                               |
|-----|-----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| US5 | As a course author, I want the agent to load the syllabus from Evernote so I can keep content in my notes. | - Given an Evernote note ID, the agent fetches and parses the note as Markdown.                   |
| US6 | As a course author, I want the agent to write generated transcripts back to Evernote so everything stays in my notebook. | - Given valid Evernote credentials and notebook ID, the agent creates or updates notes with transcript content. |

### Backlog & Future Enhancements

- RAG-based retrieval using Completions file-search for context expansion
- Style customization via configuration
- Web-sources integration
- GUI or CLI flags for interactivity