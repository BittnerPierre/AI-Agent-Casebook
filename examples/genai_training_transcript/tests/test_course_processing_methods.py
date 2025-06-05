#!/usr/bin/env python3
"""
Unit tests for course processing methods in training manager.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock

# Mock the agents module since it's not available in test environment
import sys
sys.modules['agents'] = Mock()
sys.modules['agents.mcp'] = Mock()

from training_manager.core import TrainingManager


class TestCourseProcessingMethods:
    """Test course processing methods for single-file and directory courses."""

    @pytest.fixture
    def training_manager(self):
        """Create a TrainingManager instance for testing."""
        return TrainingManager(overwrite=False)

    def test_process_single_file_course(self, training_manager):
        """Test processing a single .txt file course."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Test transcript content")
            course_path = temp_file.name
            
        try:
            # Test with underscore filename
            base_name = "Advanced_Retrieval_for_AI.txt"
            full_path = os.path.join(os.path.dirname(course_path), base_name)
            os.rename(course_path, full_path)
            
            course_id, course_title, modules, transcripts_dir = training_manager._process_single_file_course(full_path)
            
            # Verify results
            assert course_id == "Advanced_Retrieval_for_AI"
            assert course_title == "Advanced Retrieval for AI"  # Underscores converted to spaces
            assert len(modules) == 1
            assert modules[0]["filename"] == base_name
            assert modules[0]["filepath"] == full_path
            assert modules[0]["module_id"] == "Advanced_Retrieval_for_AI"
            assert transcripts_dir == os.path.dirname(full_path)
            
        finally:
            if os.path.exists(full_path):
                os.unlink(full_path)

    def test_process_single_file_course_simple_name(self, training_manager):
        """Test processing single file with simple name (no underscores)."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Test content")
            course_path = temp_file.name
            
        try:
            base_name = "Course.txt"
            full_path = os.path.join(os.path.dirname(course_path), base_name)
            os.rename(course_path, full_path)
            
            course_id, course_title, modules, transcripts_dir = training_manager._process_single_file_course(full_path)
            
            assert course_id == "Course"
            assert course_title == "Course"  # No underscores to convert
            assert len(modules) == 1
            assert modules[0]["module_id"] == "Course"
            
        finally:
            if os.path.exists(full_path):
                os.unlink(full_path)

    def test_process_directory_course_with_dash_separator(self, training_manager):
        """Test processing directory course with course_id - course_name format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create course directory with dash separator
            course_dir = os.path.join(temp_dir, "CHROMA - Chroma Course")
            transcripts_dir = os.path.join(course_dir, "transcripts")
            os.makedirs(transcripts_dir)
            
            # Create test transcript files
            test_files = ["module1_en - Chroma - 1 - Introduction.txt", "module2_en - Chroma - 2 - Advanced.txt"]
            for filename in test_files:
                with open(os.path.join(transcripts_dir, filename), 'w') as f:
                    f.write("Test transcript content")
            
            course_id, course_title, modules, returned_transcripts_dir = training_manager._process_directory_course(course_dir)
            
            assert course_id == "CHROMA"
            assert course_title == "Chroma Course"
            assert len(modules) == 2
            assert "module1_en - Chroma - 1 - Introduction.txt" in modules
            assert "module2_en - Chroma - 2 - Advanced.txt" in modules
            assert returned_transcripts_dir == transcripts_dir

    def test_process_directory_course_without_dash_separator(self, training_manager):
        """Test processing directory course without dash separator."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create course directory without dash separator
            course_dir = os.path.join(temp_dir, "SimpleCourse")
            transcripts_dir = os.path.join(course_dir, "transcripts")
            os.makedirs(transcripts_dir)
            
            # Create test transcript files
            with open(os.path.join(transcripts_dir, "lesson1.txt"), 'w') as f:
                f.write("Test content")
            
            course_id, course_title, modules, returned_transcripts_dir = training_manager._process_directory_course(course_dir)
            
            assert course_id == "SimpleCourse"
            assert course_title == "SimpleCourse"  # Falls back to course_id
            assert len(modules) == 1
            assert "lesson1.txt" in modules

    def test_process_directory_course_missing_transcripts_dir(self, training_manager):
        """Test processing directory course with missing transcripts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = os.path.join(temp_dir, "MISSING - Missing Course")
            os.makedirs(course_dir)
            # Don't create transcripts subdirectory
            
            with pytest.raises(FileNotFoundError, match="Transcripts directory not found"):
                training_manager._process_directory_course(course_dir)

    def test_process_directory_course_empty_transcripts_dir(self, training_manager):
        """Test processing directory course with empty transcripts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = os.path.join(temp_dir, "EMPTY - Empty Course")
            transcripts_dir = os.path.join(course_dir, "transcripts")
            os.makedirs(transcripts_dir)
            
            # Create non-.txt files
            with open(os.path.join(transcripts_dir, "readme.md"), 'w') as f:
                f.write("Not a transcript")
            
            with pytest.raises(ValueError, match="No .txt transcript files found"):
                training_manager._process_directory_course(course_dir)

    def test_process_directory_course_filters_non_txt_files(self, training_manager):
        """Test that directory processing only includes .txt files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = os.path.join(temp_dir, "FILTER - Filter Course")
            transcripts_dir = os.path.join(course_dir, "transcripts")
            os.makedirs(transcripts_dir)
            
            # Create mixed file types
            files_to_create = [
                ("transcript1.txt", True),    # Should be included
                ("readme.md", False),         # Should be excluded
                ("transcript2.txt", True),    # Should be included
                ("notes.docx", False),        # Should be excluded
                ("module3.txt", True),        # Should be included
            ]
            
            for filename, _ in files_to_create:
                with open(os.path.join(transcripts_dir, filename), 'w') as f:
                    f.write("Content")
            
            course_id, course_title, modules, returned_transcripts_dir = training_manager._process_directory_course(course_dir)
            
            # Should only include .txt files, sorted
            expected_modules = ["module3.txt", "transcript1.txt", "transcript2.txt"]
            assert modules == expected_modules
            assert len(modules) == 3

    def test_modules_are_sorted(self, training_manager):
        """Test that modules are returned in sorted order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = os.path.join(temp_dir, "SORT - Sort Test")
            transcripts_dir = os.path.join(course_dir, "transcripts")
            os.makedirs(transcripts_dir)
            
            # Create files in non-alphabetical order
            unsorted_files = ["zebra.txt", "alpha.txt", "beta.txt", "gamma.txt"]
            for filename in unsorted_files:
                with open(os.path.join(transcripts_dir, filename), 'w') as f:
                    f.write("Content")
            
            course_id, course_title, modules, returned_transcripts_dir = training_manager._process_directory_course(course_dir)
            
            # Should be sorted alphabetically
            expected_sorted = ["alpha.txt", "beta.txt", "gamma.txt", "zebra.txt"]
            assert modules == expected_sorted