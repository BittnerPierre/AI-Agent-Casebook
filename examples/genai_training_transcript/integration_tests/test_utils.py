"""
Utilities for integration tests with strict success criteria
"""

import re
from typing import Any, Dict, List, Tuple


def evaluate_critical_test_success(result: Any, success_criteria: Dict[str, bool], critical_keys: List[str] = None) -> Tuple[bool, str]:
    """
    Strict evaluation with mandatory critical criteria
    
    Args:
        result: Test result object (may have returncode attribute)
        success_criteria: Dictionary of criteria name -> pass/fail boolean
        critical_keys: List of criteria that must pass (default: cli_exit_success, core_functionality)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if critical_keys is None:
        critical_keys = ["cli_exit_success", "core_functionality"]
    
    # 1. Exit code check - immediate failure if process failed
    if hasattr(result, 'returncode') and result.returncode != 0:
        print("❌ CRITICAL: Process failed - Cannot proceed")
        return False, "Process exit failure"
    
    # 2. Critical criteria must pass - no exceptions
    for key in critical_keys:
        if key in success_criteria and not success_criteria[key]:
            print(f"❌ CRITICAL: {key} failed")
            return False, f"Critical criterion failed: {key}"
    
    # 3. Higher threshold for non-critical (95% instead of 80%)
    passed = sum(success_criteria.values())
    total = len(success_criteria)
    success_rate = (passed / total) * 100
    
    is_success = success_rate >= 95.0
    message = f"Success rate: {success_rate:.1f}%"
    
    if not is_success:
        print(f"❌ Insufficient success rate: {success_rate:.1f}% (required: 95.0%)")
    
    return is_success, message


def generate_section_id(title: str) -> str:
    """Generate clean section_id from title"""
    section_id = title.lower()
    section_id = re.sub(r'[^\w\s-]', '', section_id)  # Remove punctuation
    section_id = re.sub(r'[-\s]+', '_', section_id)   # Spaces/hyphens → underscore
    return section_id.strip('_')


def validate_section_schema(section: Dict[str, Any]) -> Dict[str, Any]:
    """Validate section has required fields for WorkflowOrchestrator"""
    required_fields = ["section_id", "title", "learning_objectives"]
    for field in required_fields:
        if field not in section:
            raise ValueError(f"Missing required field: {field}")
    return section


def transform_syllabus_structure(syllabus_modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform simple syllabus to WorkflowOrchestrator schema
    
    Args:
        syllabus_modules: List of modules from load_syllabus() with structure:
            [{"title": "...", "objectives": [...]}]
            
    Returns:
        List of sections with WorkflowOrchestrator compatible structure:
        [{"section_id": "...", "title": "...", "learning_objectives": [...], ...}]
    """
    sections = []
    for i, module in enumerate(syllabus_modules):
        # Generate section_id from title
        section_id = generate_section_id(module["title"])
        
        section = {
            "section_id": section_id,
            "title": module["title"],
            "learning_objectives": module.get("objectives", []),  # mapping: objectives → learning_objectives
            "key_topics": [],  # TODO: extract from syllabus if available
            "estimated_duration": "45 minutes"  # reasonable default value
        }
        
        # Validate the section structure
        validate_section_schema(section)
        sections.append(section)
    
    return sections


def test_syllabus_transformation():
    """Test that syllabus transformation works correctly"""
    mock_modules = [
        {
            "title": "Test Module 1", 
            "objectives": ["Objective 1", "Objective 2"]
        },
        {
            "title": "Advanced AI Systems", 
            "objectives": ["Learn AI fundamentals"]
        }
    ]
    
    sections = transform_syllabus_structure(mock_modules)
    
    # Validate transformation
    assert len(sections) == 2
    assert sections[0]["section_id"] == "test_module_1"
    assert sections[0]["learning_objectives"] == ["Objective 1", "Objective 2"]
    assert sections[1]["section_id"] == "advanced_ai_systems"
    assert sections[1]["learning_objectives"] == ["Learn AI fundamentals"]
    
    # Validate required fields
    for section in sections:
        validate_section_schema(section)
    
    print("✅ Syllabus transformation test passed")
    return True


if __name__ == "__main__":
    # Run self-test
    test_syllabus_transformation() 