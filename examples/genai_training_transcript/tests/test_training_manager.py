#!/usr/bin/env python3
"""
Unit tests for transcript preprocessor, metadata extractor, and training manager.
"""

import os
import tempfile
import pytest

from tools.transcript_preprocessor import preprocess_transcript, Runner as PreprocessorRunner
from tools.metadata_extractor import extract_metadata, Runner as MetadataRunner
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