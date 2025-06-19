"""
Test suite for EditingTeam implementation (US-004)

Tests the EditingTeam class synthesize_chapter method and Response API integration.
Validates multi-step content synthesis and agent feedback loops.
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from transcript_generator.tools.editing_team import EditingTeam, ChapterDraft, SynthesisRequest, edit_chapters


class TestEditingTeamInitialization:
    """Test EditingTeam initialization and configuration"""
    
    def test_initialization_with_api_key(self):
        """Test EditingTeam initialization with API key"""
        with patch('transcript_generator.tools.editing_team.OpenAI') as mock_openai:
            editing_team = EditingTeam(api_key="test-key")
            
            assert editing_team.api_key == "test-key"
            assert editing_team.project_id == "proj_UWuOPp9MOKrOCtZABSCTY4Um"
            assert editing_team.model == "gpt-4o-mini"
            assert editing_team.max_revisions == 2
            mock_openai.assert_called_once()
    
    def test_initialization_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable required"):
                EditingTeam()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'env-test-key'})
    def test_initialization_with_env_api_key(self):
        """Test EditingTeam initialization with environment variable API key"""
        with patch('transcript_generator.tools.editing_team.OpenAI'):
            editing_team = EditingTeam()
            assert editing_team.api_key == 'env-test-key'
    
    def test_custom_configuration(self):
        """Test EditingTeam with custom configuration"""
        with patch('transcript_generator.tools.editing_team.OpenAI'):
            editing_team = EditingTeam(
                api_key="test-key",
                project_id="custom-project",
                model="gpt-4",
                max_revisions=5,
                poll_interval_secs=2.0,
                expires_after_days=7
            )
            
            assert editing_team.project_id == "custom-project"
            assert editing_team.model == "gpt-4"
            assert editing_team.max_revisions == 5
            assert editing_team.poll_interval_secs == 2.0
            assert editing_team.expires_after_days == 7


class TestChapterDraftDataClass:
    """Test ChapterDraft data structure"""
    
    def test_chapter_draft_creation(self):
        """Test ChapterDraft creation and attributes"""
        draft = ChapterDraft(
            section_id="test_section",
            content="Test content for the chapter"
        )
        
        assert draft.section_id == "test_section"
        assert draft.content == "Test content for the chapter"
    
    def test_chapter_draft_to_dict(self):
        """Test ChapterDraft serialization to dict"""
        draft = ChapterDraft(
            section_id="intro_ml",
            content="Introduction to Machine Learning content"
        )
        
        result = draft.to_dict()
        expected = {
            "section_id": "intro_ml",
            "content": "Introduction to Machine Learning content"
        }
        
        assert result == expected
        assert isinstance(result, dict)


class TestSynthesisRequestDataClass:
    """Test SynthesisRequest data structure"""
    
    def test_synthesis_request_creation(self):
        """Test SynthesisRequest creation and attributes"""
        request = SynthesisRequest(
            query="Create content for ML introduction",
            type="content_synthesis",
            target_module="Introduction to ML"
        )
        
        assert request.query == "Create content for ML introduction"
        assert request.type == "content_synthesis"
        assert request.target_module == "Introduction to ML"
    
    def test_synthesis_request_to_dict(self):
        """Test SynthesisRequest serialization to dict"""
        request = SynthesisRequest(
            query="Test query",
            type="module_overview", 
            target_module="Test Module"
        )
        
        result = request.to_dict()
        expected = {
            "query": "Test query",
            "type": "module_overview",
            "target_module": "Test Module"
        }
        
        assert result == expected


class TestEditingTeamSynthesizeChapter:
    """Test the main synthesize_chapter method"""
    
    def setup_method(self):
        """Setup test data"""
        self.sample_research_notes = {
            'target_section': 'Introduction to Machine Learning',
            'syllabus': {
                'title': 'Advanced ML Course',
                'duration_weeks': 12,
                'learning_objectives': [
                    'Understand ML fundamentals',
                    'Apply supervised learning algorithms',
                    'Evaluate model performance'
                ],
                'key_topics': ['Regression', 'Classification', 'Model Evaluation']
            },
            'agenda': [
                {
                    'title': 'Introduction to Machine Learning',
                    'duration_minutes': 90,
                    'topics': ['ML Overview', 'Types of ML', 'Applications']
                }
            ],
            'research_notes': {
                'Introduction to Machine Learning': {
                    'fundamentals': 'ML is a subset of AI that focuses on algorithms that learn from data',
                    'applications': 'Used in recommendation systems, image recognition, NLP'
                }
            }
        }
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_synthesize_chapter_interface(self, mock_openai_class):
        """Test that synthesize_chapter method has correct interface"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        # Mock the internal methods to avoid actual API calls
        editing_team._create_research_files = Mock(return_value=["/tmp/test.md"])
        editing_team._upload_files_for_search = Mock(return_value="vector_store_123")
        editing_team._create_research_assistant = Mock(return_value="assistant_123")
        editing_team._execute_synthesis_workflow = Mock(return_value="Generated content")
        editing_team._cleanup_resources = Mock()
        
        result = editing_team.synthesize_chapter(self.sample_research_notes)
        
        # Verify result type and structure
        assert isinstance(result, ChapterDraft)
        assert result.section_id == 'Introduction to Machine Learning'
        assert result.content == "Generated content"
        
        # Verify method calls
        editing_team._create_research_files.assert_called_once_with(self.sample_research_notes)
        editing_team._upload_files_for_search.assert_called_once_with(["/tmp/test.md"])
        editing_team._create_research_assistant.assert_called_once_with("vector_store_123")
        editing_team._execute_synthesis_workflow.assert_called_once_with(self.sample_research_notes, "assistant_123")
        editing_team._cleanup_resources.assert_called_once()
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_synthesize_chapter_error_handling(self, mock_openai_class):
        """Test error handling in synthesize_chapter method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        # Mock a failure in file creation
        editing_team._create_research_files = Mock(side_effect=Exception("File creation failed"))
        editing_team._cleanup_resources = Mock()
        
        result = editing_team.synthesize_chapter(self.sample_research_notes)
        
        # Should return error chapter draft
        assert isinstance(result, ChapterDraft)
        assert result.section_id == 'Introduction to Machine Learning'
        assert "Error: Unable to synthesize content" in result.content
        assert "File creation failed" in result.content
        
        # Cleanup should still be called
        editing_team._cleanup_resources.assert_called_once()
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_synthesize_chapter_missing_target_section(self, mock_openai_class):
        """Test synthesize_chapter with missing target_section"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        # Mock successful internal methods
        editing_team._create_research_files = Mock(return_value=["/tmp/test.md"])
        editing_team._upload_files_for_search = Mock(return_value="vector_store_123")
        editing_team._create_research_assistant = Mock(return_value="assistant_123")
        editing_team._execute_synthesis_workflow = Mock(return_value="Generated content")
        editing_team._cleanup_resources = Mock()
        
        # Research notes without target_section
        research_notes = dict(self.sample_research_notes)
        del research_notes['target_section']
        
        result = editing_team.synthesize_chapter(research_notes)
        
        assert result.section_id == 'Unknown Section'
        assert result.content == "Generated content"


