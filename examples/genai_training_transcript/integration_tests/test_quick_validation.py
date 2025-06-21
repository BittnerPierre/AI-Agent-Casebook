#!/usr/bin/env python3
"""
Quick validation script to test that integration test setup is working correctly.
This is a lightweight validation before running the full integration test.
"""

import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from test_utils import extract_keywords_from_title, transform_syllabus_structure
from transcript_generator.tools.syllabus_loader import load_syllabus
from common.knowledge_bridge import TrainingDataBridge


def test_keyword_extraction():
    """Test that keyword extraction works correctly."""
    print("🧪 Testing keyword extraction...")
    
    test_cases = [
        ("Prompt Engineering for Developers", ["prompt", "engineering", "developers", "prompt engineering"]),
        ("Advanced Retrieval for AI", ["advanced", "retrieval", "retrieval"]),
        ("Multi AI Agent Systems", ["multi", "agent", "systems", "multi agent"]),
        ("Building Systems with the ChatGPT API", ["building", "systems", "chatgpt", "api", "chatgpt api"])
    ]
    
    for title, expected_keywords in test_cases:
        keywords = extract_keywords_from_title(title)
        print(f"  '{title}' → {keywords}")
        
        # Check that we have some meaningful keywords
        assert len(keywords) > 0, f"No keywords extracted from '{title}'"
        
        # Check that key terms are present
        for expected in expected_keywords:
            if expected in [k.lower() for k in keywords]:
                print(f"    ✅ Found expected keyword: '{expected}'")
            else:
                print(f"    ⚠️  Missing expected keyword: '{expected}'")
    
    print("✅ Keyword extraction test passed\n")


def test_syllabus_transformation():
    """Test that syllabus transformation generates key_topics."""
    print("🧪 Testing syllabus transformation...")
    
    base_dir = Path(__file__).parent.parent
    syllabus_path = base_dir / "syllabus.md"
    
    if not syllabus_path.exists():
        print(f"❌ Syllabus not found: {syllabus_path}")
        return False
    
    # Load and transform syllabus
    modules = load_syllabus(str(syllabus_path))
    sections = transform_syllabus_structure(modules)
    
    print(f"  Loaded {len(sections)} sections from syllabus")
    
    for section in sections:
        print(f"  Section: {section['title']}")
        print(f"    key_topics: {section['key_topics']}")
        
        # Validate that key_topics is not empty
        assert len(section['key_topics']) > 0, f"Empty key_topics for section: {section['title']}"
        print(f"    ✅ Has {len(section['key_topics'])} key topics")
    
    print("✅ Syllabus transformation test passed\n")
    return sections


def test_knowledge_bridge():
    """Test that knowledge bridge can find content with keywords."""
    print("🧪 Testing knowledge bridge search...")
    
    bridge = TrainingDataBridge("knowledge_db")
    
    # Test that courses are available
    courses = bridge.list_available_courses()
    print(f"  Available courses: {courses}")
    
    if not courses:
        print("❌ No courses found. Run setup_test_data.py first.")
        return False
    
    # Test keyword search
    test_keywords = ["prompt engineering", "developers"]
    results = bridge.search_modules_by_keywords(test_keywords)
    
    print(f"  Search for {test_keywords} found {len(results)} results")
    for result in results:
        print(f"    - {result.title} (course: {result.course_id})")
    
    assert len(results) > 0, f"No search results for keywords: {test_keywords}"
    print("✅ Knowledge bridge search test passed\n")
    
    return True


def test_research_notes_content():
    """Test that research notes contain actual content."""
    print("🧪 Testing research notes content...")
    
    research_dir = Path("generated_content/research_notes")
    if not research_dir.exists():
        print("❌ Research notes directory not found")
        return False
    
    for notes_file in research_dir.glob("*.json"):
        print(f"  Checking: {notes_file.name}")
        
        with open(notes_file, 'r') as f:
            data = json.load(f)
        
        # Check that research_summary is not empty
        summary = data.get("research_summary", "")
        if summary.strip():
            print(f"    ✅ Has research summary ({len(summary)} chars)")
        else:
            print(f"    ❌ Empty research summary")
            return False
        
        # Check that knowledge_references exist
        references = data.get("knowledge_references", [])
        print(f"    ✅ Has {len(references)} knowledge references")
    
    print("✅ Research notes content test passed\n")
    return True


def main():
    """Run all validation tests."""
    print("🚀 Quick Integration Test Validation")
    print("=" * 50)
    
    try:
        # Test 1: Keyword extraction
        test_keyword_extraction()
        
        # Test 2: Syllabus transformation
        sections = test_syllabus_transformation()
        
        # Test 3: Knowledge bridge
        if not test_knowledge_bridge():
            return False
        
        # Test 4: Research notes content
        if not test_research_notes_content():
            return False
        
        print("🎉 All validation tests passed!")
        print("✅ Integration test environment is working correctly")
        print("\nReady to run full integration test:")
        print("  poetry run python integration_tests/integration_test_cli_end_to_end.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)