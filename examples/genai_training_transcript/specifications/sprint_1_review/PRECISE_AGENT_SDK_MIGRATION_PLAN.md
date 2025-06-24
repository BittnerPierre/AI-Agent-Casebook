# Precise Agent SDK Migration Plan: Technical Implementation Guide

**Plan ID**: AGENT-SDK-MIGRATION-TECHNICAL-001  
**Scope**: Complete technical roadmap for Agent SDK implementation  
**Timeline**: 17 days (3.5 weeks) for full migration  
**Date**: 2025-06-23  

## Executive Summary

**Current State**: Hybrid system with some Agent SDK components working, others using stubs/wrong APIs  
**Target State**: 100% Agent SDK compliance with functional AI content generation  
**Critical Finding**: System has proper infrastructure but lacks functional implementations in core workflow  

**Key Components Requiring Migration**:
1. **ResearchTeam**: Replace stub data processing with multi-agent workflow
2. **EditingTeam**: Migrate Assistant API → Agents SDK  
3. **Planner**: Replace stub with Agent SDK planning
4. **Reviewer**: Replace pattern matching with semantic AI review
5. **Main Entry Point**: Async Agent SDK coordination

## Phase 1: Infrastructure Preparation (Days 1-3)

### Day 1: Data Models and Types

#### Create `src/transcript_generator/models.py`
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ResearchFindings(BaseModel):
    content_sources: List[Dict[str, Any]] = Field(description="Relevant content sources identified")
    relevance_scores: Dict[str, float] = Field(description="Relevance scores for each source")
    search_strategy: str = Field(description="Search strategy used")

class AnalysisResults(BaseModel):
    key_insights: List[str] = Field(description="Key learning insights extracted")
    supporting_evidence: List[str] = Field(description="Supporting evidence for insights")
    confidence_score: float = Field(description="Confidence in analysis quality")

class ResearchSynthesis(BaseModel):
    unified_summary: str = Field(description="Coherent research summary")
    key_themes: List[str] = Field(description="Primary themes identified")
    actionable_insights: List[str] = Field(description="Actionable insights for content creation")

class CourseAgenda(BaseModel):
    modules: List[Dict[str, Any]] = Field(description="Detailed module specifications")
    total_duration: int = Field(description="Total course duration in minutes")
    learning_path: List[str] = Field(description="Optimal learning sequence")
    prerequisites: Dict[str, List[str]] = Field(description="Module prerequisites")

class ReviewResults(BaseModel):
    alignment_score: float = Field(description="Syllabus alignment score (0-1)")
    quality_issues: List[str] = Field(description="Identified quality issues")
    recommendations: List[str] = Field(description="Improvement recommendations")
    approval_status: bool = Field(description="Whether content is approved")

class DocumentedContent(BaseModel):
    organized_content: str = Field(description="Organized content from research")
    key_sources: List[str] = Field(description="Key source materials used")
    coverage_gaps: List[str] = Field(description="Identified coverage gaps")

class ChapterDraft(BaseModel):
    content: str = Field(description="Generated chapter content")
    pedagogical_notes: List[str] = Field(description="Pedagogical approach notes")
    quality_score: float = Field(description="Self-assessed quality score")

class ReviewFeedback(BaseModel):
    strengths: List[str] = Field(description="Content strengths identified")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    specific_suggestions: List[str] = Field(description="Specific improvement suggestions")
    overall_score: float = Field(description="Overall content quality score")
```

### Day 2: Agent SDK Availability Infrastructure

#### Update all tool files with Agent SDK detection
```python
# Pattern for all files: research_team.py, planner.py, reviewer.py, editing_team.py

try:
    import inspect
    import os
    from agents import Agent, Runner
    _AGENTS_SDK_AVAILABLE = (
        inspect.iscoroutinefunction(getattr(Runner, "run", None))
        and os.environ.get("OPENAI_API_KEY")
    )
except ImportError:
    _AGENTS_SDK_AVAILABLE = False
```

### Day 3: Testing Infrastructure Setup

#### Update test configuration for Agent SDK
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture
def agent_sdk_available():
    return os.environ.get("OPENAI_API_KEY") is not None

@pytest.fixture
def mock_agent_unavailable(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    return True
```

