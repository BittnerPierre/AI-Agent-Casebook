"""
Tests for Training Manager Content Accessor (US-002)

Comprehensive test suite for ContentAccessor class in training_manager.
Tests keyword search, content retrieval, thread safety, and integration.

Author: Claude Code - Sprint 1 Week 1  
Reference: US-002 Operational Training Manager Content Access
"""

import pytest
import tempfile
import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

from training_manager.content_accessor import ContentAccessor


class TestContentAccessor:
    """Test suite for ContentAccessor class"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory with sample data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample course structure
            course_dir = Path(temp_dir) / "TEST_COURSE"
            metadata_dir = course_dir / "metadata"
            transcripts_dir = course_dir / "cleaned_transcripts"
            
            metadata_dir.mkdir(parents=True)
            transcripts_dir.mkdir(parents=True)
            
            # Create sample index.json
            index_data = {
                "course_id": "TEST_COURSE",
                "course_title": "Test Course",
                "modules": [
                    {
                        "module_id": "test_module_1",
                        "title": "Introduction to Testing",
                        "summary": "This module covers basic testing concepts and methodologies.",
                        "keywords": ["testing", "unit tests", "automation"],
                        "tags": ["programming", "quality assurance"]
                    },
                    {
                        "module_id": "test_module_2", 
                        "title": "Advanced Test Strategies",
                        "summary": "Advanced testing strategies including integration and performance testing.",
                        "keywords": ["integration", "performance", "strategies"],
                        "tags": ["advanced", "testing"]
                    }
                ]
            }
            
            with open(metadata_dir / "index.json", 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            # Create sample transcript files
            transcript_1 = """---
**Introduction to Testing**

Testing is a fundamental part of software development. Unit tests help ensure individual components work correctly.

Key concepts:
- Unit testing principles
- Test automation
- Quality assurance practices
"""
            
            transcript_2 = """---
**Advanced Test Strategies**

This module explores sophisticated testing approaches including integration testing and performance optimization.

