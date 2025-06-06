#!/usr/bin/env python3
"""
Unit tests for knowledge bridge functionality.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from common.knowledge_bridge import TrainingDataBridge
from common.models import SearchQuery
from transcript_generator.tools.knowledge_retriever import KnowledgeRetriever


def create_test_training_data(base_path: Path):
    """Create sample training data structure for testing."""
    course_id = "TEST001"
    course_path = base_path / course_id
    
    # Create directory structure
    metadata_dir = course_path / "metadata"
    transcripts_dir = course_path / "cleaned_transcripts"
    metadata_dir.mkdir(parents=True)
    transcripts_dir.mkdir(parents=True)
    
    # Create sample index.json
    index_data = {
        "course_id": course_id,
        "course_title": "Test AI Course",
        "modules": [
            {
                "module_id": "intro",
                "title": "Introduction to AI",
                "summary": "Basic concepts of artificial intelligence",
                "keywords": ["AI", "machine learning", "neural networks"],
                "tags": ["beginner", "foundational"]
            },
            {
                "module_id": "advanced",
                "title": "Advanced Techniques",
                "summary": "Deep learning and transformer models",
                "keywords": ["deep learning", "transformers", "GPT"],
                "tags": ["advanced", "technical"]
            }
        ]
    }
    
    with open(metadata_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    # Create sample cleaned transcripts
    intro_content = """# Introduction to AI

## What is Artificial Intelligence?

Artificial Intelligence (AI) is the simulation of human intelligence in machines.
It encompasses machine learning, neural networks, and various algorithms.

## Key Concepts

- Machine Learning: Algorithms that improve through experience
- Neural Networks: Computing systems inspired by biological neural networks
- Deep Learning: ML methods based on artificial neural networks
"""

    advanced_content = """# Advanced AI Techniques

## Deep Learning

Deep learning uses multi-layered neural networks to model and understand complex patterns.

## Transformer Models

Transformers have revolutionized natural language processing:
- GPT (Generative Pre-trained Transformer)
- BERT (Bidirectional Encoder Representations from Transformers)
- T5 (Text-to-Text Transfer Transformer)

These models have enabled breakthrough capabilities in text generation and understanding.
"""
    
    with open(transcripts_dir / "intro.md", "w") as f:
        f.write(intro_content)
    
    with open(transcripts_dir / "advanced.md", "w") as f:
        f.write(advanced_content)
    
    return course_id


def test_training_data_bridge():
    """Test basic bridge functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        course_id = create_test_training_data(base_path)
        
        bridge = TrainingDataBridge(str(base_path))
        
        # Test listing courses
        courses = bridge.list_available_courses()
        assert course_id in courses
        
        # Test getting course metadata
        course = bridge.get_course_metadata(course_id)
        assert course is not None
        assert course.course_id == course_id
        assert course.course_title == "Test AI Course"
        assert len(course.modules) == 2
        
        # Test module metadata
        intro_module = bridge.get_module_metadata(course_id, "intro")
        assert intro_module is not None
        assert intro_module.title == "Introduction to AI"
        assert "AI" in intro_module.keywords
        
        # Test transcript content
        transcript = bridge.get_cleaned_transcript(course_id, "intro")
        assert transcript is not None
        assert "Artificial Intelligence" in transcript


def test_search_functionality():
    """Test search capabilities."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        course_id = create_test_training_data(base_path)
        
        bridge = TrainingDataBridge(str(base_path))
        
        # Test keyword search
        results = bridge.search_modules_by_keywords(["machine learning"], limit=5)
        assert len(results) >= 1
        assert any("machine learning" in ' '.join(m.keywords).lower() for m in results)
        
        # Test structured search
        query = SearchQuery(keywords=["AI"], limit=10)
        search_result = bridge.search_modules(query)
        assert search_result.total_count >= 1
        assert len(search_result.modules) >= 1


@pytest.mark.asyncio
async def test_knowledge_retriever():
    """Test knowledge retriever functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        course_id = create_test_training_data(base_path)
        
        retriever = KnowledgeRetriever(str(base_path))
        
        # Test related content retrieval
        content = await retriever.get_related_content(["AI", "machine learning"])
        assert len(content) >= 1
        assert any("AI" in item["keywords"] for item in content)
        
        # Test course outline
        outline = await retriever.get_course_outline(course_id)
        assert outline is not None
        assert outline["course_id"] == course_id
        assert len(outline["modules"]) == 2
        
        # Test topic search
        search_results = await retriever.search_by_topic(keywords=["neural networks"])
        assert len(search_results) >= 1
        
        # Test available courses
        courses = await retriever.list_available_courses()
        assert len(courses) >= 1
        assert any(c["course_id"] == course_id for c in courses)


def test_bridge_error_handling():
    """Test error handling for missing data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        bridge = TrainingDataBridge(temp_dir)
        
        # Test with non-existent course
        course = bridge.get_course_metadata("NONEXISTENT")
        assert course is None
        
        # Test with non-existent transcript
        transcript = bridge.get_cleaned_transcript("FAKE", "fake_module")
        assert transcript is None
        
        # Test empty directory
        courses = bridge.list_available_courses()
        assert len(courses) == 0