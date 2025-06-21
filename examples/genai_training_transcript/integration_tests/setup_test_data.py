#!/usr/bin/env python3
"""
Integration Test Data Setup Script

This script sets up the test environment for integration tests by:
1. Creating lightweight smoke test data in the expected format
2. Generating minimal training manager outputs for testing
3. Ensuring knowledge bridge can find test data

Usage:
    python integration_tests/setup_test_data.py
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any


def create_mock_training_data(base_dir: Path) -> None:
    """Create mock training manager outputs for integration tests."""
    print("🔧 Setting up mock training manager data...")
    
    # Smoke test files mapping
    smoke_tests = {
        "prompt_engineering_for_developers": "Prompt_Engineering_Smoke_Test.txt",
        "advanced_retrieval_for_ai": "Advanced_Retrieval_Smoke_Test.txt", 
        "multi_ai_agent_systems": "Multi_Agent_Smoke_Test.txt",
        "building_systems_with_the_chatgpt_api": "Building_Systems_Smoke_Test.txt"
    }
    
    smoke_dir = base_dir / "data" / "training_courses" / "smoke_tests"
    knowledge_db_dir = base_dir / "knowledge_db"  # Use knowledge_db instead of output
    
    for course_id, smoke_file in smoke_tests.items():
        smoke_path = smoke_dir / smoke_file
        if not smoke_path.exists():
            print(f"⚠️  Smoke test file not found: {smoke_path}")
            continue
            
        # Read smoke test content
        with open(smoke_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create course directory structure in knowledge_db
        course_dir = knowledge_db_dir / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory
        metadata_dir = course_dir / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        
        # Create cleaned_transcripts directory
        transcripts_dir = course_dir / "cleaned_transcripts"
        transcripts_dir.mkdir(exist_ok=True)
        
        # Create cleaned transcript file
        transcript_file = transcripts_dir / f"{course_id}.md"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create mock metadata index
        module_data = {
            "module_id": course_id,
            "title": course_id.replace('_', ' ').title(),
            "summary": f"Test module for {course_id}",
            "keywords": [course_id.replace('_', ' ')],
            "tags": ["integration-test", "smoke-test"],
            "word_count": len(content.split()),
            "estimated_duration_minutes": 10,
            "transcript_path": str(transcript_file.relative_to(base_dir))
        }
        
        index_data = {
            "course_id": course_id,
            "course_title": course_id.replace('_', ' ').title(),
            "description": f"Integration test course for {course_id}",
            "modules": [module_data],
            "created_at": "2025-06-20T23:00:00Z",
            "total_modules": 1,
            "total_duration_minutes": 10
        }
        
        # Write metadata index
        index_file = metadata_dir / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
        
        print(f"✅ Created mock data for {course_id}")


def setup_integration_test_environment(base_dir: Path) -> None:
    """Set up complete integration test environment."""
    print("🚀 Setting up integration test environment...")
    
    # Ensure required directories exist (separate knowledge_db and generated_content)
    required_dirs = [
        "knowledge_db",
        "generated_content",
        "generated_content/research_notes", 
        "generated_content/chapter_drafts",
        "generated_content/quality_issues",
        "generated_content/logs"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    # Create mock training data
    create_mock_training_data(base_dir)
    
    print("🎉 Integration test environment ready!")


def main():
    """Main setup function."""
    # Get base directory (examples/genai_training_transcript)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print(f"📁 Base directory: {base_dir}")
    
    # Setup test environment
    setup_integration_test_environment(base_dir)
    
    print("\n✅ Integration test data setup complete!")
    print("You can now run integration tests:")
    print("  poetry run python integration_tests/integration_test_cli_end_to_end.py")


if __name__ == "__main__":
    main()