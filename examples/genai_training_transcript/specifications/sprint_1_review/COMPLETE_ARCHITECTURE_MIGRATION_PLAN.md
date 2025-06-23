# COMPLETE ARCHITECTURE MIGRATION PLAN: Agents SDK Compliance

**Migration ID**: EMERGENCY-MIG-001  
**Scope**: ALL core workflow components  
**Framework**: OpenAI Agents SDK  
**Priority**: EMERGENCY - CRITICAL PATH  
**Estimated Effort**: 3-4 weeks (FULL SPRINT EQUIVALENT)  

## Overview

This document provides a comprehensive plan to migrate ALL components to OpenAI Agents SDK compliance, addressing the catastrophic architecture violations discovered across the entire codebase.

**SCOPE OF MIGRATION**:
- 🔴 **ResearchTeam**: Complete rewrite from data processing to multi-agent workflow
- 🔴 **EditingTeam**: Migration from Assistant API to Agents SDK
- 🟡 **Editorial Finalizer**: Audit and compliance verification
- ✅ **Supporting Components**: Already compliant (Module List, Transcript Generator)

## Pre-Migration Assessment

### Current Architecture State

| Component | Lines of Code | Architecture | Compliance | Migration Type |
|-----------|---------------|--------------|------------|----------------|
| **ResearchTeam** | ~150 | Data processing | ❌ 0% | COMPLETE REWRITE |
| **EditingTeam** | ~400 | Assistant API | ❌ 0% | API MIGRATION |
| **Editorial Finalizer** | ~300 | Unknown/Mixed | ⚠️ TBD | AUDIT + FIX |
| **Module List Agent** | ~20 | Agents SDK | ✅ 100% | NO CHANGE |
| **Transcript Generator** | ~50 | Agents SDK | ✅ 100% | NO CHANGE |

**TOTAL MIGRATION SCOPE**: ~850 lines of non-compliant code

### Dependencies Impact Assessment

**Current Dependencies** (will be preserved):
```toml
openai = "^1.74.0"                    # Keep for vector stores
openai-agents = "^0.0.17"             # PRIMARY framework
langsmith = {version = ">=0.3.15", extras = ["openai-agents"]}  # Keep for tracing
```

**NO dependency changes required** - Agents SDK already installed

## Migration Strategy

### Phase-Based Approach (3-4 Weeks)

#### Phase 1: Emergency Preparedness (Week 1)
- [ ] Create emergency migration branch
- [ ] Establish architecture compliance baseline
- [ ] Set up comprehensive testing framework
- [ ] Team training on Agents SDK patterns

#### Phase 2: Core Component Migration (Week 2-3)
- [ ] ResearchTeam complete rewrite
- [ ] EditingTeam API migration
- [ ] Editorial Finalizer audit and compliance

#### Phase 3: Integration & Validation (Week 4)
- [ ] End-to-end integration testing
- [ ] Performance validation
- [ ] Quality assurance
- [ ] Production deployment

## Detailed Migration Plans

### 1. ResearchTeam Complete Rewrite

#### Current Implementation (WRONG)
```python
# src/transcript_generator/tools/research_team.py
def research_topic(self, syllabus_section: dict[str, Any]) -> dict[str, Any]:
    # Plain data processing - NO LLM, NO agents
    raw_items = asyncio.run(self.retriever.get_related_content(key_topics))
    
    # Basic string manipulation
    for item in raw_items:
        words = preview.split()
        # Simple text chunking...
    
    # String concatenation
    research_summary = " ".join(summary_parts)
    return notes
```

