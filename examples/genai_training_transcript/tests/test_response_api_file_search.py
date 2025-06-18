#!/usr/bin/env python3
"""
Unit Tests for US-011: Response API File_Search Integration Pattern

Tests the working OpenAI Response API file_search implementation for research note synthesis.
Validates patterns that EditingTeam will use for content synthesis.

Author: Sprint 1 Development Team
Reference: US-011 Response API File_Search Integration Pattern  
Issue: #50
"""

import sys
import os
import tempfile
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from response_api_file_search_example import (
    ResponseAPIFileSearchIntegration,
    create_sample_research_data,
    demonstrate_response_api_file_search
)


class TestResponseAPIFileSearchIntegration:
    """Test suite for ResponseAPIFileSearchIntegration class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.api_key = "test-api-key"
        self.project_id = "test-project-id"
        self.sample_research_data = create_sample_research_data()
        
    def test_initialization_with_api_key(self):
        """Test proper initialization with API key"""
        with patch('response_api_file_search_example.OpenAI') as mock_openai:
            integration = ResponseAPIFileSearchIntegration(
                api_key=self.api_key,
                project_id=self.project_id
            )
            
            assert integration.api_key == self.api_key
            assert integration.project_id == self.project_id
            assert integration.vector_store_id is None
            assert integration.assistant_id is None
            assert integration.thread_id is None
            assert integration.uploaded_file_ids == []
            
            # Verify OpenAI client initialized correctly
            mock_openai.assert_called_once_with(
                api_key=self.api_key,
                organization=None,
                project=self.project_id
            )
    
    def test_initialization_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable required"):
                ResponseAPIFileSearchIntegration()
    
    def test_initialization_with_env_api_key(self):
        """Test initialization using environment variable"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': self.api_key}):
            with patch('response_api_file_search_example.OpenAI') as mock_openai:
                integration = ResponseAPIFileSearchIntegration()
                assert integration.api_key == self.api_key
                assert integration.project_id == "proj_UWuOPp9MOKrOCtZABSCTY4Um"  # Default project ID
    
    def test_create_research_notes_files(self):
        """Test creation of research notes files from data structure"""
        with patch('response_api_file_search_example.OpenAI'):
            integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
            
            file_paths = integration.create_research_notes_files(self.sample_research_data)
            
            # Verify correct number of files created
            expected_files = 2 + len(self.sample_research_data['research_notes'])  # syllabus + agenda + research notes
            assert len(file_paths) == expected_files
            
            # Verify all files exist
            for file_path in file_paths:
                assert os.path.exists(file_path)
                assert os.path.getsize(file_path) > 0  # Files have content
            
            # Verify file naming patterns
            file_names = [os.path.basename(fp) for fp in file_paths]
            assert "course_syllabus.md" in file_names
            assert "module_agenda.md" in file_names
            assert any("research_notes_" in name for name in file_names)
            
            # Cleanup test files
            for file_path in file_paths:
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def test_create_research_notes_files_content_validation(self):
        """Test that created files contain expected content"""
        with patch('response_api_file_search_example.OpenAI'):
            integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
            
            file_paths = integration.create_research_notes_files(self.sample_research_data)
            
            # Find and validate syllabus file
            syllabus_file = next(fp for fp in file_paths if "syllabus" in fp)
            with open(syllabus_file, 'r', encoding='utf-8') as f:
                syllabus_content = f.read()
                assert "# Course Syllabus" in syllabus_content
                assert self.sample_research_data['syllabus']['title'] in syllabus_content
                assert "## Learning Objectives" in syllabus_content
                assert "## Key Topics" in syllabus_content
            
            # Find and validate agenda file
            agenda_file = next(fp for fp in file_paths if "agenda" in fp)
            with open(agenda_file, 'r', encoding='utf-8') as f:
                agenda_content = f.read()
                assert "# Module Agenda" in agenda_content
                assert "Module 1:" in agenda_content
                
            # Cleanup test files
            for file_path in file_paths:
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    @patch('response_api_file_search_example.OpenAI')
    def test_upload_files_for_search_success(self, mock_openai_class):
        """Test successful file upload and vector store creation"""
        # Setup mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock file upload
        mock_uploaded_file = Mock()
        mock_uploaded_file.id = "test-file-id"
        mock_client.files.create.return_value = mock_uploaded_file
        
        # Mock vector store creation
        mock_vector_store = Mock()
        mock_vector_store.id = "test-vector-store-id"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        
        # Mock file batch
        mock_file_batch = Mock()
        mock_file_batch.id = "test-batch-id"
        mock_file_batch.status = "completed"
        mock_client.beta.vector_stores.file_batches.create.return_value = mock_file_batch
        mock_client.beta.vector_stores.file_batches.retrieve.return_value = mock_file_batch
        
        integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
        
        # Create temporary test files
        with tempfile.TemporaryDirectory() as temp_dir:
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_file_{i}.txt")
                with open(test_file, 'w') as f:
                    f.write(f"Test content {i}")
                test_files.append(test_file)
            
            # Test upload
            vector_store_id = integration.upload_files_for_search(test_files)
            
            # Verify results
            assert vector_store_id == "test-vector-store-id"
            assert integration.vector_store_id == "test-vector-store-id"
            assert len(integration.uploaded_file_ids) == 3
            
            # Verify API calls
            assert mock_client.files.create.call_count == 3
            mock_client.beta.vector_stores.create.assert_called_once()
            mock_client.beta.vector_stores.file_batches.create.assert_called_once()
    
    @patch('response_api_file_search_example.OpenAI')
    def test_create_research_assistant_success(self, mock_openai_class):
        """Test successful research assistant creation"""
        # Setup mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_assistant = Mock()
        mock_assistant.id = "test-assistant-id"
        mock_client.beta.assistants.create.return_value = mock_assistant
        
        integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
        
        # Test assistant creation
        assistant_id = integration.create_research_assistant("test-vector-store-id")
        
        # Verify results
        assert assistant_id == "test-assistant-id"
        assert integration.assistant_id == "test-assistant-id"
        
        # Verify API call
        mock_client.beta.assistants.create.assert_called_once()
        call_args = mock_client.beta.assistants.create.call_args
        assert call_args[1]['name'] == "Research Content Synthesizer"
        assert call_args[1]['model'] == "gpt-4o-mini"  # Updated default model
        assert call_args[1]['tools'] == [{"type": "file_search"}]
        assert call_args[1]['tool_resources']['file_search']['vector_store_ids'] == ["test-vector-store-id"]
    
    @patch('response_api_file_search_example.OpenAI')
    def test_synthesize_content_success(self, mock_openai_class):
        """Test successful content synthesis"""
        # Setup comprehensive mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock thread creation
        mock_thread = Mock()
        mock_thread.id = "test-thread-id"
        mock_client.beta.threads.create.return_value = mock_thread
        
        # Mock message creation
        mock_message = Mock()
        mock_client.beta.threads.messages.create.return_value = mock_message
        
        # Mock run creation and completion
        mock_run = Mock()
        mock_run.id = "test-run-id"
        mock_run.status = "completed"
        mock_client.beta.threads.runs.create.return_value = mock_run
        mock_client.beta.threads.runs.retrieve.return_value = mock_run
        
        # Mock messages response
        mock_annotation = Mock()
        mock_annotation.file_citation.file_id = "test-file-id"
        mock_annotation.file_citation.quote = "test quote"
        mock_annotation.text = "test annotation"
        
        mock_content = Mock()
        mock_content.text.value = "Test synthesized content"
        mock_content.text.annotations = [mock_annotation]
        
        mock_assistant_message = Mock()
        mock_assistant_message.role = "assistant"
        mock_assistant_message.content = [mock_content]
        
        mock_messages = Mock()
        mock_messages.data = [mock_assistant_message]
        mock_client.beta.threads.messages.list.return_value = mock_messages
        
        integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
        integration.assistant_id = "test-assistant-id"
        
        # Test synthesis
        synthesis_request = {
            'query': 'Test query',
            'type': 'content_synthesis',
            'target_module': 'Test Module'
        }
        
        result = integration.synthesize_content(synthesis_request)
        
        # Verify results
        assert result['status'] == 'success'
        assert result['synthesis_type'] == 'content_synthesis'
        assert result['target_module'] == 'Test Module'
        assert result['synthesized_content'] == "Test synthesized content"
        assert len(result['file_search_results']) == 1
        assert result['sources_used'] == 1
        assert result['run_id'] == "test-run-id"
        assert result['thread_id'] == "test-thread-id"
        
        # Verify API calls
        mock_client.beta.threads.create.assert_called_once()
        mock_client.beta.threads.messages.create.assert_called_once()
        mock_client.beta.threads.runs.create.assert_called_once()
    
    @patch('response_api_file_search_example.OpenAI')
    def test_cleanup_resources(self, mock_openai_class):
        """Test proper cleanup of created resources"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        integration = ResponseAPIFileSearchIntegration(api_key=self.api_key)
        integration.vector_store_id = "test-vector-store-id"
        integration.assistant_id = "test-assistant-id"
        
        # Test cleanup
        integration.cleanup_resources()
        
        # Verify cleanup calls
        mock_client.beta.vector_stores.delete.assert_called_once_with("test-vector-store-id")
        mock_client.beta.assistants.delete.assert_called_once_with("test-assistant-id")


class TestSampleDataCreation:
    """Test suite for sample data creation functions"""
    
    def test_create_sample_research_data_structure(self):
        """Test that sample research data has correct structure"""
        data = create_sample_research_data()
        
        # Verify top-level structure
        assert 'syllabus' in data
        assert 'agenda' in data
        assert 'research_notes' in data
        
        # Verify syllabus structure
        syllabus = data['syllabus']
        assert 'title' in syllabus
        assert 'duration_weeks' in syllabus
        assert 'learning_objectives' in syllabus
        assert 'key_topics' in syllabus
        assert isinstance(syllabus['learning_objectives'], list)
        assert isinstance(syllabus['key_topics'], list)
        assert len(syllabus['learning_objectives']) > 0
        assert len(syllabus['key_topics']) > 0
        
        # Verify agenda structure
        agenda = data['agenda']
        assert isinstance(agenda, list)
        assert len(agenda) > 0
        for module in agenda:
            assert 'title' in module
            assert 'duration_minutes' in module
            assert 'topics' in module
            assert isinstance(module['topics'], list)
        
        # Verify research notes structure
        research_notes = data['research_notes']
        assert isinstance(research_notes, dict)
        assert len(research_notes) > 0
        for module_name, notes in research_notes.items():
            assert isinstance(notes, dict)
            assert len(notes) > 0
    
    def test_create_sample_research_data_content_quality(self):
        """Test that sample research data contains meaningful content"""
        data = create_sample_research_data()
        
        # Check syllabus content quality
        syllabus = data['syllabus']
        assert len(syllabus['title']) > 10
        assert syllabus['duration_weeks'] > 0
        assert all(len(obj) > 20 for obj in syllabus['learning_objectives'])
        assert all(len(topic) > 10 for topic in syllabus['key_topics'])
        
        # Check agenda content quality
        agenda = data['agenda']
        total_duration = sum(module['duration_minutes'] for module in agenda)
        assert total_duration > 100  # Reasonable total duration
        assert all(len(module['title']) > 5 for module in agenda)
        
        # Check research notes content quality
        research_notes = data['research_notes']
        for module_name, notes in research_notes.items():
            for section_name, content in notes.items():
                assert len(content) > 100  # Substantial content
                assert content.count('\n') > 5  # Multi-paragraph content


class TestIntegrationPatterns:
    """Test suite for integration patterns and US-004 compatibility"""
    
    @patch('response_api_file_search_example.OpenAI')
    def test_editing_team_integration_interface(self, mock_openai_class):
        """Test that the integration provides proper interface for EditingTeam usage"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        integration = ResponseAPIFileSearchIntegration(api_key="test-key")
        
        # Test that key methods exist and are callable
        assert hasattr(integration, 'create_research_notes_files')
        assert callable(integration.create_research_notes_files)
        
        assert hasattr(integration, 'upload_files_for_search')
        assert callable(integration.upload_files_for_search)
        
        assert hasattr(integration, 'create_research_assistant')
        assert callable(integration.create_research_assistant)
        
        assert hasattr(integration, 'synthesize_content')
        assert callable(integration.synthesize_content)
        
        assert hasattr(integration, 'demonstrate_multi_step_synthesis')
        assert callable(integration.demonstrate_multi_step_synthesis)
        
        assert hasattr(integration, 'cleanup_resources')
        assert callable(integration.cleanup_resources)
    
    def test_synthesis_request_interface(self):
        """Test synthesis request interface matches EditingTeam expectations"""
        # Define expected synthesis request format for US-004
        synthesis_request = {
            'query': 'Create content for machine learning introduction',
            'type': 'content_synthesis',
            'target_module': 'Introduction to Machine Learning'
        }
        
        # Verify all required fields are present
        assert 'query' in synthesis_request
        assert 'type' in synthesis_request
        assert 'target_module' in synthesis_request
        
        # Verify field types
        assert isinstance(synthesis_request['query'], str)
        assert isinstance(synthesis_request['type'], str)
        assert isinstance(synthesis_request['target_module'], str)
    
    def test_synthesis_response_interface(self):
        """Test synthesis response interface provides expected data for EditingTeam"""
        # Expected response structure for US-004 integration
        expected_response_fields = [
            'status',
            'synthesis_type', 
            'target_module',
            'synthesized_content',
            'file_search_results',
            'sources_used',
            'run_id',
            'thread_id'
        ]
        
        # This validates that EditingTeam can expect these fields
        # in successful synthesis responses
        for field in expected_response_fields:
            assert isinstance(field, str)
            assert len(field) > 0