class TestEditingTeamInternalMethods:
    """Test internal helper methods of EditingTeam"""
    
    def setup_method(self):
        """Setup test data"""
        self.sample_research_notes = {
            'target_section': 'Test Section',
            'syllabus': {
                'title': 'Test Course',
                'duration_weeks': 8,
                'learning_objectives': ['Learn basics', 'Apply knowledge'],
                'key_topics': ['Topic 1', 'Topic 2']
            },
            'agenda': [
                {
                    'title': 'Test Module',
                    'duration_minutes': 60,
                    'topics': ['Subtopic A', 'Subtopic B']
                }
            ],
            'research_notes': {
                'Test Module': 'Research content for test module'
            }
        }
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_create_research_files(self, mock_openai_class):
        """Test _create_research_files method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        file_paths = editing_team._create_research_files(self.sample_research_notes)
        
        # Should create 4 files: syllabus, agenda, research notes, guidelines
        assert len(file_paths) == 4
        
        # Verify files were created and contain expected content
        for file_path in file_paths:
            assert os.path.exists(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 0
        
        # Check specific file contents
        syllabus_file = next(f for f in file_paths if 'syllabus' in f)
        with open(syllabus_file, 'r', encoding='utf-8') as f:
            syllabus_content = f.read()
            assert 'Test Course' in syllabus_content
            assert 'Learn basics' in syllabus_content
            assert 'Topic 1' in syllabus_content
        
        agenda_file = next(f for f in file_paths if 'agenda' in f)
        with open(agenda_file, 'r', encoding='utf-8') as f:
            agenda_content = f.read()
            assert 'Test Module' in agenda_content
            assert 'Subtopic A' in agenda_content
        
        research_file = next(f for f in file_paths if 'research_notes' in f)
        with open(research_file, 'r', encoding='utf-8') as f:
            research_content = f.read()
            assert 'Research content for test module' in research_content
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_create_documentalist_query(self, mock_openai_class):
        """Test _create_documentalist_query method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        query = editing_team._create_documentalist_query("Test Section", self.sample_research_notes)
        
        assert "Documentalist" in query
        assert "Test Section" in query
        assert "syllabus, agenda, and research notes" in query
        assert "learning objectives" in query
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_create_writer_query(self, mock_openai_class):
        """Test _create_writer_query method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        documented_content = "Sample documented content from documentalist"
        query = editing_team._create_writer_query("Test Section", documented_content, self.sample_research_notes)
        
        assert "Writer" in query
        assert "Test Section" in query
        assert documented_content in query
        assert "training course guidelines" in query
        assert "learning scaffolding" in query
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_create_reviewer_query(self, mock_openai_class):
        """Test _create_reviewer_query method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        draft_content = "Sample draft content from writer"
        query = editing_team._create_reviewer_query("Test Section", draft_content)
        
        assert "Reviewer" in query
        assert "Test Section" in query
        assert draft_content in query
        assert "Pedagogical effectiveness" in query
        assert "Content accuracy" in query
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_create_final_revision_query(self, mock_openai_class):
        """Test _create_final_revision_query method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        draft_content = "Sample draft content"
        review_feedback = "Sample review feedback"
        query = editing_team._create_final_revision_query("Test Section", draft_content, review_feedback)
        
        assert "Script Strategist" in query
        assert "Test Section" in query
        assert draft_content in query
        assert review_feedback in query
        assert "Address all concerns" in query
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_get_assistant_instructions(self, mock_openai_class):
        """Test _get_assistant_instructions method"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        instructions = editing_team._get_assistant_instructions()
        
        assert "EditingTeam" in instructions
        assert "file_search" in instructions
        assert "Documentalist" in instructions
        assert "Writer" in instructions
        assert "Reviewer" in instructions
        assert "Script Strategist" in instructions