#### Required Implementation (CORRECT)
```python
# NEW: Multi-agent research workflow
from agents import Agent, Runner, FileSearchTool

class ResearchTeam:
    def __init__(self, vector_store_id: str = None):
        # Agent 1: Researcher - Information gathering
        self.researcher_agent = Agent(
            name="ResearcherAgent",
            instructions="""You are a research specialist. Your role is to:
            1. Analyze the given syllabus section and key topics
            2. Search through available knowledge sources
            3. Identify relevant content for the topic
            4. Compile comprehensive source materials
            Return structured research findings with source references.""",
            tools=[FileSearchTool(vector_store_ids=[vector_store_id])] if vector_store_id else []
        )
        
        # Agent 2: Analyst - Content analysis and extraction
        self.analyst_agent = Agent(
            name="AnalystAgent", 
            instructions="""You are a content analyst. Your role is to:
            1. Review research findings from the Researcher
            2. Extract key concepts, themes, and insights
            3. Identify gaps or areas needing additional research
            4. Organize information into logical structures
            Return structured analysis with key points and themes."""
        )
        
        # Agent 3: Synthesizer - Knowledge synthesis
        self.synthesizer_agent = Agent(
            name="SynthesizerAgent",
            instructions="""You are a knowledge synthesizer. Your role is to:
            1. Combine research findings and analysis
            2. Create cohesive research summaries
            3. Ensure comprehensive coverage of topic requirements
            4. Produce final research notes for content creation
            Return final research notes in structured format."""
        )
        
        self.runner = Runner()
    
    def research_topic(self, syllabus_section: dict[str, Any]) -> dict[str, Any]:
        """Execute multi-agent research workflow"""
        section_id = syllabus_section.get("section_id")
        key_topics = syllabus_section.get("key_topics", [])
        
        # Step 1: Researcher - Gather information
        research_query = f"""
        Research the following section: {section_id}
        Key topics to investigate: {', '.join(key_topics)}
        
        Please search for relevant information and compile comprehensive source materials.
        """
        
        research_findings = self.runner.run(
            agent=self.researcher_agent,
            messages=[{"role": "user", "content": research_query}]
        )
        
        # Step 2: Analyst - Analyze content
        analysis_query = f"""
        Analyze the following research findings and extract key insights:
        
        {research_findings.data}
        
        Focus on: {', '.join(key_topics)}
        
        Extract key concepts, themes, and organize information logically.
        """
        
        analysis_results = self.runner.run(
            agent=self.analyst_agent,
            messages=[{"role": "user", "content": analysis_query}]
        )
        
        # Step 3: Synthesizer - Create final research notes
        synthesis_query = f"""
        Create comprehensive research notes by synthesizing:
        
        Research Findings:
        {research_findings.data}
        
        Analysis Results:
        {analysis_results.data}
        
        Section: {section_id}
        Topics: {', '.join(key_topics)}
        
        Produce final research notes suitable for content creation.
        """
        
        final_notes = self.runner.run(
            agent=self.synthesizer_agent,
            messages=[{"role": "user", "content": synthesis_query}]
        )
        
        # Structure return data to match expected schema
        return {
            "section_id": section_id,
            "knowledge_references": self._extract_references(research_findings.data),
            "research_summary": final_notes.data,
            "analysis_insights": analysis_results.data,
            "synthesis_metadata": {
                "research_agent_id": research_findings.metadata.get("agent_id"),
                "analysis_agent_id": analysis_results.metadata.get("agent_id"),
                "synthesis_agent_id": final_notes.metadata.get("agent_id")
            }
        }
```

#### Migration Tasks for ResearchTeam
- [ ] **Complete rewrite**: Replace data processing with agent workflow
- [ ] **Agent design**: Create Researcher, Analyst, Synthesizer agents
- [ ] **Workflow orchestration**: Implement multi-agent coordination
- [ ] **Schema compliance**: Ensure output matches expected format
- [ ] **Testing**: Comprehensive test suite for agent behaviors
- [ ] **Performance**: Validate processing time and quality

### 2. EditingTeam API Migration 

#### Current Implementation (WRONG)
```python
# Assistant API usage (PROHIBITED)
assistant = self.client.beta.assistants.create(
    name="EditingTeam Content Synthesizer",
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
)

thread = self.client.beta.threads.create()
```

