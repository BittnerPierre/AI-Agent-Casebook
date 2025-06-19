"""
Workflow Orchestrator (US-006)

Component Integration Orchestrator for seamless execution of 
Research Team → Editing Team → Editorial Finalizer pipeline.

This module serves as the main pipeline entry point that coordinates
all system components with proper error handling, recovery, and progress tracking.

Author: Claude Code - Sprint 1 Week 2
Reference: US-006 Component Integration Orchestrator (Issue #53)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from .editorial_finalizer import ChapterDraft, EditorialFinalizer
from .tools.editing_team import edit_chapters
from .tools.research_team import ResearchTeam

# LangSmith integration for US-007 evaluation logging
try:
    from ..evaluation import EvaluationLogger, LangSmithIntegration
    LANGSMITH_INTEGRATION_AVAILABLE = True
except ImportError:
    EvaluationLogger = None
    LangSmithIntegration = None
    LANGSMITH_INTEGRATION_AVAILABLE = False


@dataclass
class WorkflowResult:
    """Result of complete workflow execution"""
    success: bool
    final_transcript_path: str | None = None
    quality_summary_path: str | None = None
    research_notes: dict[str, Any] | None = None
    chapter_drafts: list[ChapterDraft] | None = None
    execution_time: float | None = None
    errors: list[str] | None = None
    quality_metrics: dict[str, Any] | None = None


@dataclass
class WorkflowConfig:
    """Configuration for workflow orchestrator"""
    output_dir: str = "output"
    research_output_dir: str = "research_notes"
    quality_output_dir: str = "quality_issues"
    overwrite_existing: bool = False
    max_retries: int = 3
    timeout_per_phase: int = 300  # 5 minutes per phase
    continue_on_errors: bool = True
    enable_progress_tracking: bool = True
    # LangSmith evaluation logging configuration (US-007)
    enable_langsmith_logging: bool = True
    langsmith_project_name: str = "story-ops"
    langsmith_auto_send: bool = True


class WorkflowOrchestrator:
    """
    Component Integration Orchestrator for transcript generation pipeline.
    
    Coordinates execution of Research Team → Editing Team → Editorial Finalizer
    with comprehensive error handling, progress tracking, and recovery mechanisms.
    
    Architecture:
    - Async/await pattern for efficient I/O operations
    - Rich console integration for progress tracking
    - Configurable error handling and retry logic
    - Temporary directory management with cleanup
    - Component lifecycle management
    """
    
    def __init__(self, config: WorkflowConfig | None = None):
        """
        Initialize WorkflowOrchestrator with configuration.
        
        Args:
            config: Optional workflow configuration (uses defaults if None)
        """
        self.config = config or WorkflowConfig()
        self.console = Console() if self.config.enable_progress_tracking else None
        self.logger = logging.getLogger(__name__)
        
        # Component instances
        self._research_team: ResearchTeam | None = None
        self._editorial_finalizer: EditorialFinalizer | None = None
        
        # LangSmith integration for US-007 evaluation logging
        self._langsmith_integration: LangSmithIntegration | None = None
        if (self.config.enable_langsmith_logging and LANGSMITH_INTEGRATION_AVAILABLE):
            try:
                self._langsmith_integration = LangSmithIntegration(
                    project_name=self.config.langsmith_project_name,
                    auto_send_enabled=self.config.langsmith_auto_send
                )
                self.logger.info("[WorkflowOrchestrator] LangSmith integration enabled")
            except Exception as e:
                self.logger.warning(f"[WorkflowOrchestrator] Failed to initialize LangSmith integration: {e}")
                self._langsmith_integration = None
        else:
            self.logger.info("[WorkflowOrchestrator] LangSmith integration disabled")
        
        # Execution state
        self._current_phase = "initialization"
        self._start_time: datetime | None = None
        self._errors: list[str] = []
        
        self.logger.info(f"[WorkflowOrchestrator] Initialized with config: {self.config}")
    
    async def execute_pipeline(self, syllabus: dict[str, Any]) -> WorkflowResult:
        """
        Execute complete transcript generation pipeline.
        
        Main orchestration method that coordinates all system components
        in sequence: Research → Editing → Finalization.
        
        Args:
            syllabus: Syllabus structure with course and section definitions
            
        Returns:
            WorkflowResult with execution outcome and generated artifacts
        """
        self._start_time = datetime.now()
        self._errors = []
        
        self.logger.info("[WorkflowOrchestrator] Starting pipeline execution")
        
        if self.console:
            self.console.print("[bold blue]🚀 Starting Transcript Generation Pipeline[/bold blue]")
        
        try:
            # Phase 1: Research Team - Generate research notes
            self._current_phase = "research"
            research_notes = await self._execute_research_phase(syllabus)
            
            if not research_notes and not self.config.continue_on_errors:
                return self._create_error_result("Research phase failed and continue_on_errors=False")
            
            # Phase 2: Editing Team - Generate chapter drafts
            self._current_phase = "editing"
            chapter_drafts = await self._execute_editing_phase(research_notes, syllabus)
            
            if not chapter_drafts and not self.config.continue_on_errors:
                return self._create_error_result("Editing phase failed and continue_on_errors=False")
            
            # Phase 3: Editorial Finalizer - Produce final transcript
            self._current_phase = "finalization"
            final_transcript_path, quality_summary_path, quality_metrics = await self._execute_finalization_phase(
                chapter_drafts, syllabus
            )
            
            # Calculate execution time
            execution_time = (datetime.now() - self._start_time).total_seconds()
            
            # Create success result
            result = WorkflowResult(
                success=True,
                final_transcript_path=final_transcript_path,
                quality_summary_path=quality_summary_path,
                research_notes=research_notes,
                chapter_drafts=chapter_drafts,
                execution_time=execution_time,
                errors=self._errors if self._errors else None,
                quality_metrics=quality_metrics
            )
            
            if self.console:
                self._display_success_summary(result)
            
            # US-007: Send execution metadata to LangSmith for post-execution analysis
            if self._langsmith_integration:
                try:
                    execution_context = {
                        "execution_mode": "pipeline",
                        "continue_on_errors": self.config.continue_on_errors,
                        "timeout_per_phase": self.config.timeout_per_phase,
                        "max_retries": self.config.max_retries,
                        "current_phase": self._current_phase,
                        "phases_completed": ["research", "editing", "finalization"],
                        "resource_usage": {
                            "total_execution_time": execution_time,
                            "research_notes_generated": len(research_notes) if research_notes else 0,
                            "chapter_drafts_created": len(chapter_drafts) if chapter_drafts else 0
                        }
                    }
                    
                    # Send asynchronously (don't block pipeline completion)
                    asyncio.create_task(
                        self._langsmith_integration.send_execution_metadata(
                            workflow_result=result,
                            syllabus=syllabus,
                            execution_context=execution_context
                        )
                    )
                    self.logger.debug("[WorkflowOrchestrator] LangSmith logging initiated for successful execution")
                except Exception as e:
                    self.logger.warning(f"[WorkflowOrchestrator] LangSmith logging failed: {e}")
            
            self.logger.info(f"[WorkflowOrchestrator] Pipeline completed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Pipeline execution failed in {self._current_phase} phase: {e!s}"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            
            if self.console:
                self.console.print(f"[bold red]❌ Pipeline Failed: {error_msg}[/bold red]")
            
            # US-007: Log failed execution to LangSmith for analysis
            error_result = self._create_error_result(error_msg)
            if self._langsmith_integration:
                try:
                    execution_time = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
                    execution_context = {
                        "execution_mode": "pipeline",
                        "failed_phase": self._current_phase,
                        "execution_time_before_failure": execution_time,
                        "error_message": error_msg,
                        "continue_on_errors": self.config.continue_on_errors,
                        "timeout_per_phase": self.config.timeout_per_phase
                    }
                    
                    # Send error data asynchronously
                    asyncio.create_task(
                        self._langsmith_integration.send_execution_metadata(
                            workflow_result=error_result,
                            syllabus=syllabus,
                            execution_context=execution_context
                        )
                    )
                    self.logger.debug("[WorkflowOrchestrator] LangSmith logging initiated for failed execution")
                except Exception as log_error:
                    self.logger.warning(f"[WorkflowOrchestrator] LangSmith error logging failed: {log_error}")
            
            return error_result
    
    async def _execute_research_phase(self, syllabus: dict[str, Any]) -> dict[str, Any]:
        """
        Execute research phase using ResearchTeam component.
        
        Args:
            syllabus: Syllabus structure with sections to research
            
        Returns:
            Aggregated research notes from all sections
        """
        if self.console:
            self.console.print("[yellow]📚 Phase 1: Research Team - Generating research notes[/yellow]")
        
        try:
            # Initialize ResearchTeam
            research_output_dir = Path(self.config.output_dir) / self.config.research_output_dir
            research_output_dir.mkdir(parents=True, exist_ok=True)
            
            self._research_team = ResearchTeam(
                output_dir=str(research_output_dir),
                config={
                    "max_key_points_per_item": 3,
                    "words_per_key_point": 5,
                    "max_summary_length": 1000
                }
            )
            
            # Get syllabus sections
            sections = syllabus.get("sections", [])
            if not sections:
                error_msg = "No sections found in syllabus"
                self.logger.warning(f"[WorkflowOrchestrator] {error_msg}")
                self._errors.append(error_msg)
                return {}
            
            # Process each section with progress tracking
            aggregated_research = {}
            
            if self.console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task("Processing sections...", total=len(sections))
                    
                    for section in sections:
                        section_id = section.get("section_id", f"section_{len(aggregated_research)}")
                        progress.update(task, description=f"Researching {section_id}")
                        
                        try:
                            # Research this section
                            research_notes = await asyncio.wait_for(
                                asyncio.to_thread(self._research_team.research_topic, section),
                                timeout=self.config.timeout_per_phase / len(sections)
                            )
                            
                            if research_notes:
                                aggregated_research[section_id] = research_notes
                                self.logger.info(f"[WorkflowOrchestrator] Research completed for section: {section_id}")
                            else:
                                error_msg = f"No research notes generated for section: {section_id}"
                                self.logger.warning(f"[WorkflowOrchestrator] {error_msg}")
                                self._errors.append(error_msg)
                        
                        except asyncio.TimeoutError:
                            error_msg = f"Research timeout for section: {section_id}"
                            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
                            self._errors.append(error_msg)
                        
                        except Exception as e:
                            error_msg = f"Research failed for section {section_id}: {e!s}"
                            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
                            self._errors.append(error_msg)
                        
                        progress.advance(task)
            else:
                # Process without progress tracking
                for section in sections:
                    section_id = section.get("section_id", f"section_{len(aggregated_research)}")
                    
                    try:
                        research_notes = await asyncio.to_thread(self._research_team.research_topic, section)
                        if research_notes:
                            aggregated_research[section_id] = research_notes
                            self.logger.info(f"[WorkflowOrchestrator] Research completed for section: {section_id}")
                    except Exception as e:
                        error_msg = f"Research failed for section {section_id}: {e!s}"
                        self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
                        self._errors.append(error_msg)
            
            self.logger.info(f"[WorkflowOrchestrator] Research phase completed: {len(aggregated_research)} sections processed")
            return aggregated_research
            
        except Exception as e:
            error_msg = f"Research phase setup failed: {e!s}"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            raise
    
    async def _execute_editing_phase(self, research_notes: dict[str, Any], syllabus: dict[str, Any]) -> list[ChapterDraft]:
        """
        Execute editing phase using EditingTeam component.
        
        Args:
            research_notes: Research notes from research phase
            syllabus: Original syllabus for context
            
        Returns:
            List of chapter drafts for finalization
        """
        if self.console:
            self.console.print("[cyan]✏️ Phase 2: Editing Team - Generating chapter drafts[/cyan]")
        
        try:
            if not research_notes:
                error_msg = "No research notes available for editing phase"
                self.logger.warning(f"[WorkflowOrchestrator] {error_msg}")
                self._errors.append(error_msg)
                return []
            
            # Prepare research notes for editing team (convert format)
            editing_input = {}
            section_mapping = {}
            
            for section_id, notes in research_notes.items():
                # Convert research notes to editing team format
                research_summary = notes.get("research_summary", "")
                editing_input[section_id] = research_summary
                section_mapping[section_id] = notes
            
            # Execute editing with timeout
            editing_config = {
                "output_format": "markdown",
                "include_metadata": True
            }
            
            chapter_drafts_dict = await asyncio.wait_for(
                asyncio.to_thread(edit_chapters, editing_input, editing_config),
                timeout=self.config.timeout_per_phase
            )
            
            # Convert to ChapterDraft objects
            chapter_drafts = []
            sections = syllabus.get("sections", [])
            section_titles = {s.get("section_id"): s.get("title", "Untitled Section") for s in sections}
            
            for section_id, draft_content in chapter_drafts_dict.items():
                if draft_content:  # Only include non-empty drafts
                    chapter_draft = ChapterDraft(
                        section_id=section_id,
                        content=draft_content,
                        title=section_titles.get(section_id, f"Chapter: {section_id}")
                    )
                    chapter_drafts.append(chapter_draft)
                    self.logger.info(f"[WorkflowOrchestrator] Chapter draft created for section: {section_id}")
                else:
                    error_msg = f"Empty chapter draft for section: {section_id}"
                    self.logger.warning(f"[WorkflowOrchestrator] {error_msg}")
                    self._errors.append(error_msg)
            
            self.logger.info(f"[WorkflowOrchestrator] Editing phase completed: {len(chapter_drafts)} chapters generated")
            return chapter_drafts
            
        except asyncio.TimeoutError:
            error_msg = "Editing phase timeout"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            raise
        
        except Exception as e:
            error_msg = f"Editing phase failed: {e!s}"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            raise
    
    async def _execute_finalization_phase(
        self, 
        chapter_drafts: list[ChapterDraft], 
        syllabus: dict[str, Any]
    ) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """
        Execute finalization phase using EditorialFinalizer component.
        
        Args:
            chapter_drafts: Chapter drafts from editing phase
            syllabus: Original syllabus for quality assessment
            
        Returns:
            Tuple of (final_transcript_path, quality_summary_path, quality_metrics)
        """
        if self.console:
            self.console.print("[green]🔍 Phase 3: Editorial Finalizer - Quality control and finalization[/green]")
        
        try:
            if not chapter_drafts:
                error_msg = "No chapter drafts available for finalization"
                self.logger.warning(f"[WorkflowOrchestrator] {error_msg}")
                self._errors.append(error_msg)
                return None, None, None
            
            # Initialize EditorialFinalizer
            output_dir = Path(self.config.output_dir)
            quality_dir = Path(self.config.output_dir) / self.config.quality_output_dir
            
            output_dir.mkdir(parents=True, exist_ok=True)
            quality_dir.mkdir(parents=True, exist_ok=True)
            
            self._editorial_finalizer = EditorialFinalizer(
                output_dir=str(output_dir),
                quality_dir=str(quality_dir)
            )
            
            # Execute finalization with timeout
            final_transcript_path, quality_summary_path = await asyncio.wait_for(
                asyncio.to_thread(self._editorial_finalizer.finalize_content, chapter_drafts, syllabus),
                timeout=self.config.timeout_per_phase
            )
            
            # Get quality metrics
            quality_metrics = self._editorial_finalizer.get_quality_metrics()
            
            self.logger.info("[WorkflowOrchestrator] Finalization completed")
            self.logger.info(f"[WorkflowOrchestrator] Final transcript: {final_transcript_path}")
            self.logger.info(f"[WorkflowOrchestrator] Quality summary: {quality_summary_path}")
            self.logger.info(f"[WorkflowOrchestrator] Quality score: {quality_metrics.get('quality_score', 'N/A')}")
            
            return final_transcript_path, quality_summary_path, quality_metrics
            
        except asyncio.TimeoutError:
            error_msg = "Finalization phase timeout"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            raise
        
        except Exception as e:
            error_msg = f"Finalization phase failed: {e!s}"
            self.logger.error(f"[WorkflowOrchestrator] {error_msg}")
            self._errors.append(error_msg)
            raise
    
    def _create_error_result(self, error_msg: str) -> WorkflowResult:
        """Create WorkflowResult for error conditions"""
        execution_time = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        return WorkflowResult(
            success=False,
            execution_time=execution_time,
            errors=self._errors + [error_msg] if error_msg not in self._errors else self._errors
        )
    
    def _display_success_summary(self, result: WorkflowResult):
        """Display success summary using Rich console"""
        if not self.console:
            return
        
        self.console.print("[bold green]✅ Pipeline Completed Successfully![/bold green]")
        self.console.print(f"⏱️  Execution time: {result.execution_time:.2f} seconds")
        
        if result.final_transcript_path:
            self.console.print(f"📄 Final transcript: {result.final_transcript_path}")
        
        if result.quality_summary_path:
            self.console.print(f"📊 Quality summary: {result.quality_summary_path}")
        
        if result.quality_metrics:
            quality_score = result.quality_metrics.get("quality_score", 0)
            total_issues = result.quality_metrics.get("total_issues", 0)
            self.console.print(f"🎯 Quality score: {quality_score:.2f} ({total_issues} issues detected)")
        
        if result.errors:
            self.console.print(f"⚠️  Warnings: {len(result.errors)} non-critical issues")
    
    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on orchestrator and all components.
        
        Returns:
            Health status information
        """
        health_status = {
            "orchestrator_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "output_dir": self.config.output_dir,
                "research_output_dir": self.config.research_output_dir,
                "quality_output_dir": self.config.quality_output_dir,
                "max_retries": self.config.max_retries,
                "timeout_per_phase": self.config.timeout_per_phase
            }
        }
        
        try:
            # Check if output directories are accessible
            output_dir = Path(self.config.output_dir)
            if output_dir.exists():
                health_status["output_dir_accessible"] = True
            else:
                health_status["output_dir_accessible"] = False
                health_status["orchestrator_status"] = "warning"
            
            # Test component initialization
            try:
                test_research_team = ResearchTeam(output_dir="temp_test")
                health_status["research_team_available"] = True
            except Exception as e:
                health_status["research_team_available"] = False
                health_status["research_team_error"] = str(e)
                health_status["orchestrator_status"] = "warning"
            
            try:
                test_finalizer = EditorialFinalizer(output_dir="temp_test")
                health_status["editorial_finalizer_available"] = True
            except Exception as e:
                health_status["editorial_finalizer_available"] = False
                health_status["editorial_finalizer_error"] = str(e)
                health_status["orchestrator_status"] = "warning"
            
        except Exception as e:
            health_status["orchestrator_status"] = "error"
            health_status["error"] = str(e)
        
        return health_status


# Convenience function for external use
async def orchestrate_transcript_generation(
    syllabus: dict[str, Any], 
    config: WorkflowConfig | None = None
) -> WorkflowResult:
    """
    Convenience function to orchestrate complete transcript generation.
    
    Args:
        syllabus: Syllabus structure with course and section definitions
        config: Optional workflow configuration
        
    Returns:
        WorkflowResult with execution outcome
    """
    orchestrator = WorkflowOrchestrator(config)
    return await orchestrator.execute_pipeline(syllabus)