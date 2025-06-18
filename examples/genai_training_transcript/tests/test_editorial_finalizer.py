"""
Tests for Editorial Finalizer - US-005 Implementation

This module tests the EditorialFinalizer class to ensure it correctly:
1. Detects misconduct according to defined categories
2. Produces correct output files (final_transcript.md, quality_issues.json)
3. Tracks quality metrics for evaluation system integration
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from transcript_generator.editorial_finalizer import (
    EditorialFinalizer,
    ChapterDraft,
    QualityIssue,
    IssueSeverity
)


class TestEditorialFinalizer:
    """Test cases for EditorialFinalizer class"""
    
    def setup_method(self):
        """Setup test environment with temporary directories"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        self.output_dir = self.temp_path / "output"
        self.quality_dir = self.temp_path / "quality_issues"
        
        self.finalizer = EditorialFinalizer(
            output_dir=str(self.output_dir),
            quality_dir=str(self.quality_dir)
        )
    
    def teardown_method(self):
        """Cleanup temporary directories"""
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Test EditorialFinalizer initialization creates directories"""
        assert self.output_dir.exists()
        assert self.quality_dir.exists()
        assert hasattr(self.finalizer, 'misconduct_categories')
        
        # Check misconduct categories are properly defined
        assert "CRITICAL" in self.finalizer.misconduct_categories
        assert "HIGH" in self.finalizer.misconduct_categories 
        assert "MEDIUM" in self.finalizer.misconduct_categories
    
    def test_track_issues_short_content(self):
        """Test detection of inadequate content length"""
        chapter = ChapterDraft(
            section_id="test_01",
            content="Too short",
            title="Test Chapter"
        )
        
        issues = self.finalizer.track_issues(chapter)
        
        # Should detect short content
        assert len(issues) > 0
        short_content_issue = next((i for i in issues if "too short" in i.description.lower()), None)
        assert short_content_issue is not None
        assert short_content_issue.severity == IssueSeverity.ERROR
        assert short_content_issue.misconduct_category == "inadequate_level"
    
    def test_track_issues_repetitive_content(self):
        """Test detection of repetitive content"""
        repetitive_content = "This is repetitive content. " * 50  # Very repetitive
        chapter = ChapterDraft(
            section_id="test_02",
            content=repetitive_content,
            title="Repetitive Chapter"
        )
        
        issues = self.finalizer.track_issues(chapter)
        
        # Should detect repetitive content
        repetition_issue = next((i for i in issues if "repetitive" in i.description.lower()), None)
        assert repetition_issue is not None
        assert repetition_issue.misconduct_category == "content_repetition"
    
    def test_track_issues_ai_artifacts(self):
        """Test detection of AI artifacts in content"""
        content_with_artifacts = """
        This is a good chapter about machine learning.
        As an AI, I cannot provide specific recommendations.
        TODO: Add more examples here.
        Machine learning is an important topic.
        """
        
        chapter = ChapterDraft(
            section_id="test_03",
            content=content_with_artifacts,
            title="Chapter with Artifacts"
        )
        
        issues = self.finalizer.track_issues(chapter)
        
        # Should detect AI artifacts
        ai_artifact_issues = [i for i in issues if "ai artifacts" in i.description.lower()]
        assert len(ai_artifact_issues) >= 1
        assert ai_artifact_issues[0].severity == IssueSeverity.ERROR
        assert ai_artifact_issues[0].misconduct_category == "training_principles_violations"
    
    def test_track_issues_syllabus_alignment(self):
        """Test syllabus alignment checking"""
        chapter = ChapterDraft(
            section_id="section_01",
            content="This chapter discusses completely different topics than expected.",
            title="Misaligned Chapter"
        )
        
        syllabus = {
            "course_title": "Machine Learning Basics",
            "sections": [
                {
                    "section_id": "section_01",
                    "title": "Introduction to Neural Networks",
                    "learning_objectives": [
                        "Understand neural network architecture",
                        "Implement basic perceptron"
                    ],
                    "key_topics": ["neurons", "weights", "activation functions"]
                }
            ]
        }
        
        issues = self.finalizer.track_issues(chapter, syllabus)
        
        # Should detect syllabus misalignment
        alignment_issues = [i for i in issues if i.misconduct_category == "content_syllabus_alignment"]
        assert len(alignment_issues) > 0
    
    def test_finalize_content_creates_outputs(self):
        """Test that finalize_content creates expected output files"""
        chapters = [
            ChapterDraft(
                section_id="section_01",
                content="This is a well-structured chapter about machine learning. " * 20,
                title="Machine Learning Introduction"
            ),
            ChapterDraft(
                section_id="section_02", 
                content="This chapter covers advanced topics in depth. " * 25,
                title="Advanced Concepts"
            )
        ]
        
        syllabus = {
            "course_title": "Machine Learning Course",
            "sections": [
                {"section_id": "section_01", "title": "Introduction", "learning_objectives": [], "key_topics": []},
                {"section_id": "section_02", "title": "Advanced", "learning_objectives": [], "key_topics": []}
            ]
        }
        
        md_path, summary_path = self.finalizer.finalize_content(chapters, syllabus)
        
        # Check that files were created
        assert Path(md_path).exists()
        assert Path(summary_path).exists()
        
        # Check individual quality files were created
        assert (self.quality_dir / "section_01.json").exists()
        assert (self.quality_dir / "section_02.json").exists()
        
        # Check final transcript JSON was created
        assert (self.output_dir / "final_transcript.json").exists()
        
        # Verify content of final transcript JSON
        with open(self.output_dir / "final_transcript.json", 'r') as f:
            transcript_data = json.load(f)
        
        assert transcript_data["course_title"] == "Machine Learning Course"
        assert len(transcript_data["sections"]) == 2
        assert transcript_data["sections"][0]["section_id"] == "section_01"
    
    def test_quality_metrics_interface(self):
        """Test get_quality_metrics method for evaluation system integration"""
        # First, create some quality data
        chapters = [
            ChapterDraft(
                section_id="test_section",
                content="Short",  # This will trigger an error
                title="Test"
            )
        ]
        
        self.finalizer.finalize_content(chapters)
        
        # Test quality metrics retrieval
        metrics = self.finalizer.get_quality_metrics()
        
        assert "total_issues" in metrics
        assert "error_count" in metrics
        assert "warning_count" in metrics
        assert "sections_with_errors" in metrics
        assert "misconduct_categories" in metrics
        assert "quality_score" in metrics
        
        # Should have detected the short content error
        assert metrics["error_count"] > 0
        assert metrics["total_issues"] > 0
        assert metrics["quality_score"] < 1.0
    
    def test_groundedness_violations_detection(self):
        """Test detection of groundedness violations"""
        content_with_vague_claims = """
        Everyone knows that machine learning is the future.
        Obviously, neural networks are the best approach.
        It goes without saying that this technology will revolutionize everything.
        Without a doubt, this is the most important advancement.
        """
        
        chapter = ChapterDraft(
            section_id="test_04",
            content=content_with_vague_claims,
            title="Vague Chapter"
        )
        
        issues = self.finalizer.track_issues(chapter)
        
        # Should detect groundedness violations
        groundedness_issues = [i for i in issues if i.misconduct_category == "groundedness_violations"]
        assert len(groundedness_issues) > 0
        
        # Check that vague claim indicators are detected
        vague_claim_issues = [i for i in groundedness_issues if "unsupported claims" in i.description]
        assert len(vague_claim_issues) > 0
    
    def test_training_principles_structure_check(self):
        """Test training course principles checking for educational structure"""
        # Content without proper educational structure
        unstructured_content = "Machine learning algorithms process data. " * 50
        
        # Content with good educational structure  
        structured_content = """
        Introduction: Welcome to this chapter on machine learning.
        
        For example, consider a neural network that processes images.
        Such as convolutional neural networks used in computer vision.
        
        Summary: In this chapter we covered the key concepts of machine learning.
        """
        
        unstructured_chapter = ChapterDraft(
            section_id="unstructured",
            content=unstructured_content,
            title="Unstructured Chapter"
        )
        
        structured_chapter = ChapterDraft(
            section_id="structured", 
            content=structured_content,
            title="Structured Chapter"
        )
        
        unstructured_issues = self.finalizer.track_issues(unstructured_chapter)
        structured_issues = self.finalizer.track_issues(structured_chapter)
        
        # Unstructured should have training principles violations
        training_violations_unstructured = [
            i for i in unstructured_issues 
            if i.misconduct_category == "training_principles_violations"
        ]
        
        training_violations_structured = [
            i for i in structured_issues 
            if i.misconduct_category == "training_principles_violations" 
            and "educational structure" in i.description
        ]
        
        # Unstructured content should trigger violations, structured should not
        assert len(training_violations_unstructured) > len(training_violations_structured)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation logic"""
        # Test with no issues
        summary_no_issues = {
            "total_issues": 0,
            "issues_by_severity": {"INFO": 0, "WARNING": 0, "ERROR": 0}
        }
        score = self.finalizer._calculate_quality_score(summary_no_issues)
        assert score == 1.0
        
        # Test with only warnings
        summary_warnings = {
            "total_issues": 2,
            "issues_by_severity": {"INFO": 0, "WARNING": 2, "ERROR": 0}
        }
        score = self.finalizer._calculate_quality_score(summary_warnings)
        assert 0.8 <= score < 1.0  # Should be high but not perfect
        
        # Test with errors
        summary_errors = {
            "total_issues": 3,
            "issues_by_severity": {"INFO": 0, "WARNING": 1, "ERROR": 2}
        }
        score = self.finalizer._calculate_quality_score(summary_errors)
        assert score < 0.8  # Should be significantly lower with errors
    
    def test_json_schema_compliance(self):
        """Test that output JSON files comply with defined schemas"""
        chapter = ChapterDraft(
            section_id="schema_test",
            content="This is a test chapter for schema compliance." * 10,
            title="Schema Test Chapter"
        )
        
        self.finalizer.finalize_content([chapter])
        
        # Test quality issues schema compliance
        quality_file = self.quality_dir / "schema_test.json"
        with open(quality_file, 'r') as f:
            quality_data = json.load(f)
        
        # Check required fields per schema
        assert "section_id" in quality_data
        assert "issues" in quality_data
        assert "approved" in quality_data
        assert isinstance(quality_data["issues"], list)
        assert isinstance(quality_data["approved"], bool)
        
        # Check issue structure
        for issue in quality_data["issues"]:
            assert "description" in issue
            assert "severity" in issue
            assert issue["severity"] in ["INFO", "WARNING", "ERROR"]
        
        # Test final transcript schema compliance
        transcript_file = self.output_dir / "final_transcript.json"
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        
        assert "course_title" in transcript_data
        assert "sections" in transcript_data
        assert isinstance(transcript_data["sections"], list)
        
        for section in transcript_data["sections"]:
            assert "section_id" in section
            assert "title" in section
            assert "content" in section


if __name__ == "__main__":
    pytest.main([__file__]) 