## Phase 2: ResearchTeam Migration (Days 4-8)

### Day 4: ResearchTeam Agent Architecture

#### Replace `src/transcript_generator/tools/research_team.py` lines 94-141

**CURRENT (Lines 98-141) - Complete stub replacement:**
```python
# DELETE ENTIRE SECTION:
try:
    raw_items = asyncio.run(self.retriever.get_related_content(key_topics))
except Exception as e:
    raw_items = []

# Basic string processing...
research_summary = " ".join(summary_parts)
return {"section_id": section_id, "research_summary": research_summary, ...}
```

**REPLACE WITH:**
```python
async def research_topic(self, syllabus_section: dict[str, Any]) -> dict[str, Any]:
    """
    Multi-agent research workflow: Researcher → Analyst → Synthesizer
    """
    if not _AGENTS_SDK_AVAILABLE:
        return self._fallback_research(syllabus_section)
    
    section_id = syllabus_section.get("section_id", "unknown")
    key_topics = syllabus_section.get("key_topics", [])
    
    # Step 1: Research Agent - Find relevant content
    research_result = await self._execute_research_phase(key_topics)
    
    # Step 2: Analysis Agent - Extract key insights
    analysis_result = await self._execute_analysis_phase(research_result, key_topics)
    
    # Step 3: Synthesis Agent - Create coherent summary
    synthesis_result = await self._execute_synthesis_phase(analysis_result, section_id)
    
    return {
        "section_id": section_id,
        "research_summary": synthesis_result.unified_summary,
        "key_themes": synthesis_result.key_themes,
        "actionable_insights": synthesis_result.actionable_insights,
        "knowledge_references": self._format_references(research_result)
    }

async def _execute_research_phase(self, key_topics: list[str]) -> ResearchFindings:
    """Phase 1: Content Discovery"""
    researcher_agent = Agent(
        name="ResearcherAgent",
        instructions="""You are a Research Specialist who identifies and retrieves relevant 
        training content for specific learning topics. Use the knowledge retrieval system 
        to find the most relevant modules and content pieces.
        
        Focus on:
        1. Comprehensive content discovery
        2. Relevance assessment
        3. Source quality evaluation
        4. Coverage gap identification
        
        Be thorough but focused on educational value.""",
        model="gpt-4o-mini",
        output_type=ResearchFindings
    )
    
    # Use existing knowledge retrieval system
    try:
        raw_items = asyncio.run(self.retriever.get_related_content(key_topics))
    except Exception as e:
        raw_items = []
    
    research_context = f"""
    RESEARCH REQUEST
    Key Topics: {key_topics}
    Available Content: {len(raw_items)} items found
    
    Content Summary:
    {self._format_content_for_analysis(raw_items)}
    
    Task: Analyze this content and identify the most relevant sources for training development.
    Provide relevance scores and explain your selection strategy.
    """
    
    result = await Runner.run(
        starting_agent=researcher_agent,
        input=research_context
    )
    
    findings = result.final_output_as(ResearchFindings)
    # Attach actual content items for next phase
    findings.content_sources = raw_items
    return findings

async def _execute_analysis_phase(self, research_findings: ResearchFindings, 
                                 key_topics: list[str]) -> AnalysisResults:
    """Phase 2: Content Analysis"""
    analyst_agent = Agent(
        name="AnalystAgent", 
        instructions="""You are a Content Analyst who extracts key learning points 
        from retrieved content. Focus on identifying the most important concepts, 
        examples, and insights that support the learning objectives.
        
        Expertise areas:
        1. Learning objective alignment
        2. Conceptual hierarchy identification
        3. Example and case study extraction
        4. Knowledge gap analysis
        5. Pedagogical value assessment
        
        Extract insights that will be valuable for content creation.""",
        model="gpt-4o-mini",
        output_type=AnalysisResults
    )
    
    analysis_context = f"""
    CONTENT ANALYSIS REQUEST
    
    Target Learning Topics: {key_topics}
    Research Strategy Used: {research_findings.search_strategy}
    
    Content to Analyze:
    {self._format_research_for_analysis(research_findings)}
    
    Task: Extract the most valuable learning insights that would support 
    training content creation for these topics. Focus on concepts, examples, 
    and practical applications.
    """
    
    result = await Runner.run(
        starting_agent=analyst_agent,
        input=analysis_context
    )
    
    return result.final_output_as(AnalysisResults)

async def _execute_synthesis_phase(self, analysis_results: AnalysisResults, 
                                  section_id: str) -> ResearchSynthesis:
    """Phase 3: Knowledge Synthesis"""
    synthesizer_agent = Agent(
        name="SynthesizerAgent",
        instructions="""You are a Knowledge Synthesizer who creates coherent 
        research summaries from multiple content sources. Create unified 
        summaries that capture key themes and actionable insights for 
        training content development.
        
        Synthesis approach:
        1. Theme identification and organization
        2. Insight prioritization
        3. Knowledge flow optimization
        4. Actionable recommendation creation
        5. Coherent narrative construction
        
        Create summaries that training content creators can immediately use.""",
        model="gpt-4o-mini",
        output_type=ResearchSynthesis
    )
    
    synthesis_context = f"""
    KNOWLEDGE SYNTHESIS REQUEST
    
    Target Section: {section_id}
    
    Analysis Results:
    Key Insights: {analysis_results.key_insights}
    Supporting Evidence: {analysis_results.supporting_evidence}
    Analysis Confidence: {analysis_results.confidence_score}
    
    Task: Create a coherent research summary that captures the key themes 
    and provides actionable insights for training content creation on this section.
    
    Focus on creating a unified narrative that content creators can use 
    to develop high-quality training materials.
    """
    
    result = await Runner.run(
        starting_agent=synthesizer_agent,
        input=synthesis_context
    )
    
    return result.final_output_as(ResearchSynthesis)

def _fallback_research(self, syllabus_section: dict[str, Any]) -> dict[str, Any]:
    """Fallback when Agent SDK unavailable"""
    section_id = syllabus_section.get("section_id", "unknown")
    return {
        "section_id": section_id,
        "research_summary": f"[FALLBACK] Research summary for {section_id}",
        "key_themes": ["fallback-theme"],
        "actionable_insights": ["fallback-insight"],
        "knowledge_references": []
    }
```