#### Required Implementation (CORRECT)
```python
# Agents SDK usage (REQUIRED)
from agents import Agent, Runner, FileSearchTool

class EditingTeam:
    def __init__(self, vector_store_id: str):
        # Multi-role editing agent with file search capability
        self.editing_agent = Agent(
            name="EditingTeam",
            instructions="""You are a sophisticated editing team combining multiple roles:
            
            DOCUMENTALIST ROLE:
            - Extract and organize content from research notes
            - Structure information for content creation
            - Ensure comprehensive coverage of topics
            
            WRITER ROLE:
            - Create engaging, educational content
            - Follow pedagogical best practices
            - Maintain consistent tone and style
            
            REVIEWER ROLE:
            - Review content for quality and accuracy
            - Provide constructive feedback
            - Ensure learning objectives are met
            
            SCRIPT STRATEGIST ROLE:
            - Optimize content for target audience
            - Ensure narrative flow and engagement
            - Final quality assessment
            
            Use the file search tool to access research materials and create high-quality chapter content.""",
            tools=[FileSearchTool(
                max_num_results=10,
                vector_store_ids=[vector_store_id]
            )]
        )
        
        self.runner = Runner(agent=self.editing_agent)
    
    def synthesize_chapter(self, research_data: dict[str, Any]) -> ChapterDraft:
        """Execute multi-step content synthesis using Agents SDK"""
        target_section = research_data.get('target_section', 'Unknown Section')
        
        # Single agent with multi-role capability
        synthesis_query = f"""
        Create a comprehensive chapter for: {target_section}
        
        Using the available research materials, please:
        
        1. DOCUMENTALIST PHASE:
           - Review all research notes and materials
           - Extract key concepts and information
           - Organize content structure
        
        2. WRITER PHASE:
           - Create engaging chapter content
           - Include learning objectives
           - Develop clear explanations and examples
           - Ensure pedagogical effectiveness
        
        3. REVIEWER PHASE:
           - Review the written content
           - Check for accuracy and completeness
           - Verify learning objectives are addressed
           - Identify areas for improvement
        
        4. SCRIPT STRATEGIST PHASE:
           - Optimize for target audience engagement
           - Ensure narrative flow and clarity
           - Final quality polish
        
        Research Data Available:
        - Syllabus: {research_data.get('syllabus', {})}
        - Agenda: {research_data.get('agenda', [])}
        - Research Notes: {research_data.get('research_notes', {})}
        
        Please use the file search tool to access detailed research materials.
        
        Return the final chapter content in Markdown format.
        """
        
        try:
            response = self.runner.run(synthesis_query)
            
            return ChapterDraft(
                section_id=target_section,
                content=response.data
            )
            
        except Exception as e:
            logger.error(f"Chapter synthesis failed: {e}")
            return ChapterDraft(
                section_id=target_section,
                content=f"Error: Chapter synthesis failed - {str(e)}"
            )
```

#### Migration Tasks for EditingTeam
- [ ] **Remove Assistant API**: Delete all `client.beta.assistants.*` calls
- [ ] **Remove Thread API**: Delete all `client.beta.threads.*` calls  
- [ ] **Implement Agents SDK**: Create Agent with FileSearchTool
- [ ] **Workflow migration**: Convert thread-based to agent-based workflow
- [ ] **Resource management**: Update cleanup to remove assistant/thread handling
- [ ] **Testing**: Update all 23 unit tests for Agents SDK

### 3. Editorial Finalizer Audit & Compliance

#### Audit Requirements
```python
# Check current implementation in editorial_finalizer_multi_agent.py
# Verify:
# 1. Uses agents.Agent (not direct OpenAI calls)
# 2. Uses agents.Runner for execution
# 3. No Assistant API or Thread API usage
# 4. Proper multi-agent orchestration
```

