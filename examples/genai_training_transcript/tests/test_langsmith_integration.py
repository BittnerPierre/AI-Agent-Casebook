"""
Tests for LangSmith Integration (US-007 and US-012)

Test Coverage:
- EvaluationLogger functionality
- LangSmithIntegration post-execution metadata
- Configuration management and validation
- WorkflowOrchestrator integration
- EditorialFinalizer agent conversation logging

Note: These tests run without requiring actual LangSmith API keys for CI/CD compatibility.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.evaluation import (
    EvaluationLogger,
    LangSmithConfig,
    LangSmithIntegration,
    get_default_config,
    validate_environment,
)
from src.transcript_generator.editorial_finalizer import ChapterDraft
from src.transcript_generator.workflow_orchestrator import WorkflowConfig, WorkflowResult


class TestLangSmithConfig:
    """Test LangSmith configuration management"""
    
    def test_default_config_creation(self):
        """Test creating config with defaults"""
        config = LangSmithConfig()
        
        assert config.project_name == "story-ops"
        assert config.enable_evaluation_logging is True
        assert config.use_kebab_case is True
        assert config.run_name_prefix == "transcript-generation"
    
    def test_config_from_environment(self):
        """Test config creation from environment variables"""
        with patch.dict(os.environ, {
            'LANGSMITH_API_KEY': 'test_key',
            'LANGSMITH_PROJECT': 'test-project',
            'LANGSMITH_AUTO_TRACE': 'false'
        }):
            config = LangSmithConfig.from_environment()
            
            assert config.api_key == 'test_key'
            assert config.project_name == 'test-project'
            assert config.enable_auto_trace is False
    
    def test_is_fully_configured(self):
        """Test configuration validation"""
        # Not configured
        config = LangSmithConfig()
        assert not config.is_fully_configured()
        
        # Fully configured
        config = LangSmithConfig(api_key="test_key", project_name="test-project")
        assert config.is_fully_configured()
    
    def test_get_run_name_kebab_case(self):
        """Test run name generation with kebab-case"""
        config = LangSmithConfig(use_kebab_case=True)
        
        assert config.get_run_name() == "transcript-generation"
        assert config.get_run_name("test_suffix") == "transcript-generation-test-suffix"
        assert config.get_run_name("Test Suffix") == "transcript-generation-test-suffix"
    
    def test_validate_environment(self):
        """Test environment validation"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_environment()
            
            assert result["valid"] is True
            assert result["fully_configured"] is False
            assert len(result["warnings"]) > 0
            assert "LANGSMITH_API_KEY not set" in result["warnings"][0]