### Day 5-6: ResearchTeam Helper Methods

```python
def _format_content_for_analysis(self, raw_items: list[dict]) -> str:
    """Format content for research agent analysis"""
    formatted = []
    for item in raw_items[:10]:  # Limit for context size
        content_id = item.get("module_id") or item.get("content_id", "unknown")
        title = item.get("title", "Untitled")
        preview = item.get("content_preview", "")[:200]  # Limit preview
        formatted.append(f"ID: {content_id}, Title: {title}, Preview: {preview}...")
    return "\n".join(formatted)

def _format_research_for_analysis(self, findings: ResearchFindings) -> str:
    """Format research findings for analysis phase"""
    content_summary = []
    for source in findings.content_sources:
        relevance = findings.relevance_scores.get(source.get("content_id", ""), 0.0)
        content_summary.append(f"Relevance: {relevance:.2f} - {source}")
    return "\n".join(content_summary)

def _format_references(self, findings: ResearchFindings) -> list[dict]:
    """Format knowledge references for output"""
    references = []
    for source in findings.content_sources:
        ref = {
            "content_id": source.get("content_id", "unknown"),
            "title": source.get("title", "Untitled"),
            "relevance_score": findings.relevance_scores.get(source.get("content_id", ""), 0.0),
            "key_points": ["Generated from research findings"]
        }
        references.append(ref)
    return references
```

### Day 7-8: ResearchTeam Testing and Integration

## Phase 3: Supporting Components Migration (Days 9-11)

### Day 9: Planner Migration

#### Replace `src/transcript_generator/tools/planner.py` entirely