Topics covered:
- Integration testing methodologies  
- Performance testing strategies
- Advanced test frameworks
"""
            
            with open(transcripts_dir / "test_module_1.md", 'w', encoding='utf-8') as f:
                f.write(transcript_1)
                
            with open(transcripts_dir / "test_module_2.md", 'w', encoding='utf-8') as f:
                f.write(transcript_2)
            
            yield temp_dir
    
    @pytest.fixture
    def content_accessor(self, temp_output_dir):
        """Create ContentAccessor instance with test data"""
        return ContentAccessor(temp_output_dir)
    
    def test_initialization(self, temp_output_dir):
        """Test ContentAccessor initialization"""
        accessor = ContentAccessor(temp_output_dir)
        
        assert accessor.output_path == Path(temp_output_dir)
        assert accessor._lock is not None
        assert isinstance(accessor._content_cache, dict)
        assert isinstance(accessor._metadata_cache, dict)
    
    def test_list_available_courses(self, content_accessor):
        """Test listing available courses"""
        courses = content_accessor.list_available_courses()
        
        assert isinstance(courses, list)
        assert "TEST_COURSE" in courses
        assert len(courses) == 1
    
    def test_health_check(self, content_accessor):
        """Test health check functionality"""
        health = content_accessor.health_check()
        
        assert health["status"] == "healthy"
        assert health["available_courses"] == 1
        assert health["total_modules"] == 2
        assert health["content_cache_size"] == 0  # Initially empty
        assert health["metadata_cache_size"] >= 0  # May be populated during health check
        assert "timestamp" in health
    
    def test_get_by_keywords_basic_search(self, content_accessor):
        """Test basic keyword search functionality"""
        # Search for "testing" keyword
        results = content_accessor.get_by_keywords(["testing"])
        
        assert isinstance(results, list)
        assert len(results) == 2  # Both modules should match
        
        # Check result structure
        for result in results:
            assert "content_id" in result
            assert "title" in result
            assert "relevance_score" in result
            assert "content_preview" in result
            assert "metadata" in result
            
        # Results should be sorted by relevance
        assert results[0]["relevance_score"] >= results[1]["relevance_score"]
    
    def test_get_by_keywords_specific_search(self, content_accessor):
        """Test specific keyword search"""
        # Search for "integration" - should only match module 2
        results = content_accessor.get_by_keywords(["integration"])
        
        assert len(results) == 1
        assert "test_module_2" in results[0]["content_id"]
        assert results[0]["relevance_score"] > 0
    
    def test_get_by_keywords_multiple_keywords(self, content_accessor):
        """Test search with multiple keywords"""
        results = content_accessor.get_by_keywords(["testing", "advanced"])
        
        assert len(results) >= 1
        # Module 2 should score higher due to "advanced" in title
        assert any("test_module_2" in result["content_id"] for result in results)
    
    def test_get_by_keywords_max_results(self, content_accessor):
        """Test max_results parameter"""
        results = content_accessor.get_by_keywords(["testing"], max_results=1)
        
        assert len(results) == 1
    
    def test_get_by_keywords_empty_keywords(self, content_accessor):
        """Test search with empty keywords"""
        results = content_accessor.get_by_keywords([])
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_get_by_keywords_no_matches(self, content_accessor):
        """Test search with no matching keywords"""
        results = content_accessor.get_by_keywords(["nonexistent", "keyword"])
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_get_content_valid_id(self, content_accessor):
        """Test getting content with valid content ID"""
        content = content_accessor.get_content("TEST_COURSE:test_module_1")
        
        assert content is not None
        assert content["content_id"] == "TEST_COURSE:test_module_1"
        assert "full_content" in content
        assert "metadata" in content
        
        # Check full content
        assert "Introduction to Testing" in content["full_content"]
        assert "Unit tests help ensure" in content["full_content"]
        
        # Check metadata
        metadata = content["metadata"]
        assert metadata["title"] == "Introduction to Testing"
        assert metadata["source"] == "TEST_COURSE"
        assert metadata["content_type"] == "training_transcript"
        assert "testing" in metadata["keywords"]
    
    def test_get_content_invalid_id_format(self, content_accessor):
        """Test getting content with invalid ID format"""
        content = content_accessor.get_content("invalid_format")
        
        assert content is None
    
    def test_get_content_nonexistent_course(self, content_accessor):
        """Test getting content from nonexistent course"""
        content = content_accessor.get_content("NONEXISTENT:module")
        
        assert content is None
    
    def test_get_content_nonexistent_module(self, content_accessor):
        """Test getting content from nonexistent module"""
        content = content_accessor.get_content("TEST_COURSE:nonexistent_module")
        
        assert content is None
    
    def test_content_caching(self, content_accessor):
        """Test content caching functionality"""
        # First request
        content1 = content_accessor.get_content("TEST_COURSE:test_module_1")
        assert content1 is not None
        
        # Check cache is populated
        assert len(content_accessor._content_cache) == 1
        
        # Second request should use cache
        content2 = content_accessor.get_content("TEST_COURSE:test_module_1")
        assert content2 is not None
        assert content1["full_content"] == content2["full_content"]
    
    def test_metadata_caching(self, content_accessor):
        """Test metadata caching functionality"""
        # First search should populate metadata cache
        results = content_accessor.get_by_keywords(["testing"])
        assert len(results) >= 1
        
        # Check metadata cache is populated
        assert len(content_accessor._metadata_cache) > 0
        
        # Second search should use cache
        results2 = content_accessor.get_by_keywords(["testing"])
        assert len(results) == len(results2)
    
    def test_thread_safety(self, content_accessor):
        """Test thread-safe access for concurrent queries"""
        results = []
        errors = []
        
        def search_worker():
            try:
                result = content_accessor.get_by_keywords(["testing"])
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        def content_worker():
            try:
                result = content_accessor.get_content("TEST_COURSE:test_module_1")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=search_worker))
            threads.append(threading.Thread(target=content_worker))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10  # 5 search + 5 content results
    
    def test_relevance_scoring(self, content_accessor):
        """Test relevance scoring algorithm"""
        # Test title match vs keyword match
        title_match = content_accessor.get_by_keywords(["Introduction"])
        keyword_match = content_accessor.get_by_keywords(["automation"])
        
        assert len(title_match) >= 1
        assert len(keyword_match) >= 1
        
        # Title matches should generally score higher (0.4 weight vs 0.3 for keywords)
        title_result = next((r for r in title_match if "test_module_1" in r["content_id"]), None)
        assert title_result is not None
        assert title_result["relevance_score"] > 0
    
    def test_content_preview_generation(self, content_accessor):
        """Test content preview generation"""
        results = content_accessor.get_by_keywords(["testing"])
        
        assert len(results) >= 1
        preview = results[0]["content_preview"]
        
        assert "Title:" in preview
        assert "Summary:" in preview
        assert "Keywords:" in preview
        assert len(preview) > 0
    
    def test_empty_output_directory(self):
        """Test behavior with empty output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            accessor = ContentAccessor(temp_dir)
            
            # Should handle empty directory gracefully
            courses = accessor.list_available_courses()
            assert courses == []
            
            health = accessor.health_check()
            assert health["status"] == "healthy"
            assert health["available_courses"] == 0
            assert health["total_modules"] == 0
    
    def test_nonexistent_output_directory(self):
        """Test behavior with nonexistent output directory"""
        accessor = ContentAccessor("/nonexistent/path")
        
        # Should handle gracefully
        courses = accessor.list_available_courses()
        assert courses == []
        
        health = accessor.health_check()
        assert health["status"] == "healthy"
        assert health["available_courses"] == 0