#### Potential Migration (TBD after audit)
If violations found, implement:
```python
from agents import Agent, Runner

class MultiAgentEditorialFinalizer:
    def __init__(self):
        # Quality assessment agents
        self.semantic_agent = Agent(
            name="SemanticAlignmentAgent",
            instructions="Assess content-syllabus semantic alignment..."
        )
        
        self.pedagogical_agent = Agent(
            name="PedagogicalQualityAgent", 
            instructions="Evaluate educational effectiveness..."
        )
        
        self.groundedness_agent = Agent(
            name="GroundednessAgent",
            instructions="Evaluate evidence quality and factual grounding..."
        )
        
        self.consensus_orchestrator = Agent(
            name="QualityConsensusOrchestrator",
            instructions="Coordinate quality assessments and reach consensus..."
        )
        
        self.runner = Runner()
```

## Integration Architecture

### Agent-to-Agent Communication Flow

```
ResearchTeam Agents → Research Notes JSON
                 ↓
EditingTeam Agent → Chapter Drafts
                 ↓  
Editorial Finalizer Agents → Final Transcript + Quality Reports
```

### Data Flow Schema
```python
# ResearchTeam Output → EditingTeam Input
research_notes = {
    "section_id": str,
    "knowledge_references": List[dict],
    "research_summary": str,
    "analysis_insights": str,
    "synthesis_metadata": dict
}

# EditingTeam Output → Editorial Finalizer Input  
chapter_draft = {
    "section_id": str,
    "content": str,  # Markdown format
    "metadata": dict
}

# Editorial Finalizer Output → Final Product
final_output = {
    "final_transcript": str,
    "quality_issues": List[dict],
    "assessment_summary": dict
}
```

## Testing Strategy

### Unit Testing Migration

#### ResearchTeam Tests
```python
# NEW: Test agent behaviors instead of data processing
@patch('agents.Runner')
@patch('agents.Agent')
def test_research_topic_multi_agent_workflow(self, mock_agent, mock_runner):
    # Mock agent responses
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    
    # Mock research agent response
    research_response = Mock()
    research_response.data = "Research findings..."
    
    # Mock analysis agent response
    analysis_response = Mock()
    analysis_response.data = "Analysis results..."
    
    # Mock synthesis agent response
    synthesis_response = Mock()
    synthesis_response.data = "Final research notes..."
    
    mock_runner_instance.run.side_effect = [
        research_response,
        analysis_response, 
        synthesis_response
    ]
    
    # Test execution
    research_team = ResearchTeam()
    result = research_team.research_topic(test_syllabus_section)
    
    # Verify agent coordination
    assert mock_runner_instance.run.call_count == 3
    assert result["section_id"] == test_syllabus_section["section_id"]
    assert "research_summary" in result
```

#### EditingTeam Tests  
```python
# UPDATED: Test Agents SDK instead of Assistant API
@patch('agents.Runner')  
@patch('agents.Agent')
def test_synthesize_chapter_agents_sdk(self, mock_agent, mock_runner):
    mock_agent_instance = Mock()
    mock_agent.return_value = mock_agent_instance
    
    mock_runner_instance = Mock()
    mock_runner.return_value = mock_runner_instance
    
    # Mock synthesis response
    mock_response = Mock()
    mock_response.data = "Synthesized chapter content..."
    mock_runner_instance.run.return_value = mock_response
    
    editing_team = EditingTeam(vector_store_id="vs_123")
    result = editing_team.synthesize_chapter(test_research_data)
    
    # Verify Agents SDK usage
    mock_agent.assert_called_once()
    mock_runner.assert_called_once_with(agent=mock_agent_instance)
    assert isinstance(result, ChapterDraft)
```

### Integration Testing

#### End-to-End Agent Workflow
```python
def test_complete_agent_workflow():
    """Test full Research → Editing → Finalizer agent pipeline"""
    
    # 1. ResearchTeam multi-agent workflow
    research_team = ResearchTeam(vector_store_id="vs_research")
    research_notes = research_team.research_topic(test_syllabus_section)
    
    # 2. EditingTeam agent synthesis
    editing_team = EditingTeam(vector_store_id="vs_editing") 
    chapter_draft = editing_team.synthesize_chapter({
        "target_section": test_syllabus_section["section_id"],
        "research_notes": research_notes
    })
    
    # 3. Editorial Finalizer multi-agent assessment
    finalizer = MultiAgentEditorialFinalizer()
    final_result = finalizer.finalize_content([chapter_draft])
    
    # Verify complete agent workflow
    assert research_notes["section_id"] == test_syllabus_section["section_id"]
    assert chapter_draft.section_id == test_syllabus_section["section_id"]
    assert final_result["final_transcript"]
    assert final_result["quality_issues"]
```

