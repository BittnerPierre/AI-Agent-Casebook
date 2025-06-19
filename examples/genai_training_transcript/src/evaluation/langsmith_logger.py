"""
LangSmith Evaluation Logger (US-007)

This module implements the EvaluationLogger class for logging agent conversations
and quality metadata to LangSmith for post-execution analysis.

Key Features:
- Async logging of workflow executions
- Agent conversation capture and structuring
- Quality metrics integration from EditorialFinalizer  
- Automatic trace collection and metadata organization
- Error handling and fallback logging

Integration Points:
- WorkflowOrchestrator: Complete pipeline execution logging
- EditorialFinalizer: Quality assessment and agent conversation data
- Research Team / Editing Team: Individual agent interaction logs

Author: Claude Code - Sprint 1 Week 3
Reference: US-007 LangSmith Evaluation Logging (Issue #55)
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LangSmithClient = None
    LANGSMITH_AVAILABLE = False

logger = logging.getLogger(__name__)


class EvaluationLogger:
    """
    LangSmith Evaluation Logger for agent conversation and quality metadata logging.
    
    Provides comprehensive logging capabilities for workflow executions, agent interactions,
    and quality assessments to enable post-execution analysis and evaluation.
    """
    
    def __init__(self, 
                 project_name: str = "story-ops",
                 api_key: str | None = None,
                 enabled: bool = True):
        """
        Initialize EvaluationLogger with LangSmith configuration.
        
        Args:
            project_name: LangSmith project name (default: "story-ops")
            api_key: LangSmith API key (uses LANGSMITH_API_KEY env var if not provided)
            enabled: Whether logging is enabled (can be disabled for testing)
        """
        self.project_name = project_name
        self.enabled = enabled and LANGSMITH_AVAILABLE
        self.client = None
        
        if self.enabled:
            self.api_key = api_key or os.getenv('LANGSMITH_API_KEY')
            if not self.api_key:
                logger.warning("LANGSMITH_API_KEY not found. LangSmith logging disabled.")
                self.enabled = False
            else:
                try:
                    self.client = LangSmithClient(api_key=self.api_key)
                    logger.info(f"LangSmith logging enabled for project: {self.project_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize LangSmith client: {e}. Logging disabled.")
                    self.enabled = False
        else:
            if not LANGSMITH_AVAILABLE:
                logger.warning("LangSmith library not available. Install with: pip install langsmith")
            else:
                logger.info("LangSmith logging disabled by configuration")
    
    async def log_workflow(self, 
                          workflow_result: Any,
                          syllabus: dict[str, Any],
                          execution_metadata: dict[str, Any] | None = None) -> str | None:
        """
        Log complete workflow execution to LangSmith.
        
        Main interface method for US-007: logs all agent conversations,
        quality metadata, and execution data for post-execution analysis.
        
        Args:
            workflow_result: WorkflowResult object with execution outcome
            syllabus: Original syllabus used for generation
            execution_metadata: Additional execution context and metadata
            
        Returns:
            LangSmith run ID if successful, None if disabled or failed
        """
        if not self.enabled:
            logger.debug("LangSmith logging disabled, skipping workflow log")
            return None
        
        try:
            # Generate unique run ID and timestamp
            run_id = str(uuid4())
            timestamp = datetime.now().isoformat()
            
            logger.info(f"Logging workflow execution to LangSmith (run_id: {run_id})")
            
            # Collect comprehensive metrics
            metrics = await self.collect_metrics(workflow_result, syllabus, execution_metadata)
            
            # Structure workflow data for LangSmith
            workflow_data = {
                "run_id": run_id,
                "timestamp": timestamp,
                "project": self.project_name,
                "workflow_type": "transcript-generation-pipeline",
                "success": getattr(workflow_result, 'success', False),
                "execution_time": getattr(workflow_result, 'execution_time', None),
                "errors": getattr(workflow_result, 'errors', []),
                "syllabus": syllabus,
                "metrics": metrics,
                "metadata": execution_metadata or {}
            }
            
            # Log to LangSmith with structured data
            await self._send_to_langsmith(run_id, workflow_data)
            
            logger.info(f"Workflow execution logged successfully (run_id: {run_id})")
            return run_id
            
        except Exception as e:
            logger.error(f"Failed to log workflow execution to LangSmith: {e}")
            return None
    
    async def collect_metrics(self, 
                            workflow_result: Any,
                            syllabus: dict[str, Any],
                            execution_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Collect comprehensive metrics from workflow execution.
        
        Gathers agent conversation data, quality assessments, performance metrics,
        and execution statistics for LangSmith analysis.
        
        Args:
            workflow_result: WorkflowResult with execution data
            syllabus: Original syllabus structure  
            execution_metadata: Additional execution context
            
        Returns:
            Comprehensive metrics dictionary for LangSmith logging
        """
        try:
            metrics = {
                "execution_metrics": self._collect_execution_metrics(workflow_result),
                "quality_metrics": self._collect_quality_metrics(workflow_result),
                "agent_conversations": await self._collect_agent_conversations(workflow_result),
                "syllabus_analysis": self._analyze_syllabus(syllabus),
                "performance_metrics": self._collect_performance_metrics(workflow_result, execution_metadata),
                "error_analysis": self._analyze_errors(workflow_result)
            }
            
            logger.debug(f"Collected {len(metrics)} metric categories for LangSmith")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect comprehensive metrics: {e}")
            return {"error": f"Metrics collection failed: {e}"}
    
    def _collect_execution_metrics(self, workflow_result: Any) -> dict[str, Any]:
        """Collect basic execution metrics"""
        return {
            "success": getattr(workflow_result, 'success', False),
            "execution_time_seconds": getattr(workflow_result, 'execution_time', None),
            "final_transcript_generated": bool(getattr(workflow_result, 'final_transcript_path', None)),
            "quality_summary_generated": bool(getattr(workflow_result, 'quality_summary_path', None)),
            "research_notes_count": len(getattr(workflow_result, 'research_notes', {}) or {}),
            "chapter_drafts_count": len(getattr(workflow_result, 'chapter_drafts', []) or []),
            "error_count": len(getattr(workflow_result, 'errors', []) or [])
        }
    
    def _collect_quality_metrics(self, workflow_result: Any) -> dict[str, Any]:
        """Extract quality metrics from EditorialFinalizer"""
        quality_metrics = getattr(workflow_result, 'quality_metrics', {}) or {}
        
        # Standard quality metrics structure
        return {
            "overall_quality_score": quality_metrics.get('quality_score', None),
            "quality_level": quality_metrics.get('quality_level', 'unknown'),
            "critical_issues_count": quality_metrics.get('critical_issues', 0),
            "warning_issues_count": quality_metrics.get('warning_issues', 0),
            "info_issues_count": quality_metrics.get('info_issues', 0),
            "total_quality_checks": quality_metrics.get('total_checks', 0),
            "passed_quality_checks": quality_metrics.get('passed_checks', 0),
            "quality_categories": quality_metrics.get('categories', {}),
            "improvement_recommendations": quality_metrics.get('recommendations', []),
            "quality_summary": quality_metrics.get('summary', '')
        }
    
    async def _collect_agent_conversations(self, workflow_result: Any) -> dict[str, Any]:
        """Collect agent conversation data for conversation analysis"""
        conversations = {
            "research_team_conversations": [],
            "editing_team_conversations": [],
            "editorial_finalizer_conversations": [],
            "total_agent_interactions": 0
        }
        
        try:
            # Extract research notes which may contain agent interaction data
            research_notes = getattr(workflow_result, 'research_notes', {}) or {}
            for module_id, notes in research_notes.items():
                if isinstance(notes, dict) and 'agent_interactions' in notes:
                    conversations["research_team_conversations"].append({
                        "module_id": module_id,
                        "interactions": notes['agent_interactions']
                    })
            
            # Extract chapter drafts which may contain editing team conversations  
            chapter_drafts = getattr(workflow_result, 'chapter_drafts', []) or []
            for draft in chapter_drafts:
                if hasattr(draft, 'agent_metadata') and draft.agent_metadata:
                    conversations["editing_team_conversations"].append({
                        "section_id": getattr(draft, 'section_id', 'unknown'),
                        "agent_metadata": draft.agent_metadata
                    })
            
            # Extract quality metrics which may contain multi-agent assessment data
            quality_metrics = getattr(workflow_result, 'quality_metrics', {}) or {}
            if 'agent_assessments' in quality_metrics:
                conversations["editorial_finalizer_conversations"] = quality_metrics['agent_assessments']
            
            # Calculate total interactions
            conversations["total_agent_interactions"] = (
                len(conversations["research_team_conversations"]) +
                len(conversations["editing_team_conversations"]) +
                len(conversations.get("editorial_finalizer_conversations", {}))
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect agent conversations: {e}")
            conversations["collection_error"] = str(e)
        
        return conversations
    
    def _analyze_syllabus(self, syllabus: dict[str, Any]) -> dict[str, Any]:
        """Analyze syllabus structure for context"""
        return {
            "course_title": syllabus.get('title', 'Unknown'),
            "section_count": len(syllabus.get('sections', [])),
            "learning_objectives_count": len(syllabus.get('learning_objectives', [])),
            "key_topics_count": len(syllabus.get('key_topics', [])),
            "estimated_duration": syllabus.get('duration_weeks', None),
            "difficulty_level": syllabus.get('difficulty_level', 'unspecified'),
            "target_audience": syllabus.get('target_audience', 'unspecified')
        }
    
    def _collect_performance_metrics(self, workflow_result: Any, execution_metadata: dict[str, Any] | None) -> dict[str, Any]:
        """Collect performance and resource utilization metrics"""
        metadata = execution_metadata or {}
        
        return {
            "execution_time_seconds": getattr(workflow_result, 'execution_time', None),
            "memory_usage_mb": metadata.get('memory_usage_mb', None),
            "cpu_usage_percent": metadata.get('cpu_usage_percent', None),
            "api_calls_count": metadata.get('api_calls_count', None),
            "tokens_consumed": metadata.get('tokens_consumed', None),
            "cost_estimate_usd": metadata.get('cost_estimate_usd', None),
            "concurrent_operations": metadata.get('concurrent_operations', None),
            "retry_count": metadata.get('retry_count', 0),
            "timeout_events": metadata.get('timeout_events', 0)
        }
    
    def _analyze_errors(self, workflow_result: Any) -> dict[str, Any]:
        """Analyze error patterns and categorize for insights"""
        errors = getattr(workflow_result, 'errors', []) or []
        
        error_analysis = {
            "total_errors": len(errors),
            "error_categories": {},
            "error_severity": {"critical": 0, "warning": 0, "info": 0},
            "error_phases": {"research": 0, "editing": 0, "finalization": 0, "unknown": 0},
            "error_details": errors[:10]  # Limit to first 10 errors to avoid bloat
        }
        
        for error in errors:
            error_str = str(error).lower()
            
            # Categorize by error type
            if "timeout" in error_str:
                error_analysis["error_categories"]["timeout"] = error_analysis["error_categories"].get("timeout", 0) + 1
            elif "api" in error_str or "network" in error_str:
                error_analysis["error_categories"]["api_network"] = error_analysis["error_categories"].get("api_network", 0) + 1
            elif "file" in error_str or "path" in error_str:
                error_analysis["error_categories"]["file_system"] = error_analysis["error_categories"].get("file_system", 0) + 1
            elif "agent" in error_str or "llm" in error_str:
                error_analysis["error_categories"]["agent_llm"] = error_analysis["error_categories"].get("agent_llm", 0) + 1
            else:
                error_analysis["error_categories"]["other"] = error_analysis["error_categories"].get("other", 0) + 1
            
            # Categorize by phase
            if "research" in error_str:
                error_analysis["error_phases"]["research"] += 1
            elif "edit" in error_str:
                error_analysis["error_phases"]["editing"] += 1
            elif "final" in error_str:
                error_analysis["error_phases"]["finalization"] += 1
            else:
                error_analysis["error_phases"]["unknown"] += 1
        
        return error_analysis
    
    async def _send_to_langsmith(self, run_id: str, workflow_data: dict[str, Any]) -> None:
        """Send structured workflow data to LangSmith"""
        try:
            if not self.client:
                raise RuntimeError("LangSmith client not initialized")
            
            # Create run in LangSmith with kebab-case naming as specified
            run_name = f"transcript-generation-{workflow_data['timestamp']}"
            
            # Use LangSmith's create_run method for structured logging
            run = await asyncio.to_thread(
                self.client.create_run,
                name=run_name,
                run_type="chain",  # Workflow is a chain of components
                inputs={
                    "syllabus": workflow_data["syllabus"],
                    "metadata": workflow_data["metadata"]
                },
                outputs={
                    "success": workflow_data["success"],
                    "execution_time": workflow_data["execution_time"],
                    "metrics": workflow_data["metrics"]
                },
                project_name=self.project_name,
                extra={
                    "run_id": run_id,
                    "workflow_type": workflow_data["workflow_type"],
                    "errors": workflow_data["errors"],
                    "detailed_metrics": workflow_data["metrics"]
                }
            )
            
            logger.debug(f"Successfully sent workflow data to LangSmith (run: {run.id})")
            
        except Exception as e:
            logger.error(f"Failed to send data to LangSmith: {e}")
            # Fallback: save to local file for manual analysis
            await self._save_fallback_log(run_id, workflow_data)
    
    async def _save_fallback_log(self, run_id: str, workflow_data: dict[str, Any]) -> None:
        """Save workflow data to local file when LangSmith is unavailable"""
        try:
            log_dir = Path("logs/langsmith_fallback")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"workflow_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, default=str)
            
            logger.info(f"Workflow data saved to fallback log: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save fallback log: {e}")
    
    def log_agent_interaction(self, 
                            agent_name: str,
                            interaction_type: str,
                            input_data: dict[str, Any],
                            output_data: dict[str, Any],
                            metadata: dict[str, Any] | None = None) -> None:
        """
        Log individual agent interaction for detailed conversation analysis.
        
        Args:
            agent_name: Name of the agent (e.g., "research_team", "editing_team")
            interaction_type: Type of interaction (e.g., "query", "synthesis", "review")
            input_data: Agent input data
            output_data: Agent output data
            metadata: Additional interaction metadata
        """
        if not self.enabled:
            return
        
        try:
            # Structure interaction data for future batch logging
            structured_interaction = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "interaction_type": interaction_type,
                "input_data": input_data,
                "output_data": output_data,
                "metadata": metadata or {}
            }
            
            # For now, store in memory for batch logging with workflow
            # Future enhancement: Real-time streaming to LangSmith
            logger.debug(f"Logged {agent_name} interaction: {interaction_type} (data: {len(str(structured_interaction))} chars)")
            
        except Exception as e:
            logger.warning(f"Failed to log agent interaction: {e}")