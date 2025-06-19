"""Knowledge Bridge MCP Server Module

Provides MCP interface for knowledge database access with proper schemas
and thread-safe operations for concurrent queries.
"""

from .content_accessor import ContentAccessor
from .mcp_interface import KnowledgeMCPServer

__all__ = ['ContentAccessor', 'KnowledgeMCPServer']