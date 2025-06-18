"""
Knowledge Bridge MCP Interface

Implements MCP server for knowledge database access with proper schemas
and thread-safe operations. Provides lookup_content and read_content operations.

Author: Sprint 1 Development Team  
Reference: US-001 Knowledge Database MCP Interface
"""

import json
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from training_manager.content_accessor import ContentAccessor


class KnowledgeMCPServer:
    """
    MCP Server interface for knowledge database access.
    
    Implements the interface specified in sprint_1.md:
    - lookup_content(keywords, max_results) -> KnowledgeResponse  
    - read_content(content_id) -> ContentData
    - health_check() -> status
    
    Provides thread-safe access for concurrent queries.
    """
    
    def __init__(self, output_base_path: str = "output"):
        """Initialize Knowledge MCP Server with content accessor"""
        self.content_accessor = ContentAccessor(output_base_path)
        self._lock = threading.RLock()
        self._query_count = 0
        print("[KnowledgeMCPServer] Initialized with MCP protocol support")
    
    def lookup_content(self, keywords: List[str], learning_objectives: Optional[List[str]] = None, 
                      max_results: int = 10) -> Dict[str, Any]:
        """
        MCP Operation: lookup_content
        
        Searches knowledge base using keywords and optional learning objectives.
        
        Args:
            keywords: List of search keywords
            learning_objectives: Optional learning objectives to filter by
            max_results: Maximum number of results to return
            
        Returns:
            KnowledgeResponse schema with content matches
        """
        with self._lock:
            self._query_count += 1
            query_id = f"query_{self._query_count}_{int(datetime.now().timestamp())}"
            
            print(f"[KnowledgeMCPServer] Processing lookup_content: {query_id}")
            print(f"[KnowledgeMCPServer] Keywords: {keywords}")
            if learning_objectives:
                print(f"[KnowledgeMCPServer] Learning objectives: {learning_objectives}")
            
            try:
                # Combine keywords with learning objectives for broader search
                search_terms = keywords.copy()
                if learning_objectives:
                    # Extract key terms from learning objectives
                    for objective in learning_objectives:
                        # Simple extraction - could be enhanced with NLP
                        obj_words = [word.strip().lower() for word in objective.split() 
                                   if len(word.strip()) > 3 and word.strip().lower() not in 
                                   ['learn', 'understand', 'apply', 'practice', 'hands-on']]
                        search_terms.extend(obj_words)
                
                # Remove duplicates while preserving order
                unique_search_terms = []
                seen = set()
                for term in search_terms:
                    if term.lower() not in seen:
                        unique_search_terms.append(term)
                        seen.add(term.lower())
                
                # Get content matches from content accessor
                content_matches = self.content_accessor.get_by_keywords(
                    unique_search_terms, max_results
                )
                
                # Format response according to KnowledgeResponse schema
                knowledge_response = {
                    "query_id": query_id,
                    "total_matches": len(content_matches),
                    "content_matches": content_matches
                }
                
                print(f"[KnowledgeMCPServer] Lookup complete: {len(content_matches)} matches")
                return knowledge_response
                
            except Exception as e:
                print(f"[KnowledgeMCPServer] Error in lookup_content: {str(e)}")
                # Return empty response on error
                return {
                    "query_id": query_id,
                    "total_matches": 0,
                    "content_matches": [],
                    "error": str(e)
                }
    
    def read_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        MCP Operation: read_content
        
        Retrieves full content by content_id.
        
        Args:
            content_id: Content identifier (format: "course_id:module_id")
            
        Returns:
            ContentData schema with full content and metadata or None
        """
        with self._lock:
            print(f"[KnowledgeMCPServer] Processing read_content: {content_id}")
            
            try:
                content_data = self.content_accessor.get_content(content_id)
                
                if content_data:
                    print(f"[KnowledgeMCPServer] Content retrieved: {content_id}")
                else:
                    print(f"[KnowledgeMCPServer] Content not found: {content_id}")
                
                return content_data
                
            except Exception as e:
                print(f"[KnowledgeMCPServer] Error in read_content: {str(e)}")
                return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        MCP Operation: health_check
        
        Returns server health status and statistics.
        
        Returns:
            Health status with server metrics
        """
        with self._lock:
            print("[KnowledgeMCPServer] Processing health_check")
            
            try:
                # Get content accessor health
                accessor_health = self.content_accessor.health_check()
                
                # Add server-level metrics
                server_health = {
                    "server_status": "healthy",
                    "mcp_protocol": "1.0",
                    "total_queries": self._query_count,
                    "timestamp": datetime.now().isoformat(),
                    "content_accessor": accessor_health
                }
                
                print("[KnowledgeMCPServer] Health check complete")
                return server_health
                
            except Exception as e:
                print(f"[KnowledgeMCPServer] Error in health_check: {str(e)}")
                return {
                    "server_status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    def list_operations(self) -> List[Dict[str, Any]]:
        """
        MCP Operation: list_operations
        
        Returns available MCP operations with their schemas.
        
        Returns:
            List of operation definitions
        """
        return [
            {
                "name": "lookup_content",
                "description": "Search knowledge base using keywords and learning objectives",
                "parameters": {
                    "keywords": {"type": "array", "items": {"type": "string"}, "required": True},
                    "learning_objectives": {"type": "array", "items": {"type": "string"}, "required": False},
                    "max_results": {"type": "integer", "default": 10, "required": False}
                },
                "returns": "KnowledgeResponse"
            },
            {
                "name": "read_content", 
                "description": "Retrieve full content by content_id",
                "parameters": {
                    "content_id": {"type": "string", "required": True}
                },
                "returns": "ContentData"
            },
            {
                "name": "health_check",
                "description": "Check server health and statistics", 
                "parameters": {},
                "returns": "HealthStatus"
            }
        ]
    
    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        MCP Operation: get_schemas
        
        Returns JSON schemas for all data types used by this MCP server.
        
        Returns:
            Dictionary of schema definitions
        """
        return {
            "KnowledgeResponse": {
                "type": "object",
                "properties": {
                    "query_id": {"type": "string"},
                    "total_matches": {"type": "integer"},
                    "content_matches": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ContentMatch"}
                    }
                },
                "required": ["query_id", "total_matches", "content_matches"]
            },
            "ContentMatch": {
                "type": "object", 
                "properties": {
                    "content_id": {"type": "string"},
                    "title": {"type": "string"},
                    "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "content_preview": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "content_type": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "required": ["content_id", "title", "relevance_score", "content_preview"]
            },
            "ContentData": {
                "type": "object",
                "properties": {
                    "content_id": {"type": "string"},
                    "full_content": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["content_id", "full_content", "metadata"]
            },
            "HealthStatus": {
                "type": "object",
                "properties": {
                    "server_status": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "content_accessor": {"type": "object"}
                },
                "required": ["server_status", "timestamp"]
            }
        }


# Convenience function for initializing the MCP server
def create_knowledge_mcp_server(output_base_path: str = "output") -> KnowledgeMCPServer:
    """
    Factory function to create a configured Knowledge MCP Server.
    
    Args:
        output_base_path: Path to training manager output directory
        
    Returns:
        Configured KnowledgeMCPServer instance
    """
    return KnowledgeMCPServer(output_base_path)