```python
"""
Advanced syllabus planning using OpenAI Agents SDK for curriculum design.
"""

import asyncio
from typing import List, Dict, Any
from ..models import CourseAgenda

# Agent SDK availability check
try:
    import inspect
    import os
    from agents import Agent, Runner
    _AGENTS_SDK_AVAILABLE = (
        inspect.iscoroutinefunction(getattr(Runner, "run", None))
        and os.environ.get("OPENAI_API_KEY")
    )
except ImportError:
    _AGENTS_SDK_AVAILABLE = False

class SyllabusPlanner:
    """Advanced curriculum planner using Agent SDK"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        if _AGENTS_SDK_AVAILABLE:
            self.planner_agent = Agent(
                name="SyllabusPlanner",
                instructions="""You are a Curriculum Planning Specialist who transforms 
                high-level module lists into detailed course agendas. Your expertise includes:
                
                1. Learning progression analysis
                2. Optimal module sequencing
                3. Duration estimation based on content complexity
                4. Prerequisite mapping and dependency analysis
                5. Learning objective refinement and alignment
                6. Cognitive load optimization
                
                Create detailed course agendas with proper timing, clear dependencies, 
                and well-structured learning objectives that follow pedagogical best practices.""",
                model=model,
                output_type=CourseAgenda
            )
    
    def refine_syllabus(self, modules: List[Any], config: Dict[str, Any]) -> Any:
        """Main entry point for syllabus refinement"""
        if not _AGENTS_SDK_AVAILABLE:
            return self._fallback_planning(modules, config)
        
        return asyncio.run(self._async_refine_syllabus(modules, config))
    
    async def _async_refine_syllabus(self, modules: List[Any], 
                                   config: Dict[str, Any]) -> CourseAgenda:
        """Async Agent SDK implementation"""
        context = f"""
        CURRICULUM PLANNING REQUEST
        
        Raw Module List: {modules}
        Configuration Parameters: {config}
        
        Transform this into a detailed course agenda with:
        
        1. OPTIMAL MODULE SEQUENCING
           - Identify logical learning progression
           - Account for prerequisite relationships
           - Optimize for knowledge building
        
        2. DURATION ESTIMATION
           - Estimate realistic completion times
           - Account for complexity levels
           - Include buffer time for practice
        
        3. PREREQUISITE MAPPING
           - Identify module dependencies
           - Create clear learning paths
           - Flag potential bottlenecks
        
        4. LEARNING OBJECTIVE REFINEMENT
           - Clarify learning outcomes
           - Align with course goals
           - Ensure measurable objectives
        
        Provide a comprehensive course agenda that maximizes learning effectiveness.
        """
        
        result = await Runner.run(
            starting_agent=self.planner_agent,
            input=context
        )
        
        return result.final_output_as(CourseAgenda)
    
    def _fallback_planning(self, modules: List[Any], config: Dict[str, Any]) -> List[Any]:
        """Fallback when Agent SDK unavailable"""
        print("[planner] Using fallback planning (Agent SDK unavailable)")
        return modules

# Maintain backward compatibility
def refine_syllabus(modules: List[Any], config: Dict[str, Any]) -> Any:
    """Backward compatible function"""
    planner = SyllabusPlanner()
    return planner.refine_syllabus(modules, config)
```

### Day 10: Reviewer Migration

#### Replace `src/transcript_generator/tools/reviewer.py`

