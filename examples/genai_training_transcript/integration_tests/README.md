# Integration Tests

This directory contains integration tests that verify end-to-end functionality of the GenAI Training Transcript Generator system.

## Test Categories

### Component Integration Tests
- `integration_test_editing_team.py` - Tests EditingTeam with Response API file_search
- `integration_test_editorial_finalizer.py` - Tests EditorialFinalizer quality assessment
- `integration_test_response_api_file_search.py` - Tests Response API integration patterns
- `integration_test_real_datasets.py` - Tests with real training course data

### Workflow Integration Tests
- `integration_test_workflow_orchestrator.py` - Tests complete WorkflowOrchestrator pipeline

## Running Integration Tests

Integration tests require:
- Valid API keys (OpenAI, LangSmith optional)
- MCP filesystem server running (for knowledge access tests)
- Real or test training course data

### Prerequisites

1. Set up environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key
export LANGSMITH_API_KEY=your_langsmith_api_key  # optional
```

2. Start MCP filesystem server (if testing knowledge access):
```bash
npx @modelcontextprotocol/server-filesystem data/training_courses/
```

### Running Tests

Integration tests are designed as standalone Python scripts, not pytest tests:

```bash
# Run all integration tests
for test in integration_tests/integration_test_*.py; do
    echo "=== Running $test ==="
    poetry run python "$test"
    echo
done

# Run specific integration test
poetry run python integration_tests/integration_test_workflow_orchestrator.py

# Run CLI end-to-end test
poetry run python integration_tests/integration_test_cli_end_to_end.py
```

## Test Data

Integration tests use:
- Sample syllabus files
- Test training course data from `data/training_courses/`
- Mock research notes and chapter drafts
- Real API responses (where API keys are available)

## Test Structure

Each integration test typically:
1. Sets up test data and configuration
2. Initializes the component/workflow under test
3. Executes the integration scenario
4. Validates output quality and structure
5. Cleans up resources

## Notes

- Integration tests may take longer than unit tests due to API calls
- Some tests may be skipped if required API keys are not available
- Tests are designed to be independent and can run in any order
- Real API usage may incur costs - review test scope before running

## Adding New Integration Tests

When adding new integration tests:
1. Use the `integration_test_` prefix
2. Include comprehensive setup and teardown
3. Add appropriate API key checks and skipping
4. Document test purpose and requirements
5. Follow existing patterns for consistency