class TestContentAccessorIntegration:
    """Integration tests for ContentAccessor with training_manager"""
    
    def test_integration_with_training_manager_output(self):
        """Test integration with actual training_manager output format"""
        # This test uses the actual CHROMA course data if available
        accessor = ContentAccessor("output")
        
        courses = accessor.list_available_courses()
        if "CHROMA" in courses:
            # Test with real data
            health = accessor.health_check()
            assert health["status"] == "healthy"
            assert health["available_courses"] >= 1
            
            # Test search
            results = accessor.get_by_keywords(["Chroma", "RAG"])
            assert isinstance(results, list)
            
            # Test content retrieval if modules exist
            if health["total_modules"] > 0:
                # Get first module
                all_content = accessor._get_all_content_metadata()
                if all_content:
                    first_content_id = list(all_content.keys())[0]
                    content = accessor.get_content(first_content_id)
                    assert content is not None
                    assert "full_content" in content
                    assert "metadata" in content


# Performance tests
class TestContentAccessorPerformance:
    """Performance tests for ContentAccessor"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory with sample data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample course structure
            course_dir = Path(temp_dir) / "TEST_COURSE"
            metadata_dir = course_dir / "metadata"
            transcripts_dir = course_dir / "cleaned_transcripts"
            
            metadata_dir.mkdir(parents=True)
            transcripts_dir.mkdir(parents=True)
            
            # Create sample index.json
            index_data = {
                "course_id": "TEST_COURSE",
                "course_title": "Test Course",
                "modules": [
                    {
                        "module_id": "test_module_1",
                        "title": "Introduction to Testing",
                        "summary": "This module covers basic testing concepts and methodologies.",
                        "keywords": ["testing", "unit tests", "automation"],
                        "tags": ["programming", "quality assurance"]
                    }
                ]
            }
            
            with open(metadata_dir / "index.json", 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            # Create sample transcript file
            transcript_1 = "**Introduction to Testing**\n\nTesting is fundamental."
            
            with open(transcripts_dir / "test_module_1.md", 'w', encoding='utf-8') as f:
                f.write(transcript_1)
            
            yield temp_dir
    
    @pytest.fixture
    def content_accessor(self, temp_output_dir):
        """Create ContentAccessor instance with test data for performance tests"""
        return ContentAccessor(temp_output_dir)
    
    def test_search_performance(self, content_accessor):
        """Test search performance with timing"""
        start_time = time.time()
        
        # Perform multiple searches
        for _ in range(10):
            results = content_accessor.get_by_keywords(["testing"])
            assert len(results) >= 0
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete 10 searches in reasonable time (< 1 second)
        assert elapsed < 1.0, f"Search performance too slow: {elapsed:.2f} seconds"
    
    def test_content_retrieval_performance(self, content_accessor):
        """Test content retrieval performance"""
        start_time = time.time()
        
        # Retrieve same content multiple times (should use cache)
        for _ in range(10):
            content = content_accessor.get_content("TEST_COURSE:test_module_1")
            assert content is not None
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete 10 retrievals quickly due to caching (< 0.5 seconds)
        assert elapsed < 0.5, f"Content retrieval performance too slow: {elapsed:.2f} seconds"
    
    def test_export_as_markdown_success(self, content_accessor):
        """Test successful Markdown export with frontmatter"""
        # Export existing content as Markdown
        markdown_content = content_accessor.export_as_markdown("TEST_COURSE:test_module_1")
        
        assert markdown_content is not None
        assert isinstance(markdown_content, str)
        
        # Verify YAML frontmatter structure
        assert markdown_content.startswith("---")
        assert 'title: "Introduction to Testing"' in markdown_content
        assert 'content_id: "TEST_COURSE:test_module_1"' in markdown_content
        assert 'course_id: "TEST_COURSE"' in markdown_content
        assert 'module_id: "test_module_1"' in markdown_content
        assert 'content_type: "training_transcript"' in markdown_content
        
        # Verify keywords and tags are included
        assert 'keywords: ["testing", "unit tests", "automation"]' in markdown_content
        assert 'tags: ["programming", "quality assurance"]' in markdown_content
        
        # Verify summary is included
        assert 'summary: "This module covers basic testing concepts and methodologies."' in markdown_content
        
        # Verify metadata and content separation
        frontmatter_end = markdown_content.find("---", 3)  # Find second ---
        assert frontmatter_end > 0
        
        # Content should follow after frontmatter
        content_start = frontmatter_end + 3
        content_section = markdown_content[content_start:].strip()
        assert content_section.startswith("**Introduction to Testing**")
    
    def test_export_as_markdown_nonexistent_content(self, content_accessor):
        """Test Markdown export for non-existent content"""
        markdown_content = content_accessor.export_as_markdown("NONEXISTENT:module")
        
        assert markdown_content is None
    
    def test_export_as_markdown_thread_safety(self, content_accessor):
        """Test thread safety of Markdown export"""
        results = {}
        
        def export_markdown(thread_id):
            """Export markdown in separate thread"""
            result = content_accessor.export_as_markdown("TEST_COURSE:test_module_1")
            results[thread_id] = result
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=export_markdown, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads got valid results
        assert len(results) == 5
        for thread_id, result in results.items():
            assert result is not None
            assert 'title: "Introduction to Testing"' in result
            assert 'content_id: "TEST_COURSE:test_module_1"' in result
    
    def test_export_as_markdown_special_characters(self, temp_output_dir):
        """Test Markdown export with special characters in content"""
        # Create content with special characters
        course_dir = Path(temp_output_dir) / "SPECIAL_COURSE"
        metadata_dir = course_dir / "metadata"
        transcripts_dir = course_dir / "cleaned_transcripts"
        
        metadata_dir.mkdir(parents=True)
        transcripts_dir.mkdir(parents=True)
        
        # Create index with special characters
        index_data = {
            "course_id": "SPECIAL_COURSE",
            "course_title": "Special Characters Test",
            "modules": [
                {
                    "module_id": "special_module",
                    "title": 'Testing "Quotes" & Special Characters',
                    "summary": "This module\nhas multiple lines\nand \"quotes\" to test escaping.",
                    "keywords": ["special", "characters", "quotes"],
                    "tags": ["testing"]
                }
            ]
        }
        
        with open(metadata_dir / "index.json", "w") as f:
            json.dump(index_data, f)
        
        # Create transcript with special characters
        transcript_content = 'Content with "quotes" and\nmultiple lines\nand special chars!'
        with open(transcripts_dir / "special_module.md", "w") as f:
            f.write(transcript_content)
        
        # Test export
        accessor = ContentAccessor(temp_output_dir)
        markdown_content = accessor.export_as_markdown("SPECIAL_COURSE:special_module")
        
        assert markdown_content is not None
        
        # Verify special characters are properly escaped
        assert 'title: "Testing \\"Quotes\\" & Special Characters"' in markdown_content
        assert 'summary: "This module\\nhas multiple lines\\nand \\"quotes\\" to test escaping."' in markdown_content
        
        # Verify content is preserved
        assert 'Content with "quotes" and\nmultiple lines\nand special chars!' in markdown_content