```python
"""
Advanced content review using OpenAI Agents SDK for quality assessment.
"""

import asyncio
from typing import Any, Dict
from ..models import ReviewResults

# Agent SDK availability check
try:
    import inspect
    import os
    from agents import Agent, Runner
    _AGENTS_SDK_AVAILABLE = (
        inspect.iscoroutinefunction(getattr(Runner, "run", None))
        and os.environ.get("OPENAI_API_KEY")
    )
except ImportError:
    _AGENTS_SDK_AVAILABLE = False

class TranscriptReviewer:
    """Advanced content reviewer using Agent SDK"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        if _AGENTS_SDK_AVAILABLE:
            self.review_agent = Agent(
                name="TranscriptReviewer",
                instructions="""You are a Training Content Quality Reviewer specializing in:
                
                1. SYLLABUS ALIGNMENT VERIFICATION
                   - Check coverage of learning objectives
                   - Verify topic completeness
                   - Assess depth appropriateness
                
                2. CONTENT COHERENCE EVALUATION
                   - Evaluate logical flow
                   - Check consistency in tone/style
                   - Assess clarity and readability
                
                3. RESEARCH INTEGRATION VALIDATION
                   - Verify research insights are incorporated
                   - Check factual accuracy
                   - Assess evidence quality
                
                4. PEDAGOGICAL EFFECTIVENESS REVIEW
                   - Evaluate learning scaffold effectiveness
                   - Check for active learning elements
                   - Assess engagement potential
                
                Provide specific, actionable feedback for improvement.""",
                model=model,
                output_type=ReviewResults
            )
    
    def review_transcript(self, module: str, content: str, 
                         syllabus_item: Any, research_note: str) -> None:
        """Main entry point for transcript review"""
        if not _AGENTS_SDK_AVAILABLE:
            return self._fallback_review(module, content, syllabus_item, research_note)
        
        result = asyncio.run(self._async_review_transcript(
            module, content, syllabus_item, research_note
        ))
        
        # Raise exception if critical issues found
        if not result.approval_status:
            issues_summary = "; ".join(result.quality_issues)
            raise RuntimeError(f"[reviewer] Quality issues in module '{module}': {issues_summary}")
    
    async def _async_review_transcript(self, module: str, content: str,
                                     syllabus_item: Any, research_note: str) -> ReviewResults:
        """Async Agent SDK implementation"""
        context = f"""
        CONTENT QUALITY REVIEW REQUEST
        
        Module: {module}
        
        CONTENT TO REVIEW:
        {content}
        
        SYLLABUS REQUIREMENTS:
        {syllabus_item}
        
        RESEARCH FOUNDATION:
        {research_note}
        
        EVALUATION CRITERIA:
        
        1. SYLLABUS ALIGNMENT (0-25 points)
           - Are all learning objectives addressed?
           - Is topic coverage complete and appropriate?
           - Does content depth match requirements?
        
        2. RESEARCH INTEGRATION (0-25 points)
           - Are research insights properly incorporated?
           - Is factual information accurate?
           - Are sources used effectively?
        
        3. CONTENT QUALITY (0-25 points)
           - Is the content logically structured?
           - Is language clear and appropriate?
           - Are examples relevant and helpful?
        
        4. PEDAGOGICAL EFFECTIVENESS (0-25 points)
           - Does content support learning goals?
           - Are active learning elements present?
           - Is engagement level appropriate?
        
        Provide detailed analysis and specific recommendations for improvement.
        Score each area and give overall approval/rejection decision.
        """
        
        result = await Runner.run(
            starting_agent=self.review_agent,
            input=context
        )
        
        return result.final_output_as(ReviewResults)
    
    def _fallback_review(self, module: str, content: str, 
                        syllabus_item: Any, research_note: str) -> None:
        """Fallback when Agent SDK unavailable"""
        if not research_note.strip():
            raise RuntimeError(f"[reviewer] No research note to review for module: {module}")
        
        # Basic validation
        title = syllabus_item.get("title") if isinstance(syllabus_item, dict) else str(syllabus_item)
        if title and title not in content:
            raise RuntimeError(f"[reviewer] Transcript for module '{module}' does not mention the module title.")

# Maintain backward compatibility
def review_transcript(module: str, content: str, syllabus_item: Any, research_note: str) -> None:
    """Backward compatible function"""
    reviewer = TranscriptReviewer()
    reviewer.review_transcript(module, content, syllabus_item, research_note)
```

### Day 11: Integration Testing for Phase 3

## Phase 4: EditingTeam Migration (Days 12-14)

### Day 12-13: EditingTeam Agent SDK Migration

#### Critical changes to `src/transcript_generator/tools/editing_team.py`

**Lines 318-339 - Replace Assistant API with Agent SDK:**

