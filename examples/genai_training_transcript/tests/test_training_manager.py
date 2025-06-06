#!/usr/bin/env python3
"""
Unit tests for transcript preprocessor, metadata extractor, and training manager.
"""

import os
import tempfile
import pytest

from transcript_generator.tools.transcript_preprocessor import preprocess_transcript, Runner as PreprocessorRunner
from transcript_generator.tools.metadata_extractor import extract_metadata, Runner as MetadataRunner
from training_manager.core import TrainingManager


class DummyOutput:
    def __init__(self, content=None, summary=None, keywords=None, tags=None):
        self.content = content
        self.summary = summary
        self.keywords = keywords
        self.tags = tags


class DummyResult:
    def __init__(self, output: DummyOutput):
        self.final_output = output

    def final_output_as(self, model):
        return model(
            summary=self.final_output.summary,
            keywords=self.final_output.keywords,
            tags=self.final_output.tags,
        )


async def dummy_preprocess(*args, **kwargs):
    return DummyResult(DummyOutput(content="cleaned content"))


async def dummy_metadata(*args, **kwargs):
    return DummyResult(
        DummyOutput(summary="summary text", keywords=["kw1", "kw2"], tags=["tag"])
    )


@pytest.mark.asyncio
async def test_preprocess_transcript(monkeypatch):
    monkeypatch.setattr(PreprocessorRunner, "run", dummy_preprocess)
    cleaned = await preprocess_transcript("mod1.txt", None)
    assert cleaned == "cleaned content"


@pytest.mark.asyncio
async def test_extract_metadata(monkeypatch):
    monkeypatch.setattr(MetadataRunner, "run", dummy_metadata)
    meta = await extract_metadata("mod1.txt", "cleaned content")
    assert meta.summary == "summary text"
    assert meta.keywords == ["kw1", "kw2"]
    assert meta.tags == ["tag"]


def test_process_single_file_course():
    """Test processing of single .txt file courses."""
    manager = TrainingManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test single file course
        course_file = os.path.join(temp_dir, "Advanced_AI_Course.txt")
        with open(course_file, "w", encoding="utf-8") as f:
            f.write("This is a test transcript content.")
        
        # Test processing
        course_id, course_title, modules, transcripts_dir = manager._process_single_file_course(course_file)
        
        # Verify results
        assert course_id == "Advanced_AI_Course"
        assert course_title == "Advanced AI Course"
        assert len(modules) == 1
        assert modules[0]["filename"] == "Advanced_AI_Course.txt"
        assert modules[0]["filepath"] == course_file
        assert modules[0]["module_id"] == "Advanced_AI_Course"
        assert transcripts_dir == temp_dir


def test_process_directory_course():
    """Test processing of multi-module directory courses."""
    manager = TrainingManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test directory course structure
        course_dir = os.path.join(temp_dir, "COURSE001 - Advanced AI")
        transcripts_dir = os.path.join(course_dir, "transcripts")
        os.makedirs(transcripts_dir)
        
        # Create test transcript files
        test_files = ["module1.txt", "module2.txt"]
        for filename in test_files:
            with open(os.path.join(transcripts_dir, filename), "w", encoding="utf-8") as f:
                f.write(f"Content for {filename}")
        
        # Test processing
        course_id, course_title, modules, result_transcripts_dir = manager._process_directory_course(course_dir)
        
        # Verify results
        assert course_id == "COURSE001"
        assert course_title == "Advanced AI"
        assert modules == ["module1.txt", "module2.txt"]
        assert result_transcripts_dir == transcripts_dir


def test_process_directory_course_no_transcripts_dir():
    """Test error handling when transcripts directory doesn't exist."""
    manager = TrainingManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        course_dir = os.path.join(temp_dir, "COURSE001 - Test Course")
        os.makedirs(course_dir)
        # Don't create transcripts subdirectory
        
        with pytest.raises(FileNotFoundError, match="Transcripts directory not found"):
            manager._process_directory_course(course_dir)


def test_process_directory_course_no_txt_files():
    """Test error handling when no .txt files are found."""
    manager = TrainingManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        course_dir = os.path.join(temp_dir, "COURSE001 - Test Course")
        transcripts_dir = os.path.join(course_dir, "transcripts")
        os.makedirs(transcripts_dir)
        
        # Create non-.txt files
        with open(os.path.join(transcripts_dir, "readme.md"), "w") as f:
            f.write("Not a transcript")
        
        with pytest.raises(ValueError, match="No .txt transcript files found"):
            manager._process_directory_course(course_dir)


def test_process_directory_course_single_name():
    """Test directory course with single name (no dash separator)."""
    manager = TrainingManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        course_dir = os.path.join(temp_dir, "SingleNameCourse")
        transcripts_dir = os.path.join(course_dir, "transcripts")
        os.makedirs(transcripts_dir)
        
        # Create test transcript file
        with open(os.path.join(transcripts_dir, "module1.txt"), "w", encoding="utf-8") as f:
            f.write("Test content")
        
        # Test processing
        course_id, course_title, modules, result_transcripts_dir = manager._process_directory_course(course_dir)
        
        # Verify results - both should be the same when no dash separator
        assert course_id == "SingleNameCourse"
        assert course_title == "SingleNameCourse"
        assert modules == ["module1.txt"]