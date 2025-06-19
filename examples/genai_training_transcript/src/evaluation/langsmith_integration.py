"""
LangSmith Post-Execution Metadata Integration (US-012)

This module implements automatic sending of execution metadata to LangSmith
after workflow completion, providing comprehensive post-execution analysis capabilities.

Key Features:
- Automatic post-execution metadata transmission
- Integration with Agent SDK built-in tracing
- Kebab-case naming convention for LangSmith project
- Rich metadata structuring for analysis
- Error handling and retry logic

Integration Points:
- WorkflowOrchestrator: Automatic calls after pipeline completion
- EvaluationLogger: Metadata enhancement and structuring
- Agent SDK: Built-in tracing integration

Author: Claude Code - Sprint 1 Week 3  
Reference: US-012 LangSmith Post-Execution Metadata Integration
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LangSmithClient = None
    LANGSMITH_AVAILABLE = False

from .langsmith_logger import EvaluationLogger

logger = logging.getLogger(__name__)


class LangSmithIntegration:
    """
    LangSmith Post-Execution Metadata Integration for automatic workflow analysis.
    
    Provides seamless integration with LangSmith for post-execution metadata transmission,
    enabling comprehensive analysis and evaluation of workflow performance.
    """
    
    def __init__(self, 
                 project_name: str = "story-ops",
                 api_key: str | None = None,
                 auto_send_enabled: bool = True,
                 retry_attempts: int = 3):
        """
        Initialize LangSmithIntegration with configuration.
        
        Args:
            project_name: LangSmith project name (kebab-case as specified)
            api_key: LangSmith API key (uses LANGSMITH_API_KEY env var if not provided)
            auto_send_enabled: Whether to automatically send metadata after execution
            retry_attempts: Number of retry attempts for failed transmissions
        """
        self.project_name = project_name
        self.auto_send_enabled = auto_send_enabled
        self.retry_attempts = retry_attempts
        self.enabled = auto_send_enabled and LANGSMITH_AVAILABLE
        
        # Initialize evaluation logger for metadata handling
        self.evaluation_logger = EvaluationLogger(
            project_name=project_name,
            api_key=api_key,
            enabled=self.enabled
        )
        
        logger.info(f"LangSmith integration initialized (enabled: {self.enabled}, project: {self.project_name})")
    
    async def send_execution_metadata(self, 
                                    workflow_result: Any,
                                    syllabus: dict[str, Any],
                                    execution_context: dict[str, Any] | None = None) -> bool:
        """
        Send execution metadata to LangSmith for post-execution analysis.
        
        Main interface method for US-012: automatically sends comprehensive
        execution metadata to LangSmith after workflow completion.
        
        Args:
            workflow_result: Complete WorkflowResult from pipeline execution
            syllabus: Original syllabus used for generation
            execution_context: Additional execution context and environment data
            
        Returns:
            True if metadata sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("LangSmith integration disabled, skipping metadata transmission")
            return False
        
        logger.info("Sending execution metadata to LangSmith for post-execution analysis")
        
        try:
            # Enhance metadata with execution context
            enhanced_metadata = await self._enhance_execution_metadata(
                workflow_result, syllabus, execution_context
            )
            
            # Send to LangSmith with retry logic
            success = await self._send_with_retry(workflow_result, syllabus, enhanced_metadata)
            
            if success:
                logger.info("Execution metadata successfully sent to LangSmith")
            else:
                logger.warning("Failed to send execution metadata to LangSmith after retries")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send execution metadata: {e}")
            return False
    
    async def _enhance_execution_metadata(self, 
                                        workflow_result: Any,
                                        syllabus: dict[str, Any],
                                        execution_context: dict[str, Any] | None) -> dict[str, Any]:
        """Enhance execution metadata with additional context for analysis"""
        base_context = execution_context or {}
        
        # Add system and environment metadata
        enhanced_metadata = {
            **base_context,
            "system_metadata": {
                "python_version": os.sys.version,
                "langsmith_integration_version": "1.0.0",
                "execution_timestamp": datetime.now().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "git_commit": os.getenv("GIT_COMMIT", "unknown"),
                "deployment_version": os.getenv("VERSION", "unknown")
            },
            "workflow_metadata": {
                "pipeline_type": "transcript-generation",
                "execution_mode": base_context.get("execution_mode", "standard"),
                "retry_enabled": base_context.get("retry_enabled", True),
                "continue_on_errors": base_context.get("continue_on_errors", True),
                "timeout_configured": base_context.get("timeout_per_phase", 300)
            },
            "analysis_metadata": {
                "post_execution_timestamp": datetime.now().isoformat(),
                "analysis_requested": True,
                "metadata_version": "v1.0",
                "integration_source": "WorkflowOrchestrator"
            }
        }
        
        # Add resource utilization if available
        if "resource_usage" in base_context:
            enhanced_metadata["resource_utilization"] = base_context["resource_usage"]
        
        return enhanced_metadata
    
    async def _send_with_retry(self, 
                             workflow_result: Any,
                             syllabus: dict[str, Any],
                             metadata: dict[str, Any]) -> bool:
        """Send metadata with retry logic for reliability"""
        for attempt in range(self.retry_attempts):
            try:
                # Use EvaluationLogger to handle the actual transmission
                run_id = await self.evaluation_logger.log_workflow(
                    workflow_result=workflow_result,
                    syllabus=syllabus,
                    execution_metadata=metadata
                )
                
                if run_id:
                    logger.debug(f"Metadata sent successfully on attempt {attempt + 1} (run_id: {run_id})")
                    return True
                else:
                    logger.warning(f"Metadata transmission returned no run_id on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Metadata transmission attempt {attempt + 1} failed: {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"All {self.retry_attempts} metadata transmission attempts failed")
        return False
    
    def configure_agent_sdk_tracing(self) -> dict[str, Any]:
        """
        Configure Agent SDK built-in tracing for LangSmith integration.
        
        Sets up automatic tracing configuration for agents to integrate
        seamlessly with LangSmith's tracing capabilities.
        
        Returns:
            Configuration dictionary for Agent SDK tracing
        """
        if not self.enabled:
            return {"enabled": False}
        
        tracing_config = {
            "enabled": True,
            "project_name": self.project_name,
            "auto_trace": True,
            "trace_level": "detailed",
            "include_inputs": True,
            "include_outputs": True,
            "include_metadata": True,
            "kebab_case_naming": True,  # As specified in requirements
            "batch_size": 10,
            "flush_interval": 30  # seconds
        }
        
        logger.info("Agent SDK tracing configured for LangSmith integration")
        return tracing_config
    
    async def send_agent_trace_data(self, 
                                  agent_name: str,
                                  trace_data: dict[str, Any],
                                  parent_run_id: str | None = None) -> bool:
        """
        Send individual agent trace data to LangSmith.
        
        Provides capability to send detailed agent-level tracing data
        for fine-grained conversation analysis.
        
        Args:
            agent_name: Name of the agent generating the trace
            trace_data: Detailed trace data from agent execution
            parent_run_id: Parent workflow run ID for trace correlation
            
        Returns:
            True if trace data sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Structure agent trace for LangSmith
            structured_trace = {
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "parent_run_id": parent_run_id,
                "trace_data": trace_data,
                "project": self.project_name
            }
            
            # Use evaluation logger for consistent formatting
            self.evaluation_logger.log_agent_interaction(
                agent_name=agent_name,
                interaction_type="trace",
                input_data=trace_data.get("inputs", {}),
                output_data=trace_data.get("outputs", {}),
                metadata=structured_trace
            )
            
            logger.debug(f"Agent trace data sent for {agent_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send agent trace data for {agent_name}: {e}")
            return False
    
    def get_integration_status(self) -> dict[str, Any]:
        """
        Get current status of LangSmith integration.
        
        Returns:
            Status information for monitoring and debugging
        """
        return {
            "enabled": self.enabled,
            "langsmith_available": LANGSMITH_AVAILABLE,
            "project_name": self.project_name,
            "auto_send_enabled": self.auto_send_enabled,
            "retry_attempts": self.retry_attempts,
            "evaluation_logger_enabled": self.evaluation_logger.enabled if self.evaluation_logger else False,
            "api_key_configured": bool(os.getenv("LANGSMITH_API_KEY")),
            "integration_version": "1.0.0"
        }