```python
# DELETE ASSISTANT API CREATION:
# assistant = self.client.beta.assistants.create(...)

# REPLACE WITH AGENT SDK SETUP:
def _setup_agent_workflow(self, vector_store_id: str) -> None:
    """Setup multi-agent editing workflow using Agent SDK"""
    
    # Documentalist Agent - Content extraction and organization
    self.documentalist_agent = Agent(
        name="DocumentalistAgent",
        instructions="""You are a Documentalist who extracts and organizes relevant 
        content from research materials for training content creation.
        
        Your responsibilities:
        1. Review provided research notes and knowledge base content
        2. Extract the most relevant information for the target section
        3. Organize content by themes and learning objectives
        4. Identify key concepts, examples, and insights
        5. Note any gaps that need additional research
        
        Focus on comprehensive content gathering that supports learning goals.""",
        model=self.model,
        tools=[FileSearchTool(vector_store_ids=[vector_store_id])] if vector_store_id else [],
        output_type=DocumentedContent
    )
    
    # Writer Agent - Content creation and pedagogical design
    self.writer_agent = Agent(
        name="WriterAgent", 
        instructions="""You are a Training Content Writer who creates engaging, 
        pedagogically sound educational content.
        
        Apply these pedagogical patterns:
        1. LEARNING SCAFFOLDING - Build from simple to complex concepts
        2. ACTIVE LEARNING - Include exercises, questions, examples
        3. KNOWLEDGE ANCHORING - Connect new concepts to existing knowledge
        4. MULTIPLE MODALITIES - Use text, examples, scenarios
        5. CLEAR STRUCTURE - Logical flow with clear transitions
        
        Create content that is engaging, practical, and educationally effective.""",
        model=self.model,
        output_type=ChapterDraft
    )
    
    # Reviewer Agent - Quality assessment and improvement
    self.reviewer_agent = Agent(
        name="ReviewerAgent",
        instructions="""You are a Content Reviewer who evaluates draft content 
        for pedagogical effectiveness, accuracy, and engagement.
        
        Evaluation criteria:
        1. LEARNING EFFECTIVENESS - Does content support learning goals?
        2. CLARITY - Is information clear and well-organized?
        3. ENGAGEMENT - Will learners find this interesting and relevant?
        4. ACCURACY - Is information factually correct?
        5. COMPLETENESS - Are all required topics covered?
        
        Provide specific, actionable feedback for improvement.""",
        model=self.model,
        output_type=ReviewFeedback
    )
```

**Lines 341-371 - Replace Assistant API workflow with Agent SDK:**

```python
# DELETE THREAD-BASED WORKFLOW
# REPLACE WITH:

async def _execute_agent_synthesis_workflow(self, research_notes: Dict[str, Any], 
                                          target_section: str) -> str:
    """Execute multi-agent content synthesis workflow"""
    
    # Phase 1: Documentalist - Content extraction and organization
    doc_context = self._create_documentalist_context(target_section, research_notes)
    doc_result = await Runner.run(
        starting_agent=self.documentalist_agent,
        input=doc_context
    )
    documented_content = doc_result.final_output_as(DocumentedContent)
    
    # Phase 2: Writer - Initial draft creation
    writer_context = self._create_writer_context(documented_content, target_section)
    writer_result = await Runner.run(
        starting_agent=self.writer_agent,
        input=writer_context
    )
    draft_content = writer_result.final_output_as(ChapterDraft)
    
    # Phase 3: Reviewer - Quality assessment
    review_context = self._create_review_context(draft_content, target_section)
    review_result = await Runner.run(
        starting_agent=self.reviewer_agent,
        input=review_context
    )
    review_feedback = review_result.final_output_as(ReviewFeedback)
    
    # Phase 4: Writer - Final revision based on feedback
    if review_feedback.overall_score < 0.8:  # If quality below threshold
        revision_context = self._create_revision_context(draft_content, review_feedback)
        final_result = await Runner.run(
            starting_agent=self.writer_agent,
            input=revision_context
        )
        final_content = final_result.final_output_as(ChapterDraft)
    else:
        final_content = draft_content
    
    return final_content.content

def _create_documentalist_context(self, target_section: str, research_notes: Dict[str, Any]) -> str:
    """Create context for documentalist phase"""
    return f"""
    CONTENT DOCUMENTATION REQUEST
    
    Target Section: {target_section}
    
    Research Notes Available:
    {json.dumps(research_notes, indent=2)}
    
    Task: Extract and organize all relevant content for this section.
    Focus on key concepts, examples, and insights that will support learning objectives.
    Identify any gaps where additional information might be needed.
    """

def _create_writer_context(self, documented_content: DocumentedContent, target_section: str) -> str:
    """Create context for writer phase"""
    return f"""
    TRAINING CONTENT CREATION REQUEST
    
    Target Section: {target_section}
    
    Organized Research Content:
    {documented_content.organized_content}
    
    Key Sources Used: {documented_content.key_sources}
    Coverage Gaps Identified: {documented_content.coverage_gaps}
    
    Task: Create engaging, pedagogically effective training content for this section.
    
    Requirements:
    - Use learning scaffolding (simple to complex)
    - Include practical examples and exercises
    - Ensure clear structure and logical flow
    - Make content engaging and relevant
    - Address any coverage gaps appropriately
    
    Create content that effectively teaches the target concepts.
    """

def _create_review_context(self, draft_content: ChapterDraft, target_section: str) -> str:
    """Create context for reviewer phase"""
    return f"""
    CONTENT QUALITY REVIEW REQUEST
    
    Target Section: {target_section}
    
    Draft Content:
    {draft_content.content}
    
    Pedagogical Notes: {draft_content.pedagogical_notes}
    Self-Assessment Score: {draft_content.quality_score}
    
    Task: Evaluate this content for quality and effectiveness.
    
    Review criteria:
    - Learning effectiveness
    - Clarity and organization
    - Engagement level
    - Factual accuracy
    - Completeness
    
    Provide specific feedback for improvement.
    """

def _create_revision_context(self, draft_content: ChapterDraft, 
                           review_feedback: ReviewFeedback) -> str:
    """Create context for revision phase"""
    return f"""
    CONTENT REVISION REQUEST
    
    Original Draft:
    {draft_content.content}
    
    Review Feedback:
    Strengths: {review_feedback.strengths}
    Weaknesses: {review_feedback.weaknesses}
    Specific Suggestions: {review_feedback.specific_suggestions}
    Overall Score: {review_feedback.overall_score}
    
    Task: Revise the content based on the feedback to improve quality.
    Address the weaknesses while preserving the strengths.
    Implement the specific suggestions where appropriate.
    """
```

