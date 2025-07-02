# Research bot

This is a simple example of a multi-agent research assistant with local MCP. To run it:

```bash
poetry install
poetry run agentic-research
```

## Architecture

The flow is:

1. User enters their research topic
2. `planner_agent` comes up with a plan to search the knowlege_base for information. The plan is a list of search queries, with a search term and a reason for each query.
3. For each search item, we run a `search_agent`, which uses the knowlege_base tool to search for that term and summarize the results. These all run in parallel.
4. Finally, the `writer_agent` receives the search summaries, and creates a written report.
