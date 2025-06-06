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


# Mock MCP Server for testing
class MockMCPServer:
    def __init__(self):
        pass


@pytest.mark.asyncio
async def test_ensure_directories_exist():
    """Test MCP helper method for directory creation."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dirs = [
            os.path.join(temp_dir, "output", "test_course"),
            os.path.join(temp_dir, "output", "test_course", "cleaned_transcripts"),
            os.path.join(temp_dir, "output", "test_course", "metadata")
        ]
        
        await manager._ensure_directories_exist(mock_server, test_dirs)
        
        # Verify directories were created
        for directory in test_dirs:
            assert os.path.exists(directory)
            assert os.path.isdir(directory)


@pytest.mark.asyncio
async def test_list_transcript_files():
    """Test MCP helper method for listing transcript files."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test transcript files
        test_files = ["module1.txt", "module2.txt", "other.md"]
        for filename in test_files:
            with open(os.path.join(temp_dir, filename), "w") as f:
                f.write("test content")
        
        files = await manager._list_transcript_files(mock_server, temp_dir)
        
        # Should only return .txt files, sorted
        expected = ["module1.txt", "module2.txt"]
        assert files == expected


@pytest.mark.asyncio
async def test_file_exists():
    """Test MCP helper method for file existence check."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        existing_file = os.path.join(temp_dir, "existing.txt")
        non_existing_file = os.path.join(temp_dir, "non_existing.txt")
        
        # Create existing file
        with open(existing_file, "w") as f:
            f.write("test content")
        
        # Test existing file
        assert await manager._file_exists(mock_server, existing_file) is True
        
        # Test non-existing file
        assert await manager._file_exists(mock_server, non_existing_file) is False


@pytest.mark.asyncio
async def test_read_file():
    """Test MCP helper method for file reading."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = "Hello, world!\nThis is a test file."
        
        # Create test file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Test reading
        content = await manager._read_file(mock_server, test_file)
        assert content == test_content


@pytest.mark.asyncio
async def test_write_file():
    """Test MCP helper method for file writing."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "output.txt")
        test_content = "Hello, world!\nThis is written content."
        
        # Test writing
        await manager._write_file(mock_server, test_file, test_content)
        
        # Verify file was written
        assert os.path.exists(test_file)
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == test_content


@pytest.mark.asyncio 
async def test_read_file_error_handling():
    """Test MCP helper method error handling for non-existent file."""
    manager = TrainingManager()
    mock_server = MockMCPServer()
    
    non_existing_file = "/path/that/does/not/exist.txt"
    
    with pytest.raises(Exception):
        await manager._read_file(mock_server, non_existing_file)

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