## Risk Assessment & Mitigation

### High-Risk Areas

#### 1. **Performance Impact**
- **Risk**: Agent workflows may be slower than current implementation
- **Mitigation**: Performance benchmarking and optimization
- **Monitoring**: Track synthesis times and optimize prompts

#### 2. **Quality Changes**
- **Risk**: Different implementation may produce different content quality
- **Mitigation**: Side-by-side quality comparison during migration
- **Validation**: Content quality assessment by domain experts

#### 3. **Integration Complexity**
- **Risk**: Agent-to-agent coordination more complex than current flows
- **Mitigation**: Comprehensive integration testing
- **Fallback**: Staged rollout with rollback capability

#### 4. **Cost Impact**
- **Risk**: Agent workflows may increase API costs
- **Mitigation**: Cost monitoring and optimization
- **Budget**: Reserve budget for migration period cost variance

### Mitigation Strategies

#### Technical Mitigation
```python
# Performance monitoring
import time
from agents.monitoring import AgentMetrics

class PerformanceMonitoredAgent:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.metrics = AgentMetrics()
    
    def run_with_monitoring(self, query: str):
        start_time = time.time()
        try:
            result = self.runner.run(query)
            duration = time.time() - start_time
            self.metrics.record_success(duration, len(result.data))
            return result
        except Exception as e:
            duration = time.time() - start_time  
            self.metrics.record_failure(duration, str(e))
            raise
```

## Timeline & Resource Allocation

### Detailed Schedule (3-4 Weeks)

#### Week 1: Preparation & Planning
- **Mon-Tue**: Emergency team training on Agents SDK
- **Wed-Thu**: Migration environment setup and baseline testing
- **Fri**: ResearchTeam rewrite begins

#### Week 2: Core Migration
- **Mon-Wed**: ResearchTeam complete rewrite and testing
- **Thu-Fri**: EditingTeam API migration begins

#### Week 3: Completion & Integration
- **Mon-Tue**: EditingTeam migration completion
- **Wed**: Editorial Finalizer audit and compliance
- **Thu-Fri**: Integration testing begins

#### Week 4: Validation & Deployment
- **Mon-Tue**: End-to-end testing and performance validation
- **Wed**: Quality assurance and stakeholder review
- **Thu**: Production deployment preparation
- **Fri**: Migration completion and monitoring setup

### Resource Requirements

#### Development Resources
- **Lead Developer**: 1 FTE × 4 weeks (migration execution)
- **Architecture Reviewer**: 0.5 FTE × 4 weeks (compliance verification)
- **QA Engineer**: 0.5 FTE × 2 weeks (testing and validation)
- **DevOps Engineer**: 0.2 FTE × 1 week (deployment support)

#### Infrastructure Resources
- **Development Environment**: Agents SDK compatible environment
- **Testing Infrastructure**: Comprehensive test automation setup
- **Monitoring Tools**: Agent performance and compliance monitoring
- **Backup Systems**: Rollback capability for emergency recovery

## Success Criteria

### Technical Success Metrics
- [ ] **100% Agents SDK Compliance**: All components use Agents SDK exclusively
- [ ] **Zero Assistant API Usage**: No `client.beta.assistants.*` calls remaining
- [ ] **Agent Workflow Functionality**: Multi-agent coordination working correctly
- [ ] **Performance Maintenance**: Processing times within 20% of current baseline
- [ ] **Quality Preservation**: Content quality equal or better than current