### Day 14: EditingTeam Integration and Testing

## Phase 5: Main Entry Point Migration (Days 15-16)

### Day 15: Async Coordination in `run.py`

**Lines 87-108 - Replace synchronous coordination with async Agent SDK:**

```python
# REPLACE SYNCHRONOUS CALLS WITH ASYNC COORDINATION

async def async_main():
    """Async main function for Agent SDK coordination"""
    
    # Initialize configuration
    config = load_config("config.yaml")
    
    # Setup knowledge infrastructure
    knowledge_retriever = setup_knowledge_retriever(config)
    knowledge_mcp_server = setup_mcp_server(config)
    
    # Generate/load syllabus and agenda
    agenda = generate_course_agenda(config)
    
    # Phase 1: Parallel research across all sections
    research_team = ResearchTeam(
        output_dir=notes_dir,
        knowledge_retriever=knowledge_retriever
    )
    
    print(f"[main] Starting parallel research for {len(agenda)} sections...")
    research_tasks = []
    for agenda_item in agenda:
        section_data = {
            "section_id": agenda_item.get("title") if isinstance(agenda_item, dict) else str(agenda_item),
            "key_topics": agenda_item.get("topics", []) if isinstance(agenda_item, dict) else []
        }
        task = research_team.research_topic(section_data)
        research_tasks.append((section_data["section_id"], task))
    
    research_results = await asyncio.gather(*[task for _, task in research_tasks])
    research_notes = {section_id: result for (section_id, _), result in zip(research_tasks, research_results)}
    
    print(f"[main] Research completed for {len(research_notes)} sections")
    
    # Phase 2: Parallel content editing
    editing_team = EditingTeam(
        model=config.get("model", "gpt-4o-mini"),
        knowledge_mcp_server=knowledge_mcp_server
    )
    
    print(f"[main] Starting parallel content editing...")
    editing_tasks = []
    for section_id, research_data in research_notes.items():
        task = editing_team.synthesize_chapter(research_data)
        editing_tasks.append((section_id, task))
    
    draft_results = await asyncio.gather(*[task for _, task in editing_tasks])
    drafts = {section_id: result for (section_id, _), result in zip(editing_tasks, draft_results)}
    
    print(f"[main] Content editing completed for {len(drafts)} sections")
    
    # Phase 3: Quality assessment and finalization
    editorial_finalizer = EditorialFinalizerMultiAgent(
        model=config.get("model", "gpt-4o-mini")
    )
    
    final_transcripts = {}
    for section_id, draft_content in drafts.items():
        # Review and finalize each section
        final_content = await editorial_finalizer.finalize_transcript(
            module=section_id,
            draft=draft_content,
            research_notes=research_notes[section_id]
        )
        final_transcripts[section_id] = final_content
    
    print(f"[main] Finalization completed for {len(final_transcripts)} sections")
    
    # Save results
    save_transcripts(final_transcripts, config)
    
    return final_transcripts

def main():
    """Main entry point with Agent SDK support"""
    if _AGENTS_SDK_AVAILABLE:
        return asyncio.run(async_main())
    else:
        print("[main] Agent SDK unavailable, using fallback synchronous mode")
        return synchronous_main()  # Keep existing implementation as fallback

def synchronous_main():
    """Fallback synchronous implementation"""
    # Keep existing implementation for when Agent SDK unavailable
    pass
```

