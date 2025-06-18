"""
Tests for Knowledge Bridge MCP Interface

Tests the MCP operations and integration with content accessor.

Author: Sprint 1 Development Team
Reference: US-001 Knowledge Database MCP Interface
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.knowledge_bridge.mcp_interface import KnowledgeMCPServer, create_knowledge_mcp_server
from src.knowledge_bridge.content_accessor import ContentAccessor


class TestKnowledgeMCPServer:
    """Test suite for Knowledge MCP Server"""
    
    @pytest.fixture
    def mock_training_data(self):
        """Create mock training manager output for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create mock course structure
        course_dir = Path(temp_dir) / "test_course"
        metadata_dir = course_dir / "metadata" 
        transcripts_dir = course_dir / "cleaned_transcripts"
        
        metadata_dir.mkdir(parents=True)
        transcripts_dir.mkdir(parents=True)
        
        # Create mock index.json
        mock_index = {
            "course_title": "Test AI Course",
            "modules": [
                {
                    "module_id": "module_001",
                    "title": "Introduction to Machine Learning",
                    "summary": "Covers basic ML concepts, algorithms, and applications",
                    "keywords": ["machine learning", "algorithms", "data science"],
                    "tags": ["beginner", "ml", "introduction"],
                    "word_count": 2500,
                    "estimated_duration_minutes": 45
                },
                {
                    "module_id": "module_002", 
                    "title": "Deep Learning Fundamentals",
                    "summary": "Neural networks, backpropagation, and deep learning frameworks",
                    "keywords": ["deep learning", "neural networks", "tensorflow"],
                    "tags": ["intermediate", "dl", "frameworks"],
                    "word_count": 3200,
                    "estimated_duration_minutes": 60
                }
            ]
        }
        
        with open(metadata_dir / "index.json", 'w') as f:
            json.dump(mock_index, f)
        
        # Create mock transcript files
        ml_content = """# Introduction to Machine Learning

## Overview
Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.

## Key Concepts
- Supervised learning
- Unsupervised learning  
- Reinforcement learning

## Applications
- Image recognition
- Natural language processing
- Recommendation systems
"""
        
        dl_content = """# Deep Learning Fundamentals

## Neural Networks
Neural networks are the foundation of deep learning, inspired by biological neurons.

## Backpropagation
The backpropagation algorithm is used to train neural networks by computing gradients.

## Frameworks
- TensorFlow
- PyTorch
- Keras
"""
        
        with open(transcripts_dir / "module_001.md", 'w') as f:
            f.write(ml_content)
        
        with open(transcripts_dir / "module_002.md", 'w') as f:
            f.write(dl_content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_mcp_server_initialization(self, mock_training_data):
        """Test MCP server initializes correctly"""
        server = KnowledgeMCPServer(mock_training_data)
        assert server is not None
        assert server.content_accessor is not None
    
    def test_factory_function(self, mock_training_data):
        """Test factory function creates server correctly"""
        server = create_knowledge_mcp_server(mock_training_data)
        assert isinstance(server, KnowledgeMCPServer)
    
    def test_lookup_content_basic(self, mock_training_data):
        """Test basic lookup_content operation"""
        server = KnowledgeMCPServer(mock_training_data)
        
        # Search for machine learning content
        response = server.lookup_content(keywords=["machine learning"])
        
        assert "query_id" in response
        assert "total_matches" in response
        assert "content_matches" in response
        assert response["total_matches"] >= 1
        
        # Check first match has required fields
        if response["content_matches"]:
            match = response["content_matches"][0]
            assert "content_id" in match
            assert "title" in match
            assert "relevance_score" in match
            assert "content_preview" in match
            assert "metadata" in match
    
    def test_lookup_content_with_learning_objectives(self, mock_training_data):
        """Test lookup_content with learning objectives"""
        server = KnowledgeMCPServer(mock_training_data)
        
        response = server.lookup_content(
            keywords=["algorithms"],
            learning_objectives=["Learn basic machine learning concepts"]
        )
        
        assert response["total_matches"] >= 0
        assert "query_id" in response
    
    def test_lookup_content_no_matches(self, mock_training_data):
        """Test lookup_content with keywords that don't match"""
        server = KnowledgeMCPServer(mock_training_data)
        
        response = server.lookup_content(keywords=["quantum computing", "blockchain"])
        
        assert response["total_matches"] == 0
        assert response["content_matches"] == []
    
    def test_read_content_valid_id(self, mock_training_data):
        """Test read_content with valid content_id"""
        server = KnowledgeMCPServer(mock_training_data)
        
        content_data = server.read_content("test_course:module_001")
        
        assert content_data is not None
        assert "content_id" in content_data
        assert "full_content" in content_data
        assert "metadata" in content_data
        assert content_data["content_id"] == "test_course:module_001"
        assert "Machine learning" in content_data["full_content"]
    
    def test_read_content_invalid_id(self, mock_training_data):
        """Test read_content with invalid content_id"""
        server = KnowledgeMCPServer(mock_training_data)
        
        content_data = server.read_content("invalid_course:invalid_module")
        
        assert content_data is None
    
    def test_read_content_malformed_id(self, mock_training_data):
        """Test read_content with malformed content_id"""
        server = KnowledgeMCPServer(mock_training_data)
        
        content_data = server.read_content("malformed_id_without_colon")
        
        assert content_data is None
    
    def test_health_check(self, mock_training_data):
        """Test health_check operation"""
        server = KnowledgeMCPServer(mock_training_data)
        
        health = server.health_check()
        
        assert "server_status" in health
        assert "mcp_protocol" in health
        assert "total_queries" in health
        assert "timestamp" in health
        assert "content_accessor" in health
        assert health["server_status"] == "healthy"
    
    def test_list_operations(self, mock_training_data):
        """Test list_operations returns correct operation definitions"""
        server = KnowledgeMCPServer(mock_training_data)
        
        operations = server.list_operations()
        
        assert len(operations) == 3
        operation_names = [op["name"] for op in operations]
        assert "lookup_content" in operation_names
        assert "read_content" in operation_names
        assert "health_check" in operation_names
    
    def test_get_schemas(self, mock_training_data):
        """Test get_schemas returns valid JSON schemas"""
        server = KnowledgeMCPServer(mock_training_data)
        
        schemas = server.get_schemas()
        
        assert "KnowledgeResponse" in schemas
        assert "ContentMatch" in schemas
        assert "ContentData" in schemas
        assert "HealthStatus" in schemas
        
        # Validate schema structure
        knowledge_response_schema = schemas["KnowledgeResponse"]
        assert "type" in knowledge_response_schema
        assert "properties" in knowledge_response_schema
        assert "required" in knowledge_response_schema
    
    def test_thread_safety(self, mock_training_data):
        """Test concurrent access to MCP server"""
        import threading
        import time
        
        server = KnowledgeMCPServer(mock_training_data)
        results = []
        errors = []
        
        def concurrent_lookup(thread_id):
            try:
                response = server.lookup_content(keywords=[f"test_{thread_id}", "machine"])
                results.append((thread_id, response))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_lookup, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent access: {errors}"
        assert len(results) == 5
        
        # Verify each thread got a response
        for thread_id, response in results:
            assert "query_id" in response
            assert "total_matches" in response


class TestContentAccessor:
    """Test suite for Content Accessor"""
    
    @pytest.fixture
    def mock_training_data(self):
        """Create mock training manager output for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create mock course structure
        course_dir = Path(temp_dir) / "test_course"
        metadata_dir = course_dir / "metadata" 
        transcripts_dir = course_dir / "cleaned_transcripts"
        
        metadata_dir.mkdir(parents=True)
        transcripts_dir.mkdir(parents=True)
        
        # Create mock index.json
        mock_index = {
            "course_title": "Test AI Course",
            "modules": [
                {
                    "module_id": "module_001",
                    "title": "Introduction to Machine Learning",
                    "summary": "Covers basic ML concepts, algorithms, and applications",
                    "keywords": ["machine learning", "algorithms", "data science"],
                    "tags": ["beginner", "ml", "introduction"],
                    "word_count": 2500,
                    "estimated_duration_minutes": 45
                }
            ]
        }
        
        with open(metadata_dir / "index.json", 'w') as f:
            json.dump(mock_index, f)
        
        # Create mock transcript files
        ml_content = """# Introduction to Machine Learning
Machine learning is a subset of artificial intelligence."""
        
        with open(transcripts_dir / "module_001.md", 'w') as f:
            f.write(ml_content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_content_accessor_initialization(self, mock_training_data):
        """Test content accessor initializes correctly"""
        accessor = ContentAccessor(mock_training_data)
        assert accessor is not None
        assert accessor.bridge is not None
    
    def test_get_by_keywords(self, mock_training_data):
        """Test keyword search functionality"""
        accessor = ContentAccessor(mock_training_data)
        
        results = accessor.get_by_keywords(["machine learning"])
        
        assert len(results) >= 1
        result = results[0]
        assert "content_id" in result
        assert "title" in result
        assert "relevance_score" in result
        assert 0 <= result["relevance_score"] <= 1
    
    def test_get_content(self, mock_training_data):
        """Test content retrieval by ID"""
        accessor = ContentAccessor(mock_training_data)
        
        content = accessor.get_content("test_course:module_001")
        
        assert content is not None
        assert content["content_id"] == "test_course:module_001"
        assert "Machine learning" in content["full_content"]
    
    def test_health_check_accessor(self, mock_training_data):
        """Test content accessor health check"""
        accessor = ContentAccessor(mock_training_data)
        
        health = accessor.health_check()
        
        assert "status" in health
        assert "available_courses" in health
        assert "total_modules" in health
        assert health["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__])