# LangSmith Tracing Tests

This directory contains test files for verifying LangSmith tracing integration with OpenAI Agents SDK.

## Test Files

- `test_langsmith_tracing.py` - Basic LangSmith tracing test
- `test_langsmith_with_flag.py` - Test with LANGSMITH_TRACING=true flag
- `test_langsmith_global.py` - Global trace processor setup test
- `test_langsmith_verification.py` - Test with trace verification in LangSmith
- `test_langsmith_direct.py` - Direct LangSmith client connectivity test
- `test_centralized_tracing.py` - Test using centralized tracing setup
- `test_openai_native_tracing.py` - OpenAI Agents SDK native tracing test

## Running Tests

From the project root:

```bash
poetry run python tests/langsmith/test_langsmith_tracing.py
```

## Prerequisites

- LangSmith API key configured in `.env`
- `LANGSMITH_TRACING=true` in `.env`
- `LANGSMITH_PROJECT=story-ops` in `.env`