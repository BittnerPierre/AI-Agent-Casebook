#!/usr/bin/env python3
"""
Unit tests for MCP helper methods in training manager.
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, Mock

# Mock the agents module since it's not available in test environment
import sys
sys.modules['agents'] = Mock()
sys.modules['agents.mcp'] = Mock()

from training_manager.core import TrainingManager


class TestMCPHelperMethods:
    """Test MCP helper methods with mock MCP server."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server for testing."""
        return AsyncMock()

    @pytest.fixture
    def training_manager(self):
        """Create a TrainingManager instance for testing."""
        return TrainingManager(overwrite=False)

    @pytest.mark.asyncio
    async def test_ensure_directories_exist(self, training_manager, mock_mcp_server):
        """Test directory creation via MCP helper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dirs = [
                os.path.join(temp_dir, "output", "TEST", "cleaned_transcripts"),
                os.path.join(temp_dir, "output", "TEST", "metadata")
            ]
            
            await training_manager._ensure_directories_exist(mock_mcp_server, test_dirs)
            
            # Verify directories were created
            for directory in test_dirs:
                assert os.path.exists(directory), f"Directory {directory} should exist"

    @pytest.mark.asyncio
    async def test_list_transcript_files_existing_dir(self, training_manager, mock_mcp_server):
        """Test listing transcript files in existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test transcript files
            test_files = ["module1.txt", "module2.txt", "notes.md", "module3.txt"]
            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write("test content")
            
            result = await training_manager._list_transcript_files(mock_mcp_server, temp_dir)
            
            # Should only return .txt files, sorted
            expected = ["module1.txt", "module2.txt", "module3.txt"]
            assert result == expected

    @pytest.mark.asyncio
    async def test_list_transcript_files_nonexistent_dir(self, training_manager, mock_mcp_server):
        """Test listing transcript files in non-existent directory."""
        result = await training_manager._list_transcript_files(mock_mcp_server, "/nonexistent/path")
        assert result == []

    @pytest.mark.asyncio
    async def test_file_exists_true(self, training_manager, mock_mcp_server):
        """Test file existence check for existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            result = await training_manager._file_exists(mock_mcp_server, temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_file_exists_false(self, training_manager, mock_mcp_server):
        """Test file existence check for non-existent file."""
        result = await training_manager._file_exists(mock_mcp_server, "/nonexistent/file.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_read_file(self, training_manager, mock_mcp_server):
        """Test reading file content via MCP helper."""
        test_content = "This is test content\nWith multiple lines"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
            
        try:
            result = await training_manager._read_file(mock_mcp_server, temp_path)
            assert result == test_content
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_read_file_error(self, training_manager, mock_mcp_server):
        """Test reading non-existent file raises exception."""
        with pytest.raises(Exception):
            await training_manager._read_file(mock_mcp_server, "/nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_write_file(self, training_manager, mock_mcp_server):
        """Test writing file content via MCP helper."""
        test_content = "This is test content\nWith multiple lines"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            await training_manager._write_file(mock_mcp_server, temp_path, test_content)
            
            # Verify content was written correctly
            with open(temp_path, 'r', encoding='utf-8') as f:
                result = f.read()
            assert result == test_content
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_write_file_error(self, training_manager, mock_mcp_server):
        """Test writing to invalid path raises exception."""
        with pytest.raises(Exception):
            await training_manager._write_file(mock_mcp_server, "/invalid/path/file.txt", "content")