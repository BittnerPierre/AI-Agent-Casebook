# Migration Plan: Assistant API to Agents SDK FileSearchTool

**Migration ID**: MIG-001  
**Target Component**: EditingTeam (US-004)  
**Source**: Assistant API file_search  
**Target**: Agents SDK FileSearchTool  
**Estimated Effort**: 7-10 days  
**Priority**: CRITICAL  

## Overview

This document provides a comprehensive migration plan to replace the Assistant API implementation in `EditingTeam` with the OpenAI Agents SDK FileSearchTool, ensuring compliance with the defined architecture standards while maintaining all existing functionality.

## Pre-Migration Assessment

### Current State Analysis

**File**: `src/transcript_generator/tools/editing_team.py`
- **Total Lines**: ~600 lines
- **Assistant API Usage**: Lines 179, 321-339, 341-380
- **Key Methods Using Assistant API**:
  - `_create_research_assistant()` (lines 318-339)
  - `_execute_synthesis_workflow()` (lines 341-380)
  - `_synthesize_content_step()` (lines 382-420)

### Dependencies Assessment

**Current Dependencies**:
```python
from openai import OpenAI
# Uses: client.beta.assistants.*, client.beta.threads.*
```

**Required Dependencies**:
```python
from agents import Agent, FileSearchTool, Runner
# New: Agents SDK integration
```

**Compatibility Check**: ✅ Both use same OpenAI vector stores

## Migration Strategy

### Phase-by-Phase Approach

#### Phase 1: Preparation (Day 1)
- [ ] Create migration branch: `feature/migrate-to-agents-sdk`
- [ ] Install Agents SDK dependencies
- [ ] Backup current implementation
- [ ] Create comprehensive test baseline

#### Phase 2: Core Migration (Days 2-4)
- [ ] Replace Assistant API with Agents SDK
- [ ] Refactor synthesis workflow
- [ ] Update resource management
- [ ] Implement error handling

#### Phase 3: Testing & Validation (Days 5-7)
- [ ] Unit test migration (23 tests)
- [ ] Integration test validation
- [ ] Performance comparison
- [ ] Quality assurance

#### Phase 4: Deployment (Days 8-10)
- [ ] Code review and architecture compliance
- [ ] Documentation updates
- [ ] Merge to main branch
- [ ] Post-deployment validation

## Detailed Implementation Plan

### 1. Core Architecture Changes

#### 1.1 Replace Assistant Creation
**Current Implementation** (lines 321-339):
```python
def _create_research_assistant(self, vector_store_id: str) -> str:
    try:
        assistant = self.client.beta.assistants.create(
            name="EditingTeam Content Synthesizer",
            description="Multi-agent editing team for training course content synthesis",
            model=self.model,
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            },
            instructions=self._get_assistant_instructions()
        )
        self.assistant_id = assistant.id
        return assistant.id
    except Exception as e:
        logger.error(f"Assistant creation failed: {e!s}")
        raise
```

**New Implementation**:
```python
def _create_research_agent(self, vector_store_id: str) -> Agent:
    """Create Agents SDK agent with FileSearchTool"""
    try:
        agent = Agent(
            name="EditingTeam Content Synthesizer",
            instructions=self._get_assistant_instructions(),
            tools=[
                FileSearchTool(
                    max_num_results=10,
                    vector_store_ids=[vector_store_id]
                )
            ]
        )
        logger.info(f"Created research agent with vector store: {vector_store_id}")
        return agent
    except Exception as e:
        logger.error(f"Agent creation failed: {e!s}")
        raise
```

#### 1.2 Replace Synthesis Workflow
**Current Implementation** (lines 341-380):
```python
def _execute_synthesis_workflow(self, research_notes: dict[str, Any], assistant_id: str) -> str:
    try:
        target_section = research_notes.get('target_section', 'Unknown Section')
        
        # Create thread for conversation
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        
        # Multi-step synthesis using thread
        documentalist_query = self._create_documentalist_query(target_section, research_notes)
        documented_content = self._synthesize_content_step(thread.id, assistant_id, documentalist_query, "documentalist")
        
        # ... additional steps
        
        return final_content
    except Exception as e:
        # error handling
```

