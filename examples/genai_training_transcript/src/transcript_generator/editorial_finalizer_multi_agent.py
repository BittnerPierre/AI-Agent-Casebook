"""
Multi-Agent Editorial Finalizer - Sophisticated Quality Control and Misconduct Tracking

This module implements US-005: Editorial Finalizer Misconduct Tracking using sophisticated
multi-agent analysis with OpenAI Agents SDK. This replaces the basic pattern matching
approach with LLM-based semantic assessment.

Module: transcript_generator/editorial_finalizer_multi_agent.py
Interface: MultiAgentEditorialFinalizer class with finalize_content(chapters), track_issues() methods

Acceptance Criteria:
- EditorialFinalizer outputs final_transcript.md + quality_issues.json with misconduct tracking
- Integration Point: Consumes chapter_drafts/, exports quality metadata for evaluation module
- Reviews generated content for quality issues and narrative consistency
- Uses multi-agent system for sophisticated quality assessment

Multi-Agent Architecture:
- SemanticAlignmentAgent: Content-syllabus semantic alignment verification
- PedagogicalQualityAgent: Educational effectiveness and learning design assessment
- GroundednessAgent: Evidence quality and factual grounding evaluation
- ContentDepthAgent: Content complexity and depth analysis
- GuidelinesComplianceAgent: Training course guidelines adherence checking
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

# Import centralized environment configuration
from common.environment import env_config

# LangSmith tracing support
from agents import set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor

# Import multi-agent quality assessment system
from .agents import (
    AssessmentConfidence,
    ChapterContent,
    QualityConsensusOrchestrator,
    QualityDimension,
)

# Import common types
from .types import ChapterDraft, IssueSeverity, QualityIssue

# Import base class from original implementation  
from .editorial_finalizer import EditorialFinalizer

# LangSmith integration for US-007 evaluation logging
try:
    from ..evaluation import EvaluationLogger
    LANGSMITH_EVALUATION_AVAILABLE = True
except ImportError:
    EvaluationLogger = None
    LANGSMITH_EVALUATION_AVAILABLE = False


class MultiAgentEditorialFinalizer(EditorialFinalizer):
    """
    Enhanced Editorial Finalizer with multi-agent quality assessment capabilities.
    
    This class extends the base EditorialFinalizer with sophisticated LLM-based
    quality assessment using specialized agents for different quality dimensions.
    Provides fallback to basic pattern matching when multi-agent system is unavailable.
    """
    
    def __init__(self, 
                 output_dir: str = "output", 
                 quality_dir: str = "quality_issues",
                 enable_multi_agent: bool = True,
                 model: str = "gpt-4o-mini"):
        """
        Initialize the Multi-Agent Editorial Finalizer.
        
        Args:
            output_dir: Directory to write final transcript
            quality_dir: Directory to write quality issues JSON files
            enable_multi_agent: Enable sophisticated multi-agent assessment
            model: Model to use for multi-agent assessment
        """
        # Initialize base class with multi-agent disabled to prevent recursion
        super().__init__(output_dir, quality_dir, enable_multi_agent=False, model=model)
        
        # Multi-agent configuration - check OpenAI API key availability
        if enable_multi_agent and not env_config.openai_api_key:
            self.logger.warning("Multi-agent assessment requested but OpenAI API key not configured")
            self.enable_multi_agent = False
        else:
            self.enable_multi_agent = enable_multi_agent
        
        self.model = model
        
        # Configure LangSmith tracing for finalizer agents
        self.langsmith_enabled = False
        langsmith_api_key = env_config.langsmith_api_key
        langsmith_project = env_config.langsmith_project
        langsmith_tracing = env_config.langsmith_tracing_enabled
        
        if langsmith_api_key and langsmith_tracing:
            try:
                # Configure tracing processor for OpenAI Agents SDK
                os.environ['LANGSMITH_API_KEY'] = langsmith_api_key
                os.environ['LANGSMITH_PROJECT'] = langsmith_project
                
                # Set up trace processors for agents
                set_trace_processors([OpenAIAgentsTracingProcessor()])
                
                self.langsmith_enabled = True
                logging.getLogger(__name__).info(f"Editorial finalizer LangSmith tracing configured for project: {langsmith_project}")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to configure LangSmith tracing: {e}")
        else:
            if not langsmith_api_key:
                logging.getLogger(__name__).debug("LANGSMITH_API_KEY not found. LangSmith tracing disabled.")
            if not langsmith_tracing:
                logging.getLogger(__name__).debug("LANGSMITH_TRACING not enabled. LangSmith tracing disabled.")
        
        # Initialize multi-agent orchestrator if available
        if self.enable_multi_agent:
            self.quality_orchestrator = QualityConsensusOrchestrator(model=self.model)
            self.logger.info(f"Multi-agent quality assessment enabled with model: {self.model}")
        else:
            self.quality_orchestrator = None
            self.logger.warning("Multi-agent assessment disabled - using fallback pattern matching")
        
        # Store agent assessments for enhanced metrics
        self.agent_assessments_cache = {}
        
        # Initialize LangSmith evaluation logger for US-007
        self._evaluation_logger: EvaluationLogger | None = None
        if LANGSMITH_EVALUATION_AVAILABLE:
            try:
                self._evaluation_logger = EvaluationLogger(
                    project_name="story-ops",
                    enabled=True
                )
                self.logger.info("LangSmith evaluation logging enabled for EditorialFinalizer")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangSmith evaluation logger: {e}")
                self._evaluation_logger = None
        else:
            self.logger.info("LangSmith evaluation logging not available")

    def finalize_content(self, chapters: list[ChapterDraft], syllabus: dict[str, Any] | None = None) -> tuple[str, str]:
        """
        Finalize content using multi-agent quality assessment.
        
        This enhanced version uses sophisticated multi-agent analysis when available,
        falling back to basic pattern matching when necessary.
        
        Args:
            chapters: List of chapter drafts to review and finalize
            syllabus: Optional syllabus for alignment checking
            
        Returns:
            Tuple of (final_transcript_path, quality_summary_path)
        """
        self.logger.info(f"Starting multi-agent content finalization for {len(chapters)} chapters")
        
        # Track all quality issues across chapters
        all_quality_issues = []
        final_sections = []
        
        # Process each chapter with multi-agent assessment
        for chapter in chapters:
            self.logger.info(f"Processing chapter: {chapter.section_id}")
            
            # Run multi-agent quality assessment
            if self.enable_multi_agent:
                try:
                    agent_assessment = self._run_multi_agent_assessment(chapter, syllabus)
                    quality_issues = self._convert_agent_assessment_to_issues(agent_assessment, chapter.section_id)
                    # Store enhanced assessment data
                    self._store_agent_assessment(chapter.section_id, agent_assessment)
                    
                    # US-007: Log agent conversations to LangSmith
                    if self._evaluation_logger:
                        self._log_agent_assessment_to_langsmith(chapter, agent_assessment, syllabus)
                    
                    self.logger.info(f"Multi-agent assessment completed for {chapter.section_id}")
                except Exception as e:
                    self.logger.error(f"Multi-agent assessment failed for {chapter.section_id}: {e}")
                    # Fallback to basic assessment
                    quality_issues = self.track_issues(chapter, syllabus)
            else:
                # Use basic pattern matching assessment
                quality_issues = self.track_issues(chapter, syllabus)
            
            all_quality_issues.extend(quality_issues)
            
            # Create enhanced quality issues file for this section
            section_quality = self._create_section_quality_data(chapter, quality_issues)
            
            # Write quality issues for this section to quality_issues/{section_id}.json
            quality_file = self.quality_dir / f"{chapter.section_id}.json"
            try:
                with open(quality_file, 'w', encoding='utf-8') as f:
                    json.dump(section_quality, f, indent=2, ensure_ascii=False)
            except OSError as e:
                self.logger.error(f"Failed to write quality file {quality_file}: {e}")
                raise
            
            # Add to final transcript (regardless of issues - flagged in quality_issues)
            final_sections.append({
                "section_id": chapter.section_id,
                "title": chapter.title or f"Section {chapter.section_id}",
                "content": chapter.content
            })
        
        # Create final transcript according to schema
        final_transcript = {
            "course_title": syllabus.get("course_title", "Generated Training Course") if syllabus else "Generated Training Course",
            "sections": final_sections
        }
        
        # Write final transcript JSON
        transcript_json_path = self.output_dir / "final_transcript.json"
        try:
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(final_transcript, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.logger.error(f"Failed to write final transcript {transcript_json_path}: {e}")
            raise
        
        # Create markdown version for readability
        md_path = self.output_dir / "final_transcript.md"
        self._create_markdown_transcript(final_transcript, md_path)
        
        # Create enhanced summary quality report
        summary_path = self.quality_dir / "quality_summary.json"
        self._create_enhanced_quality_summary(all_quality_issues, summary_path)
        
        self.logger.info(f"Multi-agent content finalization complete. Transcript: {md_path}, Quality: {summary_path}")
        return str(md_path), str(summary_path)

    def _run_multi_agent_assessment(self, chapter: ChapterDraft, syllabus: dict[str, Any] | None) -> dict[str, Any]:
        """Run multi-agent quality assessment on a chapter"""
        
        # Find corresponding syllabus section
        syllabus_section = None
        if syllabus and "sections" in syllabus:
            for section in syllabus["sections"]:
                if section.get("section_id") == chapter.section_id:
                    syllabus_section = section
                    break
        
        # Create chapter content for agent assessment
        chapter_content = ChapterContent(
            section_id=chapter.section_id,
            title=chapter.title or "",
            content=chapter.content,
            syllabus_section=syllabus_section
        )
        
        # Run multi-agent assessment
        return asyncio.run(self.quality_orchestrator.assess_chapter(chapter_content))

    def _convert_agent_assessment_to_issues(self, agent_assessment: dict[str, Any], section_id: str) -> list[QualityIssue]:
        """Convert multi-agent assessment to QualityIssue objects"""
        quality_issues = []
        
        # Extract findings from all agent assessments
        for dimension, assessment_data in agent_assessment.get("agent_assessments", {}).items():
            for finding in assessment_data.get("findings", []):
                # Map agent findings to QualityIssue format
                severity = self._map_severity(finding.get("severity", "INFO"))
                misconduct_category = self._map_misconduct_category(dimension, finding.get("category", ""))
                
                quality_issue = QualityIssue(
                    description=finding.get("description", "Quality issue detected"),
                    severity=severity,
                    section_id=section_id,
                    misconduct_category=misconduct_category
                )
                quality_issues.append(quality_issue)
        
        return quality_issues

    def _map_severity(self, agent_severity: str) -> IssueSeverity:
        """Map agent assessment severity to IssueSeverity enum"""
        severity_mapping = {
            "INFO": IssueSeverity.INFO,
            "WARNING": IssueSeverity.WARNING,
            "ERROR": IssueSeverity.ERROR
        }
        return severity_mapping.get(agent_severity, IssueSeverity.INFO)

    def _map_misconduct_category(self, dimension: str, agent_category: str) -> str:
        """Map agent assessment dimension and category to misconduct category"""
        # Map agent dimensions to misconduct categories
        dimension_mapping = {
            "semantic_alignment": "content_syllabus_alignment",
            "pedagogical_quality": "training_principles_violations",
            "groundedness": "groundedness_violations",
            "content_depth": "inadequate_level",
            "guidelines_compliance": "training_principles_violations"
        }
        
        # Use agent-provided category if available, otherwise map from dimension
        if agent_category:
            return agent_category
        
        return dimension_mapping.get(dimension, "training_principles_violations")

    def _store_agent_assessment(self, section_id: str, agent_assessment: dict[str, Any]):
        """Store agent assessment for enhanced metrics and reporting"""
        self.agent_assessments_cache[section_id] = agent_assessment

    def _create_section_quality_data(self, chapter: ChapterDraft, quality_issues: list[QualityIssue]) -> dict[str, Any]:
        """Create enhanced section quality data including agent assessments"""
        
        # Basic quality data structure
        section_quality = {
            "section_id": chapter.section_id,
            "issues": [{
                "description": issue.description,
                "severity": issue.severity.value,
                "misconduct_category": issue.misconduct_category
            } for issue in quality_issues],
            "approved": not any(issue.severity == IssueSeverity.ERROR for issue in quality_issues)
        }
        
        # Add enhanced multi-agent assessment data if available
        if chapter.section_id in self.agent_assessments_cache:
            agent_data = self.agent_assessments_cache[chapter.section_id]
            
            section_quality.update({
                "agent_assessments": agent_data.get("agent_assessments", {}),
                "overall_quality_score": agent_data.get("overall_quality_score", 0.0),
                "consensus_confidence": agent_data.get("consensus_confidence", 0.0),
                "dimension_scores": agent_data.get("dimension_scores", {}),
                "consolidated_recommendations": agent_data.get("consolidated_recommendations", []),
                "assessment_metadata": agent_data.get("assessment_metadata", {})
            })
        
        return section_quality

    def _create_enhanced_quality_summary(self, all_issues: list[QualityIssue], output_path: Path):
        """Create enhanced quality summary including multi-agent metrics"""
        
        # Create basic summary
        summary = {
            "total_issues": len(all_issues),
            "issues_by_severity": {
                "INFO": len([i for i in all_issues if i.severity == IssueSeverity.INFO]),
                "WARNING": len([i for i in all_issues if i.severity == IssueSeverity.WARNING]),
                "ERROR": len([i for i in all_issues if i.severity == IssueSeverity.ERROR])
            },
            "issues_by_category": {},
            "sections_with_errors": list(set(i.section_id for i in all_issues if i.severity == IssueSeverity.ERROR and i.section_id)),
            "details": [
                {
                    "section_id": issue.section_id,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "category": issue.misconduct_category
                }
                for issue in all_issues
            ]
        }
        
        # Count by misconduct category
        for issue in all_issues:
            if issue.misconduct_category:
                summary["issues_by_category"][issue.misconduct_category] = \
                    summary["issues_by_category"].get(issue.misconduct_category, 0) + 1
        
        # Add multi-agent assessment summary if available
        if self.agent_assessments_cache:
            agent_summary = self._create_agent_assessment_summary()
            summary.update(agent_summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def _create_agent_assessment_summary(self) -> dict[str, Any]:
        """Create summary of multi-agent assessments"""
        
        if not self.agent_assessments_cache:
            return {}
        
        # Aggregate agent scores across all sections
        dimension_scores = {}
        overall_scores = []
        consensus_scores = []
        
        for section_id, assessment in self.agent_assessments_cache.items():
            overall_scores.append(assessment.get("overall_quality_score", 0.0))
            consensus_scores.append(assessment.get("consensus_confidence", 0.0))
            
            # Aggregate dimension scores
            for dimension, score in assessment.get("dimension_scores", {}).items():
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = []
                dimension_scores[dimension].append(score)
        
        # Calculate aggregated metrics
        avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
        
        avg_dimension_scores = {}
        for dimension, scores in dimension_scores.items():
            avg_dimension_scores[dimension] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "multi_agent_summary": {
                "average_overall_quality": round(avg_overall_score, 3),
                "average_consensus_confidence": round(avg_consensus, 3),
                "average_dimension_scores": avg_dimension_scores,
                "sections_assessed": len(self.agent_assessments_cache),
                "agent_model_used": self.model
            }
        }

    def _log_agent_assessment_to_langsmith(self, 
                                         chapter: ChapterDraft, 
                                         agent_assessment: dict[str, Any],
                                         syllabus: dict[str, Any] | None = None) -> None:
        """
        Log agent assessment conversations and quality data to LangSmith for US-007.
        
        Captures detailed agent interaction data for post-execution analysis and evaluation.
        
        Args:
            chapter: Chapter that was assessed
            agent_assessment: Complete agent assessment results
            syllabus: Syllabus context for the assessment
        """
        try:
            # Structure agent interaction data for LangSmith
            agent_interaction_data = {
                "chapter_metadata": {
                    "section_id": chapter.section_id,
                    "title": getattr(chapter, 'title', 'Untitled'),
                    "content_length": len(chapter.content),
                    "word_count": len(chapter.content.split()) if chapter.content else 0
                },
                "assessment_results": {
                    "overall_quality_score": agent_assessment.get("overall_quality_score", 0.0),
                    "consensus_confidence": agent_assessment.get("consensus_confidence", 0.0),
                    "dimension_scores": agent_assessment.get("dimension_scores", {}),
                    "consolidated_findings": agent_assessment.get("consolidated_findings", []),
                    "consolidated_recommendations": agent_assessment.get("consolidated_recommendations", [])
                },
                "agent_conversations": agent_assessment.get("agent_assessments", {}),
                "syllabus_context": {
                    "syllabus_provided": syllabus is not None,
                    "course_title": syllabus.get("title", "Unknown") if syllabus else "Unknown",
                    "section_count": len(syllabus.get("sections", [])) if syllabus else 0
                },
                "assessment_metadata": agent_assessment.get("assessment_metadata", {})
            }
            
            # Log the interaction using EvaluationLogger
            self._evaluation_logger.log_agent_interaction(
                agent_name="editorial_finalizer_multi_agent",
                interaction_type="quality_assessment",
                input_data={
                    "chapter_content": chapter.content[:1000] + "..." if len(chapter.content) > 1000 else chapter.content,  # Truncate for logging
                    "section_id": chapter.section_id,
                    "syllabus_context": agent_interaction_data["syllabus_context"]
                },
                output_data=agent_interaction_data["assessment_results"],
                metadata=agent_interaction_data
            )
            
            self.logger.debug(f"Logged agent assessment for {chapter.section_id} to LangSmith")
            
        except Exception as e:
            self.logger.warning(f"Failed to log agent assessment to LangSmith for {chapter.section_id}: {e}")

    def get_quality_metrics(self) -> dict[str, Any]:
        """
        Get enhanced quality metrics from multi-agent assessment system.
        
        This method provides sophisticated quality metrics for US-007 and US-008 evaluation logging,
        including agent-specific assessments and consensus scoring.
        
        Returns:
            Dictionary containing comprehensive quality metrics for LangSmith logging
        """
        # Get basic metrics from parent class
        base_metrics = super().get_quality_metrics()
        
        # Add multi-agent specific metrics if available
        if self.enable_multi_agent and self.agent_assessments_cache:
            agent_metrics = self._extract_agent_metrics()
            base_metrics.update(agent_metrics)
        
        return base_metrics

    def _extract_agent_metrics(self) -> dict[str, Any]:
        """Extract metrics from cached agent assessments"""
        
        if not self.agent_assessments_cache:
            return {}
        
        # Aggregate metrics across all assessed sections
        dimension_scores = {}
        overall_scores = []
        consensus_scores = []
        
        for section_id, assessment in self.agent_assessments_cache.items():
            overall_scores.append(assessment.get("overall_quality_score", 0.0))
            consensus_scores.append(assessment.get("consensus_confidence", 0.0))
            
            for dimension, score in assessment.get("dimension_scores", {}).items():
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = []
                dimension_scores[dimension].append(score)
        
        # Calculate enhanced metrics
        agent_metrics = {
            "semantic_alignment_score": self._avg_score(dimension_scores.get("semantic_alignment", [])),
            "pedagogical_quality_score": self._avg_score(dimension_scores.get("pedagogical_quality", [])),
            "content_depth_assessment": self._avg_score(dimension_scores.get("content_depth", [])),
            "agent_consensus_score": self._avg_score(consensus_scores),
            "groundedness_confidence": self._avg_score(dimension_scores.get("groundedness", [])),
            "guideline_compliance_score": self._avg_score(dimension_scores.get("guidelines_compliance", [])),
            "multi_agent_overall_score": self._avg_score(overall_scores)
        }
        
        return agent_metrics

    def _avg_score(self, scores: list[float]) -> float:
        """Calculate average score with proper handling of empty lists"""
        return round(sum(scores) / len(scores), 3) if scores else 0.0


# Backward compatibility alias
EditorialFinalizerMultiAgent = MultiAgentEditorialFinalizer