# User Story: Evernote MCP Chat via Streamable HTTP

## Story
As a researcher who stores project knowledge in Evernote, I want a terminal chat interface that connects to my Evernote MCP server over Streamable HTTP (running in Docker) so that I can ask natural-language questions like "Summarize all my Evernotes regarding LLMs" and get answers without opening Evernote.

## Acceptance Criteria
- **Streamable HTTP Connection**: The CLI uses the Agents SDK and connects to `https://localhost:3443/mcp` via the Streamable HTTP transport. No SSE or stdio fallback is required.
- **Evernote Tools**: Once connected, the agent can invoke `createSearch`, `getSearch`, `getNote`, and `getNoteContent` to retrieve matching note metadata and content.
- **Conversation Flow**: The CLI keeps session history during the run, allowing follow-up questions to build on earlier answers.
- **Response Quality**: For queries like "Search my Evernote for notes about project planning" and "Show me all Evernote notes tagged with 'important'", the agent returns concise summaries that mention relevant note titles, timestamps, and tags. If no notes match, it explains why and suggests search refinements.
- **Configuration Flags**: Users can override the MCP URL, supply custom HTTP headers, set notebook filters, limit the maximum notes per query, and toggle HTML preference via CLI flags or environment variables.
- **No Vector Store**: The workflow relies only on Evernote search and metadata; no embeddings or vector stores are involved.