**New Implementation**:
```python
def _execute_synthesis_workflow(self, research_notes: dict[str, Any], agent: Agent) -> str:
    """Execute synthesis workflow using Agents SDK"""
    try:
        target_section = research_notes.get('target_section', 'Unknown Section')
        runner = Runner(agent=agent)
        
        # Step 1: Documentalist
        documentalist_query = self._create_documentalist_query(target_section, research_notes)
        documented_content = self._synthesize_with_agent(runner, documentalist_query, "documentalist")
        
        # Step 2: Writer
        writer_query = self._create_writer_query(target_section, documented_content, research_notes)
        draft_content = self._synthesize_with_agent(runner, writer_query, "writer")
        
        # Step 3: Reviewer
        reviewer_query = self._create_reviewer_query(target_section, draft_content)
        review_feedback = self._synthesize_with_agent(runner, reviewer_query, "reviewer")
        
        # Step 4: Final Revision
        final_query = self._create_final_revision_query(target_section, draft_content, review_feedback)
        final_content = self._synthesize_with_agent(runner, final_query, "script_strategist")
        
        logger.info(f"Multi-step synthesis completed for section: {target_section}")
        return final_content
        
    except Exception as e:
        logger.error(f"Synthesis workflow failed: {e!s}")
        raise
```

#### 1.3 New Synthesis Helper Method
```python
def _synthesize_with_agent(self, runner: Runner, query: str, role: str) -> str:
    """Synthesize content using Agents SDK runner"""
    try:
        logger.info(f"Starting {role} synthesis step")
        
        # Execute with Agents SDK
        response = runner.run(query)
        
        if not response or not response.data:
            raise ValueError(f"Empty response from {role} step")
        
        # Extract content from response
        content = self._extract_content_from_response(response)
        
        logger.info(f"Completed {role} synthesis: {len(content)} characters")
        return content
        
    except Exception as e:
        logger.error(f"Synthesis step failed for {role}: {e!s}")
        raise
```

### 2. Resource Management Updates

#### 2.1 Update Class Initialization
**Current**:
```python
def __init__(self, ...):
    # ... existing init
    self.assistant_id = None
    self.thread_id = None
    # ... rest
```

**New**:
```python
def __init__(self, ...):
    # ... existing init
    self.agent = None
    self.runner = None
    # Remove: self.assistant_id, self.thread_id
    # ... rest
```

#### 2.2 Update Cleanup Method
**Current**:
```python
def cleanup(self):
    """Cleanup OpenAI resources"""
    if self.assistant_id:
        try:
            self.client.beta.assistants.delete(self.assistant_id)
            logger.info(f"Deleted assistant: {self.assistant_id}")
        except Exception as e:
            logger.warning(f"Failed to delete assistant: {e}")
    # ... rest
```

**New**:
```python
def cleanup(self):
    """Cleanup OpenAI resources"""
    # No assistant/thread cleanup needed with Agents SDK
    # Keep vector store and file cleanup
    if self.vector_store_id:
        try:
            self.client.vector_stores.delete(self.vector_store_id)
            logger.info(f"Deleted vector store: {self.vector_store_id}")
        except Exception as e:
            logger.warning(f"Failed to delete vector store: {e}")
    # ... rest
```

### 3. Test Migration

#### 3.1 Unit Test Updates
**File**: `tests/test_editing_team.py`
- **Tests to Update**: 23 tests total
- **Key Changes**: Mock Agents SDK instead of Assistant API
- **Mock Targets**: `Agent`, `Runner`, `FileSearchTool`

