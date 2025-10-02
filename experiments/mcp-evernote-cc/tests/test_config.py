"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from evernote_chatbot.config import ChatbotConfig


class TestChatbotConfig:
    """Test cases for ChatbotConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ChatbotConfig()

        assert config.mcp_url == "https://localhost:3443/mcp"
        assert config.mcp_headers == {}
        assert config.mcp_timeout == 30.0
        assert config.max_notes_per_query == 20
        assert config.allowed_notebooks == set()
        assert config.prefer_html is False
        assert config.show_timestamps is True
        assert config.show_tags is True
        assert config.show_notebook is True
        assert config.max_content_preview == 200
        assert config.save_history is True

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "MCP_URL": "https://example.com:8443/mcp",
            "MCP_HEADERS": '{"Authorization": "Bearer token123"}',
            "MCP_TIMEOUT": "60.0",
            "MAX_NOTES_PER_QUERY": "50",
            "ALLOWED_NOTEBOOKS": "Work,Personal,Research",
            "PREFER_HTML": "true",
            "SHOW_TIMESTAMPS": "false",
            "SHOW_TAGS": "no",
            "SHOW_NOTEBOOK": "1",
            "MAX_CONTENT_PREVIEW": "500",
            "SAVE_HISTORY": "false",
            "HISTORY_FILE": "/tmp/history.json",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ChatbotConfig.from_env()

        assert config.mcp_url == "https://example.com:8443/mcp"
        assert config.mcp_headers == {"Authorization": "Bearer token123"}
        assert config.mcp_timeout == 60.0
        assert config.max_notes_per_query == 50
        assert config.allowed_notebooks == {"Work", "Personal", "Research"}
        assert config.prefer_html is True
        assert config.show_timestamps is False
        assert config.show_tags is False
        assert config.show_notebook is True
        assert config.max_content_preview == 500
        assert config.save_history is False
        assert config.history_file == "/tmp/history.json"

    def test_parse_headers_json_string(self):
        """Test parsing headers from JSON string."""
        config = ChatbotConfig(mcp_headers='{"Content-Type": "application/json"}')
        assert config.mcp_headers == {"Content-Type": "application/json"}

    def test_parse_headers_invalid_json(self):
        """Test parsing invalid JSON headers."""
        config = ChatbotConfig(mcp_headers='{invalid json}')
        assert config.mcp_headers == {}

    def test_parse_notebooks_string(self):
        """Test parsing notebooks from comma-separated string."""
        config = ChatbotConfig(allowed_notebooks="Work, Personal, Research, ")
        assert config.allowed_notebooks == {"Work", "Personal", "Research"}

    def test_parse_notebooks_empty_string(self):
        """Test parsing empty notebooks string."""
        config = ChatbotConfig(allowed_notebooks="")
        assert config.allowed_notebooks == set()

    def test_parse_notebooks_list(self):
        """Test parsing notebooks from list."""
        config = ChatbotConfig(allowed_notebooks=["Work", "Personal"])
        assert config.allowed_notebooks == {"Work", "Personal"}

    def test_merge_cli_args(self):
        """Test merging CLI arguments into config."""
        base_config = ChatbotConfig(max_notes_per_query=10)

        merged = base_config.merge_cli_args(
            mcp_url="https://new.example.com/mcp",
            notebooks="Project1,Project2",
            headers='{"X-Custom": "value"}',
            max_notes_per_query=30,
            prefer_html=True,
        )

        assert merged.mcp_url == "https://new.example.com/mcp"
        assert merged.allowed_notebooks == {"Project1", "Project2"}
        assert merged.mcp_headers == {"X-Custom": "value"}
        assert merged.max_notes_per_query == 30
        assert merged.prefer_html is True

        # Original config should be unchanged
        assert base_config.max_notes_per_query == 10

    def test_merge_cli_args_ignore_none(self):
        """Test that None values are ignored when merging."""
        base_config = ChatbotConfig(max_notes_per_query=10)

        merged = base_config.merge_cli_args(
            mcp_url=None,
            max_notes_per_query=20,
            prefer_html=None,
        )

        assert merged.mcp_url == "https://localhost:3443/mcp"  # unchanged
        assert merged.max_notes_per_query == 20  # changed
        assert merged.prefer_html is False  # unchanged

    def test_to_display_dict(self):
        """Test converting config to display dictionary."""
        config = ChatbotConfig(
            mcp_url="https://test.com/mcp",
            max_notes_per_query=15,
            allowed_notebooks={"Work", "Personal"},
            prefer_html=True,
            mcp_headers={"Auth": "token"},
            mcp_timeout=45.0,
        )

        display_dict = config.to_display_dict()

        assert display_dict["MCP URL"] == "https://test.com/mcp"
        assert display_dict["Max Notes"] == "15"
        assert display_dict["Allowed Notebooks"] == "Personal, Work"
        assert display_dict["Prefer HTML"] == "Yes"
        assert display_dict["Custom Headers"] == "Yes"
        assert display_dict["Timeout"] == "45.0s"

    def test_validation_max_notes_positive(self):
        """Test validation that max_notes_per_query must be positive."""
        with pytest.raises(ValueError):
            ChatbotConfig(max_notes_per_query=0)

        with pytest.raises(ValueError):
            ChatbotConfig(max_notes_per_query=-5)

    def test_validation_max_notes_limit(self):
        """Test validation that max_notes_per_query has upper limit."""
        with pytest.raises(ValueError):
            ChatbotConfig(max_notes_per_query=200)

    def test_validation_timeout_positive(self):
        """Test validation that timeout must be positive."""
        with pytest.raises(ValueError):
            ChatbotConfig(mcp_timeout=0.0)

        with pytest.raises(ValueError):
            ChatbotConfig(mcp_timeout=-1.0)