### Process Success Metrics  
- [ ] **Test Coverage**: 100% of migrated components have comprehensive tests
- [ ] **Integration Validation**: End-to-end workflows tested and validated
- [ ] **Documentation**: Complete documentation of new agent architectures
- [ ] **Team Knowledge**: All team members trained on Agents SDK patterns
- [ ] **Monitoring**: Real-time compliance and performance monitoring operational

### Business Success Metrics
- [ ] **Functionality Preservation**: All user stories continue to work correctly
- [ ] **Delivery Timeline**: Migration completed within 4-week target
- [ ] **Cost Control**: Migration costs within approved budget
- [ ] **Stakeholder Satisfaction**: Leadership approval of migration results

## Rollback Plan

### Rollback Triggers
- **Critical Functionality Failure**: Core workflows not working
- **Performance Degradation**: >50% slower than baseline
- **Quality Regression**: Significant content quality degradation
- **Timeline Overrun**: Migration taking >6 weeks
- **Cost Overrun**: Costs exceeding 200% of budget

### Rollback Procedure

#### Emergency Rollback (Same Day)
1. **Immediate**: Revert to previous commit/branch
2. **Validation**: Run full test suite on reverted code
3. **Communication**: Notify all stakeholders of rollback
4. **Analysis**: Begin immediate failure analysis

#### Planned Rollback (1-2 Days)
1. **Assessment**: Comprehensive impact analysis  
2. **Data Preservation**: Preserve any valuable migration work
3. **Selective Revert**: Keep successfully migrated components
4. **Re-planning**: Develop revised migration approach

### Recovery Strategy
- **Lessons Integration**: Apply lessons from failed migration
- **Process Enhancement**: Improve migration methodology
- **Risk Mitigation**: Address identified failure modes
- **Timeline Adjustment**: Realistic re-planning of migration

## Post-Migration Monitoring

### Compliance Monitoring
```python
# Automated compliance verification
def verify_agents_sdk_compliance():
    """Daily compliance check for Agents SDK usage"""
    violations = []
    
    # Check for prohibited Assistant API usage
    if detect_assistant_api_usage():
        violations.append("Assistant API usage detected")
    
    # Check for proper Agent instantiation
    if not verify_agent_patterns():
        violations.append("Invalid Agent patterns detected")
        
    # Check for FileSearchTool usage
    if not verify_file_search_tool():
        violations.append("Incorrect file search implementation")
    
    return violations
```

### Performance Monitoring
- **Agent Response Times**: Track individual agent performance
- **Workflow Duration**: Monitor end-to-end processing times
- **API Usage**: Monitor OpenAI API consumption patterns
- **Error Rates**: Track agent failure rates and error patterns

### Quality Monitoring
- **Content Quality Metrics**: Automated quality assessment
- **User Satisfaction**: Stakeholder feedback on migration results
- **Functional Verification**: Continuous validation of workflow functionality

## Conclusion

This comprehensive migration plan addresses the catastrophic architecture violations discovered across the entire codebase. The plan provides:

1. **Complete Coverage**: All non-compliant components identified and migration planned
2. **Detailed Implementation**: Specific code changes and architecture patterns
3. **Risk Mitigation**: Comprehensive risk assessment and mitigation strategies
4. **Success Criteria**: Clear metrics for migration success
5. **Rollback Capability**: Emergency procedures for migration failure

The migration represents a **complete sprint's worth of work** (3-4 weeks) but is essential for establishing proper architecture compliance and preventing future catastrophic failures.

Successful completion will result in:
- 100% Agents SDK compliance across all components
- Proper multi-agent workflow implementation
- Comprehensive testing and monitoring
- Bulletproof architecture governance preventing future violations

---

**Migration Status**: READY FOR EXECUTION  
**Priority**: EMERGENCY - CRITICAL PATH  
**Timeline**: 3-4 weeks  
**Success Criteria**: 100% Agents SDK compliance  

**Generated with [Claude Code](https://claude.ai/code)**

Co-Authored-By: Claude <noreply@anthropic.com>