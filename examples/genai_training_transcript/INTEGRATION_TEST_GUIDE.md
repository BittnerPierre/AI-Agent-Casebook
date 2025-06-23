# Integration Test Guide

## Overview

This guide explains how to run integration tests with the new architectural separation between knowledge database and generated content (resolves Issue #92).

## Architecture Changes

### Directory Structure

The system now uses **separate directories** to avoid conflicts:

```
knowledge_db/                    ← Training Manager outputs (processed courses)
├── prompt_engineering_for_developers/
│   ├── metadata/index.json      ← Course metadata with keywords
│   └── cleaned_transcripts/...  ← Processed transcripts

generated_content/               ← Transcript Generator outputs
├── research_notes/              ← Research team outputs
├── chapter_drafts/             ← Editing team outputs
├── execution_report.json       ← Workflow tracking
└── final_transcript.json       ← Final generated content
```

### Configuration Changes

**config.yaml** now includes:
```yaml
# Knowledge database directory (training manager outputs)
knowledge_db_dir: knowledge_db
# Generated content directory (transcript generator outputs)  
output_dir: generated_content
```

## Running Integration Tests

### 1. Quick Setup and Validation

```bash
# Set up test environment with smoke test data
poetry run python integration_tests/setup_test_data.py

# Quick validation (recommended before full test)
poetry run python integration_tests/test_quick_validation.py
```

### 2. Full End-to-End Integration Test

```bash
# Run complete CLI integration test
poetry run python integration_tests/integration_test_cli_end_to_end.py
```

## Test Components

### setup_test_data.py
**Purpose**: Creates mock training manager data for integration testing
- Generates lightweight smoke test data in `knowledge_db/`
- Creates proper directory structure
- Ensures knowledge bridge can find test data

**Output**:
```
knowledge_db/
├── prompt_engineering_for_developers/
├── advanced_retrieval_for_ai/
├── multi_ai_agent_systems/
└── building_systems_with_the_chatgpt_api/

generated_content/
├── research_notes/
├── chapter_drafts/
├── quality_issues/
└── logs/
```

### test_quick_validation.py
**Purpose**: Rapid validation of all integration components
- Tests keyword extraction from syllabus titles
- Validates syllabus transformation 
- Checks knowledge bridge search functionality
- Verifies research notes contain actual content

**Expected Output**:
```
🎉 All validation tests passed!
✅ Integration test environment is working correctly
```

### integration_test_cli_end_to_end.py
**Purpose**: Complete end-to-end CLI workflow test
- Tests full syllabus → research → editing → generation pipeline
- Uses `generated_content/` directory for outputs
- Validates against strict success criteria

## New Application Parameters

### CLI Changes

The CLI now uses separate directories:

```bash
# OLD (conflict - both used 'output/')
poetry run python cli/transcript_generator_cli.py --output-dir output

# NEW (proper separation)
poetry run python cli/transcript_generator_cli.py --output-dir generated_content
# Knowledge automatically read from knowledge_db/
```

### Configuration Parameters

**New config.yaml structure**:
```yaml
# Raw training data
raw_transcripts_dir: data/training_courses
preprocessed_dir: data/preprocessed

# Knowledge database (training manager writes here)
knowledge_db_dir: knowledge_db

# Generated content (transcript generator writes here)  
output_dir: generated_content
research_notes_dir: research_notes
drafts_dir: drafts
quality_issues_dir: quality_issues
```

### Component-Specific Changes

**Training Manager**:
- Now writes to `knowledge_db/{course_id}/`
- Creates metadata in `knowledge_db/{course_id}/metadata/index.json`
- Stores cleaned transcripts in `knowledge_db/{course_id}/cleaned_transcripts/`

**Knowledge Bridge**:
- Reads from `knowledge_db/` (not `output/`)
- Searches across all courses in knowledge database
- Provides clean separation from generated content

**Transcript Generator**:
- Writes research notes to `generated_content/research_notes/`
- Creates chapter drafts in `generated_content/chapter_drafts/`
- Outputs final transcripts to `generated_content/`

## Key Fixes Applied

### 1. Keyword Extraction Fix
**Problem**: `test_utils.py` had hardcoded empty `key_topics: []`
**Solution**: Added `extract_keywords_from_title()` function

```python
# Before (empty keywords)
"key_topics": [],  # TODO: extract from syllabus if available

# After (extracted keywords)  
"key_topics": extract_keywords_from_title(module["title"])
```

### 2. Directory Conflict Resolution
**Problem**: Both training manager and transcript generator used `output/`
**Solution**: Separate directories with clear ownership

### 3. Integration Test Data Setup
**Problem**: No proper test data for knowledge bridge to find
**Solution**: Mock training manager outputs using smoke test data

## Expected Test Results

### Successful Quick Validation
```
🧪 Testing keyword extraction... ✅
🧪 Testing syllabus transformation... ✅  
🧪 Testing knowledge bridge search... ✅
🧪 Testing research notes content... ✅
🎉 All validation tests passed!
```

### Successful Research Phase
Research notes should contain actual content:
```json
{
  "section_id": "prompt_engineering_for_developers",
  "knowledge_references": [
    {
      "content_id": "prompt_engineering_for_developers", 
      "key_points": [
        "# Prompt Engineering for Developers",
        "- Smoke Test ## Introduction",
        "to Prompt Engineering Welcome to"
      ]
    }
  ],
  "research_summary": "# Prompt Engineering for Developers - Smoke Test ## Introduction to Prompt Engineering Welcome to"
}
```

### Integration Test Progress
- ✅ **Research Phase**: Completes successfully with populated research notes
- ⏱️ **Editing Phase**: May timeout due to OpenAI API calls (expected with real data)
- 📊 **Execution Report**: Generated with detailed timing and error information

## Troubleshooting

### Research Notes Empty
- **Cause**: Missing test data setup
- **Solution**: Run `poetry run python integration_tests/setup_test_data.py`

### Knowledge Bridge Not Finding Courses  
- **Cause**: Wrong directory configuration
- **Solution**: Ensure `knowledge_db/` directory exists with proper structure

### CLI Timeout in Editing Phase
- **Expected**: Editing phase makes real OpenAI API calls
- **Normal**: 2+ minute execution times for full workflow
- **Monitor**: Check `generated_content/execution_report.json` for progress

### Directory Permission Issues
```bash
# Ensure proper permissions
chmod -R 755 knowledge_db/ generated_content/
```

## Migration Guide

### For Existing Setups
1. **Backup existing output/**: `cp -r output/ output_backup/`
2. **Run setup script**: `poetry run python integration_tests/setup_test_data.py`
3. **Update config**: Use new `config.yaml` structure
4. **Test validation**: `poetry run python integration_tests/test_quick_validation.py`

### For Training Manager Data
If you have existing training manager data in `output/`:
```bash
# Move to new location
mv output/ knowledge_db/
```

## Related Issues

- **GitHub Issue #92**: Directory conflict resolution ✅ **RESOLVED**
- **Integration test failures**: Empty research notes ✅ **RESOLVED** 
- **Keyword extraction**: Hardcoded empty topics ✅ **RESOLVED**

---

*Updated: 2025-06-21 - Post architectural separation implementation*