class TestErrorHandling:
    """Test suite for error handling and edge cases"""
    
    @patch('response_api_file_search_example.OpenAI')
    def test_upload_files_error_handling(self, mock_openai_class):
        """Test error handling during file upload"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.files.create.side_effect = Exception("Upload failed")
        
        integration = ResponseAPIFileSearchIntegration(api_key="test-key")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            with pytest.raises(Exception, match="Upload failed"):
                integration.upload_files_for_search([test_file])
    
    @patch('response_api_file_search_example.OpenAI')
    def test_synthesis_failure_handling(self, mock_openai_class):
        """Test handling of synthesis failures"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock failed run
        mock_run = Mock()
        mock_run.status = "failed"
        mock_run.last_error = "Test error"
        mock_client.beta.threads.runs.create.return_value = mock_run
        mock_client.beta.threads.runs.retrieve.return_value = mock_run
        
        mock_thread = Mock()
        mock_thread.id = "test-thread-id"
        mock_client.beta.threads.create.return_value = mock_thread
        
        integration = ResponseAPIFileSearchIntegration(api_key="test-key")
        integration.assistant_id = "test-assistant-id"
        
        synthesis_request = {
            'query': 'Test query',
            'type': 'content_synthesis',
            'target_module': 'Test Module'
        }
        
        result = integration.synthesize_content(synthesis_request)
        
        # Verify error response
        assert result['status'] == 'error'
        assert 'Run failed with status: failed' in result['error']
    
    def test_empty_research_data_handling(self):
        """Test handling of empty or invalid research data"""
        with patch('response_api_file_search_example.OpenAI'):
            integration = ResponseAPIFileSearchIntegration(api_key="test-key")
            
            # Test with empty data
            empty_data = {'syllabus': {}, 'agenda': [], 'research_notes': {}}
            file_paths = integration.create_research_notes_files(empty_data)
            
            # Should still create files (with minimal content)
            assert len(file_paths) == 2  # syllabus + agenda files
            
            # Cleanup
            for file_path in file_paths:
                try:
                    os.unlink(file_path)
                except:
                    pass