class TestEvaluationLogger:
    """Test EvaluationLogger functionality"""
    
    def test_initialization_without_langsmith(self):
        """Test logger initialization when LangSmith is not available"""
        with patch('src.evaluation.langsmith_logger.LANGSMITH_AVAILABLE', False):
            logger = EvaluationLogger(enabled=True)
            
            assert not logger.enabled
            assert logger.client is None
    
    def test_initialization_without_api_key(self):
        """Test logger initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            logger = EvaluationLogger(enabled=True)
            
            assert not logger.enabled
    
    @pytest.mark.asyncio
    async def test_log_workflow_disabled(self):
        """Test workflow logging when disabled"""
        logger = EvaluationLogger(enabled=False)
        
        result = await logger.log_workflow(
            workflow_result=MagicMock(),
            syllabus={"title": "Test Course"},
            execution_metadata={}
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self):
        """Test metrics collection from workflow result"""
        logger = EvaluationLogger(enabled=False)  # Disabled to avoid external calls
        
        # Mock workflow result
        workflow_result = MagicMock()
        workflow_result.success = True
        workflow_result.execution_time = 120.5
        workflow_result.errors = ["test error"]
        workflow_result.research_notes = {"module1": "notes"}
        workflow_result.chapter_drafts = [MagicMock(), MagicMock()]
        workflow_result.quality_metrics = {
            "quality_score": 0.85,
            "critical_issues": 2,
            "recommendations": ["improve clarity"]
        }
        
        syllabus = {
            "title": "Test Course",
            "sections": [{"id": "s1"}, {"id": "s2"}],
            "learning_objectives": ["obj1", "obj2"]
        }
        
        metrics = await logger.collect_metrics(workflow_result, syllabus, {"test": "metadata"})
        
        # Verify metrics structure
        assert "execution_metrics" in metrics
        assert "quality_metrics" in metrics
        assert "agent_conversations" in metrics
        assert "syllabus_analysis" in metrics
        
        # Verify specific values
        assert metrics["execution_metrics"]["success"] is True
        assert metrics["execution_metrics"]["execution_time_seconds"] == 120.5
        assert metrics["quality_metrics"]["overall_quality_score"] == 0.85
        assert metrics["syllabus_analysis"]["section_count"] == 2
    
    def test_log_agent_interaction(self):
        """Test individual agent interaction logging"""
        logger = EvaluationLogger(enabled=False)
        
        # Should not raise exception even when disabled
        logger.log_agent_interaction(
            agent_name="test_agent",
            interaction_type="assessment",
            input_data={"input": "test"},
            output_data={"output": "result"},
            metadata={"meta": "data"}
        )


class TestLangSmithIntegration:
    """Test LangSmithIntegration functionality"""
    
    def test_initialization(self):
        """Test integration initialization"""
        integration = LangSmithIntegration(
            project_name="test-project",
            auto_send_enabled=True
        )
        
        assert integration.project_name == "test-project"
        assert integration.auto_send_enabled is True
        assert integration.evaluation_logger is not None
    
    @pytest.mark.asyncio
    async def test_send_execution_metadata_disabled(self):
        """Test metadata sending when disabled"""
        integration = LangSmithIntegration(auto_send_enabled=False)
        
        result = await integration.send_execution_metadata(
            workflow_result=MagicMock(),
            syllabus={"title": "Test"},
            execution_context={}
        )
        
        assert result is False
    
    def test_configure_agent_sdk_tracing(self):
        """Test Agent SDK tracing configuration"""
        integration = LangSmithIntegration(auto_send_enabled=False)
        
        config = integration.configure_agent_sdk_tracing()
        
        assert config["enabled"] is False
        
        # Test with enabled integration
        integration = LangSmithIntegration(auto_send_enabled=True)
        integration.enabled = True  # Mock as enabled
        
        config = integration.configure_agent_sdk_tracing()
        
        assert config["enabled"] is True
        assert config["project_name"] == "story-ops"
        assert config["kebab_case_naming"] is True
    
    def test_get_integration_status(self):
        """Test integration status reporting"""
        integration = LangSmithIntegration()
        
        status = integration.get_integration_status()
        
        assert "enabled" in status
        assert "project_name" in status
        assert "langsmith_available" in status
        assert "integration_version" in status
    
    @pytest.mark.asyncio
    async def test_send_agent_trace_data(self):
        """Test Agent SDK trace data transmission"""
        integration = LangSmithIntegration(auto_send_enabled=False)
        
        result = await integration.send_agent_trace_data(
            agent_name="test_agent",
            trace_data={"inputs": {"test": "input"}, "outputs": {"test": "output"}},
            parent_run_id="parent_123"
        )
        
        assert result is False  # Disabled
    
    def test_story_ops_project_configuration(self):
        """Test US-012 specific story-ops project configuration"""
        integration = LangSmithIntegration()
        
        # Verify default project name is "story-ops" as specified
        assert integration.project_name == "story-ops"
        
        # Test custom project
        custom_integration = LangSmithIntegration(project_name="custom-project")
        assert custom_integration.project_name == "custom-project"
    
    def test_agent_sdk_tracing_configuration_us012(self):
        """Test US-012 Agent SDK built-in tracing configuration"""
        integration = LangSmithIntegration(auto_send_enabled=True)
        integration.enabled = True  # Mock as enabled
        
        config = integration.configure_agent_sdk_tracing()
        
        # Verify US-012 requirements
        assert config["enabled"] is True
        assert config["project_name"] == "story-ops"
        assert config["kebab_case_naming"] is True
        assert config["auto_trace"] is True
        assert "batch_size" in config
        assert "flush_interval" in config


class TestWorkflowOrchestratorIntegration:
    """Test LangSmith integration with WorkflowOrchestrator"""
    
    def test_workflow_config_langsmith_settings(self):
        """Test WorkflowConfig LangSmith settings"""
        config = WorkflowConfig()
        
        assert hasattr(config, 'enable_langsmith_logging')
        assert hasattr(config, 'langsmith_project_name')
        assert hasattr(config, 'langsmith_auto_send')
        
        assert config.enable_langsmith_logging is True
        assert config.langsmith_project_name == "story-ops"
        assert config.langsmith_auto_send is True
    
    def test_us012_automatic_trace_collection(self):
        """Test US-012 automatic trace collection requirement"""
        # Test that WorkflowConfig enables automatic metadata sending
        config = WorkflowConfig()
        
        # US-012 requires automatic sending after workflow completion
        assert config.langsmith_auto_send is True
        assert config.enable_langsmith_logging is True
        
        # Verify the project setup matches US-012 specs
        assert config.langsmith_project_name == "story-ops"
    
    @patch('src.transcript_generator.workflow_orchestrator.LANGSMITH_INTEGRATION_AVAILABLE', True)
    @patch('src.transcript_generator.workflow_orchestrator.LangSmithIntegration')
    def test_workflow_orchestrator_langsmith_initialization(self, mock_langsmith):
        """Test WorkflowOrchestrator initializes LangSmith integration"""
        from src.transcript_generator.workflow_orchestrator import WorkflowOrchestrator
        
        config = WorkflowConfig(enable_langsmith_logging=True)
        orchestrator = WorkflowOrchestrator(config)
        
        mock_langsmith.assert_called_once()
        assert hasattr(orchestrator, '_langsmith_integration')


class TestEditorialFinalizerIntegration:
    """Test LangSmith integration with EditorialFinalizer"""
    
    def test_editorial_finalizer_langsmith_initialization(self):
        """Test EditorialFinalizer initializes LangSmith logging"""
        with patch('src.transcript_generator.editorial_finalizer_multi_agent.LANGSMITH_EVALUATION_AVAILABLE', True), \
             patch('src.transcript_generator.editorial_finalizer_multi_agent.EvaluationLogger') as mock_logger:
            
            from src.transcript_generator.editorial_finalizer_multi_agent import MultiAgentEditorialFinalizer
            
            finalizer = MultiAgentEditorialFinalizer()
            
            mock_logger.assert_called_once()
            assert hasattr(finalizer, '_evaluation_logger')
    
    def test_log_agent_assessment_to_langsmith(self):
        """Test agent assessment logging to LangSmith"""
        with patch('src.transcript_generator.editorial_finalizer_multi_agent.LANGSMITH_EVALUATION_AVAILABLE', True), \
             patch('src.transcript_generator.editorial_finalizer_multi_agent.EvaluationLogger') as mock_logger_class:
            
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger
            
            from src.transcript_generator.editorial_finalizer_multi_agent import MultiAgentEditorialFinalizer
            
            finalizer = MultiAgentEditorialFinalizer()
            
            # Create test data
            chapter = ChapterDraft(
                section_id="test_section",
                content="Test content for the chapter",
                title="Test Chapter"
            )
            
            agent_assessment = {
                "overall_quality_score": 0.85,
                "consensus_confidence": 0.90,
                "dimension_scores": {"semantic_alignment": 0.8},
                "consolidated_findings": ["finding1"],
                "consolidated_recommendations": ["recommendation1"],
                "agent_assessments": {"agent1": "assessment1"},
                "assessment_metadata": {"timestamp": "2024-01-01"}
            }
            
            syllabus = {"title": "Test Course", "sections": []}
            
            # Call the method
            finalizer._log_agent_assessment_to_langsmith(chapter, agent_assessment, syllabus)
            
            # Verify logger was called
            mock_logger.log_agent_interaction.assert_called_once()
            
            # Verify call parameters
            call_args = mock_logger.log_agent_interaction.call_args
            assert call_args[1]["agent_name"] == "editorial_finalizer_multi_agent"
            assert call_args[1]["interaction_type"] == "quality_assessment"
            assert "chapter_content" in call_args[1]["input_data"]
            assert "overall_quality_score" in call_args[1]["output_data"]


class TestIntegrationWithFallbacks:
    """Test integration behavior with fallbacks and error handling"""
    
    @pytest.mark.asyncio
    async def test_langsmith_unavailable_fallback(self):
        """Test behavior when LangSmith library is unavailable"""
        with patch('src.evaluation.langsmith_logger.LANGSMITH_AVAILABLE', False):
            logger = EvaluationLogger()
            
            # Should handle gracefully
            result = await logger.log_workflow(
                workflow_result=MagicMock(),
                syllabus={},
                execution_metadata={}
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fallback_logging_to_file(self):
        """Test fallback logging to file when LangSmith fails"""
        logger = EvaluationLogger(enabled=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.mkdir'), \
                 patch('builtins.open', create=True) as mock_open:
                
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                # Call fallback method directly
                await logger._save_fallback_log("test_run_id", {"test": "data"})
                
                # Verify file was written
                mock_open.assert_called_once()
                assert mock_file.write.call_count > 0  # json.dump makes multiple write calls


@pytest.fixture
def sample_workflow_result():
    """Sample WorkflowResult for testing"""
    return WorkflowResult(
        success=True,
        final_transcript_path="/test/path/transcript.md",
        quality_summary_path="/test/path/quality.json",
        research_notes={"module1": "research content"},
        chapter_drafts=[
            ChapterDraft(section_id="s1", content="content1"),
            ChapterDraft(section_id="s2", content="content2")
        ],
        execution_time=95.7,
        errors=None,
        quality_metrics={
            "quality_score": 0.88,
            "critical_issues": 1,
            "warning_issues": 3,
            "recommendations": ["improve clarity", "add examples"]
        }
    )


@pytest.fixture  
def sample_syllabus():
    """Sample syllabus for testing"""
    return {
        "title": "Test AI Course",
        "duration_weeks": 8,
        "difficulty_level": "intermediate",
        "target_audience": "developers",
        "sections": [
            {"id": "s1", "title": "Introduction"},
            {"id": "s2", "title": "Advanced Topics"}
        ],
        "learning_objectives": [
            "Understand AI fundamentals",
            "Apply ML techniques"
        ],
        "key_topics": [
            "neural networks",
            "deep learning",
            "natural language processing"
        ]
    }


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_logging(self, sample_workflow_result, sample_syllabus):
        """Test complete workflow logging end-to-end"""
        # Test with mocked LangSmith
        with patch('src.evaluation.langsmith_logger.LANGSMITH_AVAILABLE', True), \
             patch('src.evaluation.langsmith_logger.LangSmithClient') as mock_client_class:
            
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock create_run to return a run object
            mock_run = MagicMock()
            mock_run.id = "test_run_123"
            mock_client.create_run.return_value = mock_run
            
            logger = EvaluationLogger(api_key="test_key", enabled=True)
            
            # Should complete without error
            run_id = await logger.log_workflow(
                workflow_result=sample_workflow_result,
                syllabus=sample_syllabus,
                execution_metadata={"test": "metadata"}
            )
            
            assert run_id is not None
            
            # Verify create_run was called
            mock_client.create_run.assert_called_once()
    
    def test_configuration_validation_comprehensive(self):
        """Test comprehensive configuration validation"""
        # Test with various environment configurations
        test_cases = [
            ({}, False, True),  # No config - valid but not fully configured
            ({"LANGSMITH_API_KEY": "test"}, True, True),  # Basic config - valid and configured
            ({"LANGSMITH_API_KEY": "", "LANGSMITH_PROJECT": "test"}, False, True),  # Empty key - valid but not configured
        ]
        
        for env_vars, should_be_configured, should_be_valid in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                result = validate_environment()
                config = get_default_config()
                
                assert config.is_fully_configured() == should_be_configured
                assert result["valid"] == should_be_valid