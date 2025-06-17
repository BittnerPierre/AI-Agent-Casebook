"""Knowledge Bridge MCP Server Module

Provides MCP interface for knowledge database access with proper schemas
and thread-safe operations for concurrent queries.
"""

from .mcp_interface import KnowledgeMCPServer
from .content_accessor import ContentAccessor

__all__ = ['KnowledgeMCPServer', 'ContentAccessor']