**Example Test Update**:
```python
# Old
@patch('editing_team.OpenAI')
def test_synthesize_chapter_success(self, mock_openai):
    mock_client = Mock()
    mock_openai.return_value = mock_client
    
    # Mock assistant creation
    mock_assistant = Mock()
    mock_assistant.id = "asst_123"
    mock_client.beta.assistants.create.return_value = mock_assistant
    
    # ... rest of test

# New
@patch('agents.Agent')
@patch('agents.Runner')
def test_synthesize_chapter_success(self, mock_runner_class, mock_agent_class):
    mock_agent = Mock()
    mock_agent_class.return_value = mock_agent
    
    mock_runner = Mock()
    mock_runner_class.return_value = mock_runner
    
    # Mock synthesis response
    mock_response = Mock()
    mock_response.data = "Synthesized content"
    mock_runner.run.return_value = mock_response
    
    # ... rest of test
```

#### 3.2 Integration Test Updates
**File**: `integration_tests/integration_test_editing_team.py`
- **No major changes needed**: Test interface remains the same
- **Validation**: Ensure no Assistant API artifacts in logs
- **Performance**: Compare processing times

### 4. Dependencies and Configuration

#### 4.1 Update Dependencies
**pyproject.toml** additions:
```toml
[tool.poetry.dependencies]
openai-agents-python = "^1.0.0"  # Add Agents SDK
```

#### 4.2 Import Updates
**File**: `src/transcript_generator/tools/editing_team.py`
```python
# Remove
# from openai import OpenAI (keep for vector stores)

# Add
from agents import Agent, FileSearchTool, Runner
from agents.types import Response
```

### 5. Error Handling and Logging

#### 5.1 Update Error Handling
```python
def _handle_synthesis_error(self, error: Exception, step: str) -> str:
    """Handle synthesis errors with Agents SDK context"""
    error_msg = f"Synthesis failed at {step}: {str(error)}"
    logger.error(error_msg)
    
    # Agents SDK specific error handling
    if isinstance(error, AgentsSDKError):
        # Handle SDK-specific errors
        logger.error(f"Agents SDK error: {error.code} - {error.message}")
    
    # Return error content for graceful degradation
    return f"Error in {step}: Unable to synthesize content due to {type(error).__name__}"
```

#### 5.2 Enhanced Logging
```python
def _log_synthesis_metrics(self, step: str, start_time: float, content_length: int):
    """Log synthesis performance metrics"""
    duration = time.time() - start_time
    logger.info(f"Synthesis metrics - Step: {step}, Duration: {duration:.2f}s, Content: {content_length} chars")
```

## Testing Strategy

### 1. Unit Test Migration Checklist
- [ ] Test 1-5: Basic functionality tests
- [ ] Test 6-10: Error handling tests
- [ ] Test 11-15: Resource management tests
- [ ] Test 16-20: Integration boundary tests
- [ ] Test 21-23: Performance and edge case tests

### 2. Integration Test Validation
- [ ] Full synthesis workflow execution
- [ ] File upload and vector store creation
- [ ] Multi-step synthesis process
- [ ] Chapter draft output validation
- [ ] Resource cleanup verification

### 3. Performance Testing
- [ ] Synthesis time comparison (target: <300 seconds)
- [ ] Memory usage analysis
- [ ] API call efficiency
- [ ] Content quality assessment

### 4. Regression Testing
- [ ] All existing functionality preserved
- [ ] Output format unchanged
- [ ] Error handling maintained
- [ ] Integration points working

## Risk Assessment and Mitigation

### High Risk Items
1. **API Behavior Differences**
   - **Risk**: Agents SDK may behave differently than Assistant API
   - **Mitigation**: Comprehensive testing and gradual rollout
   - **Contingency**: Keep Assistant API as fallback during migration

2. **Performance Degradation**
   - **Risk**: Synthesis time may increase
   - **Mitigation**: Performance benchmarking and optimization
   - **Contingency**: Optimization or rollback if performance unacceptable