class TestLegacyCompatibility:
    """Test backward compatibility with legacy edit_chapters function"""
    
    @patch('transcript_generator.tools.editing_team.EditingTeam')
    def test_legacy_edit_chapters_success(self, mock_editing_team_class):
        """Test legacy edit_chapters function with successful synthesis"""
        # Setup mock
        mock_editing_team = Mock()
        mock_editing_team_class.return_value = mock_editing_team
        
        mock_chapter_draft = Mock()
        mock_chapter_draft.content = "Generated content for module"
        mock_editing_team.synthesize_chapter.return_value = mock_chapter_draft
        
        # Test data
        research_notes = {"Module 1": "Research notes for module 1"}
        config = {"max_revisions": 3}
        
        result = edit_chapters(research_notes, config)
        
        # Verify result
        assert result == {"Module 1": "Generated content for module"}
        
        # Verify EditingTeam was created with config
        mock_editing_team_class.assert_called_once_with(max_revisions=3)
        
        # Verify synthesize_chapter was called with correct format
        mock_editing_team.synthesize_chapter.assert_called_once()
        call_args = mock_editing_team.synthesize_chapter.call_args[0][0]
        assert call_args['target_section'] == 'Module 1'
        assert call_args['research_notes'] == {'Module 1': 'Research notes for module 1'}
    
    @patch('transcript_generator.tools.editing_team.EditingTeam')
    def test_legacy_edit_chapters_fallback(self, mock_editing_team_class):
        """Test legacy edit_chapters fallback to stub behavior on error"""
        # Setup mock to raise exception
        mock_editing_team_class.side_effect = Exception("OpenAI API error")
        
        # Test data
        research_notes = {"Module 1": "Research notes for module 1"}
        config = {}
        
        result = edit_chapters(research_notes, config)
        
        # Should fallback to stub behavior
        assert result == {"Module 1": "Research notes for module 1"}
    
    def test_legacy_edit_chapters_empty_notes_error(self):
        """Test legacy edit_chapters with empty research notes"""
        research_notes = {"Module 1": ""}
        config = {}
        
        with pytest.raises(RuntimeError, match="No research notes provided for module: Module 1"):
            edit_chapters(research_notes, config)


class TestIntegrationPatterns:
    """Test integration patterns for US-004 compatibility"""
    
    def test_chapter_draft_schema_compliance(self):
        """Test that ChapterDraft complies with expected schema"""
        draft = ChapterDraft(
            section_id="test_section",
            content="test content"
        )
        
        # Verify schema compliance
        schema_dict = draft.to_dict()
        required_fields = ["section_id", "content"]
        
        for field in required_fields:
            assert field in schema_dict
            assert isinstance(schema_dict[field], str)
            assert len(schema_dict[field]) > 0
    
    def test_synthesis_request_interface_compliance(self):
        """Test synthesis request interface matches expectations"""
        request = SynthesisRequest(
            query="Create content for machine learning introduction",
            type="content_synthesis",
            target_module="Introduction to Machine Learning"
        )
        
        # Verify interface compliance
        request_dict = request.to_dict()
        required_fields = ["query", "type", "target_module"]
        
        for field in required_fields:
            assert field in request_dict
            assert isinstance(request_dict[field], str)
            assert len(request_dict[field]) > 0
    
    @patch('transcript_generator.tools.editing_team.OpenAI')
    def test_editing_team_response_api_integration_interface(self, mock_openai_class):
        """Test that EditingTeam provides proper interface for Response API integration"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        editing_team = EditingTeam(api_key="test-key")
        
        # Test that key methods exist and are callable
        assert hasattr(editing_team, 'synthesize_chapter')
        assert callable(editing_team.synthesize_chapter)
        
        # Test internal method interfaces
        assert hasattr(editing_team, '_create_research_files')
        assert callable(editing_team._create_research_files)
        
        assert hasattr(editing_team, '_upload_files_for_search')
        assert callable(editing_team._upload_files_for_search)
        
        assert hasattr(editing_team, '_create_research_assistant')
        assert callable(editing_team._create_research_assistant)
        
        assert hasattr(editing_team, '_execute_synthesis_workflow')
        assert callable(editing_team._execute_synthesis_workflow)
        
        assert hasattr(editing_team, '_cleanup_resources')
        assert callable(editing_team._cleanup_resources)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 