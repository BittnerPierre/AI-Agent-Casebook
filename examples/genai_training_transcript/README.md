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

## Launching the MCP Evernote server

Set the environment variable `EVERNOTE_TOKEN` to a valid Evernote developer token, then run:

```bash
bash run_mcp_evernote.sh
```

Or use the provided entrypoint which handles this automatically:

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