3. **Content Quality Changes**
   - **Risk**: Different API may produce different content quality
   - **Mitigation**: Side-by-side comparison and quality validation
   - **Contingency**: Fine-tune prompts and parameters

### Medium Risk Items
1. **Test Coverage Gaps**
   - **Risk**: Some edge cases not covered in migration
   - **Mitigation**: Comprehensive test review and enhancement
   - **Contingency**: Incremental testing and bug fixing

2. **Dependencies Issues**
   - **Risk**: Agents SDK compatibility problems
   - **Mitigation**: Thorough dependency testing
   - **Contingency**: Version pinning and compatibility matrix

## Rollback Plan

### Rollback Triggers
- Critical functionality failure
- Performance degradation >50%
- Test failure rate >20%
- Integration test complete failure

### Rollback Procedure
1. **Immediate**: Revert to previous commit
2. **Validation**: Run full test suite on reverted code
3. **Communication**: Notify team of rollback and reasons
4. **Analysis**: Root cause analysis of migration failure
5. **Planning**: Revised migration approach

## Success Criteria

### Functional Requirements
- [ ] All 23 unit tests pass
- [ ] Integration test completes successfully
- [ ] Chapter synthesis produces expected output
- [ ] All error handling scenarios work
- [ ] Resource cleanup functions properly

### Performance Requirements
- [ ] Synthesis time ≤ 300 seconds (current benchmark)
- [ ] Memory usage within 10% of current
- [ ] API call efficiency maintained or improved
- [ ] Content quality equivalent or better

### Quality Requirements
- [ ] No Assistant API dependencies remain
- [ ] Code follows project standards
- [ ] Documentation updated
- [ ] Architecture compliance verified

## Post-Migration Tasks

### 1. Monitoring and Validation
- [ ] Monitor synthesis performance for 1 week
- [ ] Validate content quality with sample outputs
- [ ] Check resource usage patterns
- [ ] Verify error handling in production

### 2. Documentation Updates
- [ ] Update architecture documentation
- [ ] Update API usage guidelines
- [ ] Update troubleshooting documentation
- [ ] Update team training materials

### 3. Process Improvements
- [ ] Add Agents SDK compliance to review checklist
- [ ] Update CI/CD to detect Assistant API usage
- [ ] Create architecture decision record (ADR)
- [ ] Schedule architecture review process

## Timeline and Milestones

### Week 1: Preparation and Core Migration
- **Day 1**: Setup and preparation
- **Day 2-3**: Core architecture changes
- **Day 4**: Initial testing and debugging

### Week 2: Testing and Validation
- **Day 5-6**: Comprehensive testing
- **Day 7**: Performance validation and optimization
- **Day 8**: Code review and compliance check

### Week 2: Deployment and Validation
- **Day 9**: Merge and deployment
- **Day 10**: Post-deployment validation
- **Day 11-17**: Monitoring and final validation

## Resources Required

### Development Resources
- **Primary Developer**: 1 FTE for 10 days
- **Code Reviewer**: 0.2 FTE for architecture compliance
- **QA Tester**: 0.3 FTE for validation testing

### Infrastructure Resources
- **Test Environment**: Agents SDK compatible environment
- **API Access**: OpenAI Agents SDK API access
- **Monitoring**: Performance monitoring tools

### Documentation Resources
- **Technical Writer**: 0.1 FTE for documentation updates
- **Architecture Review**: 0.1 FTE for compliance validation

## Conclusion

This migration plan provides a comprehensive roadmap for transitioning from Assistant API to Agents SDK while maintaining all existing functionality and ensuring architecture compliance. The phased approach minimizes risk while providing clear success criteria and rollback procedures.

The migration addresses the critical architecture violation identified in the bug report while establishing processes to prevent similar issues in the future.

---

**Plan Version**: 1.0  
**Next Review**: After Phase 1 completion  
**Approval Required**: Architecture Review Board  

**Generated with [Claude Code](https://claude.ai/code)**

Co-Authored-By: Claude <noreply@anthropic.com>