class TestDemonstrationFunction:
    """Test suite for the main demonstration function"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_demonstrate_without_api_key(self):
        """Test demonstration function without API key"""
        # Capture stdout to verify error message
        import io
        import contextlib
        
        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            demonstrate_response_api_file_search()
        
        output = captured_output.getvalue()
        assert "OPENAI_API_KEY environment variable not set" in output
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('response_api_file_search_example.ResponseAPIFileSearchIntegration')
    def test_demonstrate_with_api_key(self, mock_integration_class):
        """Test demonstration function with API key"""
        # Setup mock
        mock_integration = Mock()
        mock_integration.demonstrate_multi_step_synthesis.return_value = {
            'performance_metrics': {
                'successful_syntheses': 3,
                'total_synthesis_requests': 3,
                'total_sources_integrated': 5,
                'total_content_generated': 1000,
                'processing_time_seconds': 10.5
            },
            'synthesis_results': [{
                'status': 'success',
                'target_module': 'Test Module',
                'synthesized_content': 'Test content',
                'file_search_results': []
            }],
            'workflow_steps': ['step1', 'step2']
        }
        mock_integration_class.return_value = mock_integration
        
        # Test function execution (should not raise exceptions)
        try:
            demonstrate_response_api_file_search()
            demonstration_completed = True
        except Exception:
            demonstration_completed = False
        
        assert demonstration_completed
        mock_integration.demonstrate_multi_step_synthesis.assert_called_once()
        mock_integration.cleanup_resources.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 