### Day 16: Integration Testing and Error Handling

## Phase 6: Quality Validation (Day 17)

### Day 17: End-to-End Testing

#### 1. **Full Integration Test**
```bash
cd src && poetry run python run.py --config ../config.yaml
```

#### 2. **Agent SDK Functionality Test**
```python
# Test script to verify Agent SDK is actually being used
async def test_agent_sdk_usage():
    research_team = ResearchTeam()
    test_section = {
        "section_id": "test_module", 
        "key_topics": ["machine learning", "neural networks"]
    }
    
    result = await research_team.research_topic(test_section)
    
    # Verify we get actual AI-generated content, not stubs
    assert "fallback" not in result["research_summary"].lower()
    assert len(result["key_themes"]) > 0
    assert len(result["actionable_insights"]) > 0
    
    print("✅ Agent SDK research working correctly")
```

#### 3. **UAT Validation**
```python
# Verify system generates actual AI content
def validate_content_generation():
    config = load_config("config.yaml")
    result = asyncio.run(async_main())
    
    for section_id, content in result.items():
        # Verify content is not a stub
        assert not content.startswith("[FALLBACK]")
        assert len(content) > 100  # Reasonable content length
        assert "generated script" not in content.lower()  # Not stub content
        
    print("✅ UAT validation passed - real content generated")
```

## Success Criteria

### Technical Compliance
- [ ] 100% Agent SDK usage in core workflow components
- [ ] Zero Assistant API calls in agentic components
- [ ] All components have proper fallback mechanisms
- [ ] Integration tests pass with real content generation

### Functional Validation
- [ ] UAT demonstrates actual AI content generation
- [ ] Multi-agent workflows execute correctly
- [ ] Generated content meets quality standards
- [ ] Performance maintains acceptable levels

### Quality Assurance
- [ ] Unit tests pass: `poetry run pytest tests/ -v`
- [ ] Integration tests pass: `cd src && poetry run python run.py --config ../config.yaml`
- [ ] Import validation: `poetry run python -c "from transcript_generator.tools import *; print('✅ Imports work')"`
- [ ] LangSmith tracing works correctly
- [ ] Error handling and fallbacks function properly

## Migration Timeline Summary

| Phase | Days | Focus | Deliverable |
|-------|------|--------|-------------|
| 1 | 1-3 | Infrastructure | Data models, Agent SDK detection, testing setup |
| 2 | 4-8 | ResearchTeam | Multi-agent research workflow |
| 3 | 9-11 | Supporting | Planner and Reviewer migration |
| 4 | 12-14 | EditingTeam | Assistant API → Agent SDK migration |
| 5 | 15-16 | Coordination | Async main entry point |
| 6 | 17 | Validation | End-to-end testing and UAT |

**Total Duration**: 17 days (3.5 weeks)
**Risk Level**: MEDIUM (controlled, phased approach)
**Success Probability**: HIGH (detailed technical plan with fallbacks)

## Conclusion

This migration plan provides:
1. **Precise technical roadmap** with exact code changes
2. **Phased approach** minimizing integration risk
3. **Fallback mechanisms** ensuring system stability
4. **Quality validation** confirming real functionality
5. **Timeline realism** based on actual implementation complexity

The plan transforms the current hybrid system into a fully functional Agent SDK implementation while maintaining backward compatibility and system reliability.

---

**Plan Status**: READY FOR EXECUTION  
**Next Action**: Begin Phase 1 infrastructure preparation  
**Success Criteria**: Real AI content generation replacing stub implementations  

**Generated with [Claude Code](https://claude.ai/code)**

Co-Authored-By: Claude <noreply@anthropic.com>