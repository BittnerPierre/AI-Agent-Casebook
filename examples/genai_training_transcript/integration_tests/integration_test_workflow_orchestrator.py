#!/usr/bin/env python3
"""
Integration test for WorkflowOrchestrator (US-006)

Tests the complete workflow orchestrator integration with a sample syllabus
to verify end-to-end functionality works correctly.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcript_generator.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig


async def main():
    """Run integration test for WorkflowOrchestrator"""
    
    print("🚀 Starting WorkflowOrchestrator Integration Test")
    print("=" * 60)
    
    # Create test syllabus
    test_syllabus = {
        "course_title": "Introduction to Testing Frameworks",
        "course_description": "A comprehensive course covering testing frameworks and methodologies",
        "sections": [
            {
                "section_id": "testing_fundamentals",
                "title": "Testing Fundamentals",
                "learning_objectives": [
                    "Understand basic testing principles",
                    "Learn about different types of testing"
                ],
                "key_topics": [
                    "unit testing",
                    "testing principles", 
                    "test automation"
                ],
                "estimated_duration": "45 minutes"
            }
        ]
    }
    
    # Create configuration for test
    config = WorkflowConfig(
        output_dir="test_output",
        research_output_dir="test_research_notes", 
        quality_output_dir="test_quality_issues",
        overwrite_existing=True,
        timeout_per_phase=60,  # 1 minute per phase
        continue_on_errors=True,
        enable_progress_tracking=True
    )
    
    print(f"📋 Test Configuration:")
    print(f"   Output Directory: {config.output_dir}")
    print(f"   Timeout per Phase: {config.timeout_per_phase}s")
    print()
    
    # Create WorkflowOrchestrator
    orchestrator = WorkflowOrchestrator(config)
    
    print("🔍 Performing Health Check...")
    health = await orchestrator.health_check()
    print(f"   Status: {health.get('orchestrator_status', 'unknown')}")
    print()
    
    try:
        print("⚡ Executing Complete Pipeline...")
        
        # Execute the complete pipeline
        result = await orchestrator.execute_pipeline(test_syllabus)
        
        print("📊 Pipeline Execution Results:")
        print("=" * 40)
        print(f"✅ Success: {result.success}")
        print(f"⏱️  Execution Time: {result.execution_time:.2f} seconds")
        
        if result.errors:
            print(f"⚠️  Errors/Warnings ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                print(f"   {i}. {error}")
        
        print()
        print("=" * 60)
        
        if result.success:
            print("✅ Integration Test PASSED - WorkflowOrchestrator working correctly!")
            return 0
        else:
            print("❌ Integration Test FAILED - WorkflowOrchestrator encountered errors")
            return 1
        
    except Exception as e:
        print(f"💥 Integration Test CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)