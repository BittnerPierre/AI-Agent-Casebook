#!/usr/bin/env python3
"""
LangSmith Integration Validation Script

This script validates the LangSmith integration setup for US-007 and US-012.
It checks configuration, tests basic functionality, and provides setup guidance.

Usage:
    python scripts/validate_langsmith.py [--api-key YOUR_KEY] [--project PROJECT_NAME]
    
Environment Variables:
    LANGSMITH_API_KEY: Your LangSmith API key
    LANGSMITH_PROJECT: Project name (default: story-ops)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from evaluation import (
        EvaluationLogger,
        LangSmithConfig,
        LangSmithIntegration,
        validate_environment,
    )
    from transcript_generator.editorial_finalizer import ChapterDraft
    from transcript_generator.workflow_orchestrator import WorkflowResult
except ImportError as e:
    print(f"❌ Failed to import evaluation modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


async def validate_evaluation_logger(api_key: str | None = None):
    """Test EvaluationLogger functionality"""
    print("\n📊 Testing EvaluationLogger...")
    
    try:
        logger = EvaluationLogger(
            api_key=api_key,
            project_name="test-validation",
            enabled=bool(api_key)
        )
        
        if not logger.enabled:
            print("⚠️  EvaluationLogger disabled (no API key)")
            return False
        
        # Create mock workflow result
        mock_result = WorkflowResult(
            success=True,
            final_transcript_path="/test/transcript.md",
            quality_summary_path="/test/quality.json",
            research_notes={"test_module": "test content"},
            chapter_drafts=[
                ChapterDraft(section_id="test_section", content="test chapter content")
            ],
            execution_time=45.2,
            errors=None,
            quality_metrics={
                "quality_score": 0.85,
                "critical_issues": 0,
                "warning_issues": 2,
                "recommendations": ["test recommendation"]
            }
        )
        
        # Test metrics collection
        metrics = await logger.collect_metrics(
            workflow_result=mock_result,
            syllabus={"title": "Test Course", "sections": []},
            execution_metadata={"test": True}
        )
        
        print("✅ EvaluationLogger metrics collection working")
        print(f"   Collected {len(metrics)} metric categories")
        
        # Test agent interaction logging
        logger.log_agent_interaction(
            agent_name="test_agent",
            interaction_type="validation",
            input_data={"test": "input"},
            output_data={"test": "output"},
            metadata={"validation": True}
        )
        
        print("✅ Agent interaction logging working")
        return True
        
    except Exception as e:
        print(f"❌ EvaluationLogger test failed: {e}")
        return False


async def validate_langsmith_integration(api_key: str | None = None, project: str = "story-ops"):
    """Test LangSmithIntegration functionality"""
    print(f"\n🔗 Testing LangSmithIntegration (project: {project})...")
    
    try:
        integration = LangSmithIntegration(
            project_name=project,
            api_key=api_key,
            auto_send_enabled=bool(api_key)
        )
        
        if not integration.enabled:
            print("⚠️  LangSmithIntegration disabled (no API key)")
            return False
        
        # Test configuration
        agent_config = integration.configure_agent_sdk_tracing()
        print(f"✅ Agent SDK tracing configured: {agent_config['enabled']}")
        
        # Test status reporting
        status = integration.get_integration_status()
        print(f"✅ Integration status: {status['enabled']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangSmithIntegration test failed: {e}")
        return False


def validate_configuration():
    """Validate LangSmith configuration"""
    print("\n⚙️  Validating LangSmith configuration...")
    
    try:
        # Test environment validation
        env_result = validate_environment()
        
        print(f"Configuration valid: {env_result['valid']}")
        print(f"Fully configured: {env_result['fully_configured']}")
        
        if env_result['warnings']:
            print("⚠️  Warnings:")
            for warning in env_result['warnings']:
                print(f"   - {warning}")
        
        if env_result['recommendations']:
            print("💡 Recommendations:")
            for rec in env_result['recommendations']:
                print(f"   - {rec}")
        
        # Test config creation
        config = LangSmithConfig.from_environment()
        print(f"✅ Config loaded: project='{config.project_name}'")
        
        return env_result['valid']
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def print_setup_instructions():
    """Print setup instructions for LangSmith"""
    print("\n📋 LangSmith Setup Instructions:")
    print("=" * 50)
    print("1. Get LangSmith API Key:")
    print("   - Visit: https://smith.langchain.com/")
    print("   - Sign up/Login to your account")
    print("   - Go to Settings > API Keys")
    print("   - Create a new API key")
    print()
    print("2. Set Environment Variables:")
    print("   export LANGSMITH_API_KEY='your_api_key_here'")
    print("   export LANGSMITH_PROJECT='story-ops'  # or your preferred project name")
    print()
    print("3. Install Dependencies:")
    print("   poetry install  # or pip install langsmith")
    print()
    print("4. Test Integration:")
    print("   python scripts/validate_langsmith.py")
    print()
    print("5. Environment File Example:")
    print("   Copy .env.example to .env and fill in your values")


async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate LangSmith integration")
    parser.add_argument("--api-key", help="LangSmith API key (overrides environment)")
    parser.add_argument("--project", default="story-ops", help="LangSmith project name")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    
    args = parser.parse_args()
    
    if args.setup:
        print_setup_instructions()
        return
    
    print("🔍 LangSmith Integration Validation")
    print("=" * 40)
    
    # Use provided API key or environment
    api_key = args.api_key or os.getenv('LANGSMITH_API_KEY')
    
    if not api_key:
        print("⚠️  No LangSmith API key found")
        print("Set LANGSMITH_API_KEY environment variable or use --api-key")
        print("Run with --setup for detailed instructions")
        print()
    
    # Run validation tests
    config_valid = validate_configuration()
    logger_valid = await validate_evaluation_logger(api_key)
    integration_valid = await validate_langsmith_integration(api_key, args.project)
    
    # Summary
    print("\n📊 Validation Summary:")
    print("=" * 25)
    print(f"Configuration: {'✅ Valid' if config_valid else '❌ Invalid'}")
    print(f"EvaluationLogger: {'✅ Working' if logger_valid else '⚠️ Limited (no API key)' if not api_key else '❌ Failed'}")
    print(f"LangSmithIntegration: {'✅ Working' if integration_valid else '⚠️ Limited (no API key)' if not api_key else '❌ Failed'}")
    
    if api_key:
        if config_valid and logger_valid and integration_valid:
            print("\n🎉 LangSmith integration is fully configured and working!")
        else:
            print("\n❌ Some issues found. Check the output above for details.")
            sys.exit(1)
    else:
        print("\n💡 LangSmith integration is ready but needs API key to be fully functional.")
        print("Run with --setup for configuration instructions.")


if __name__ == "__main__":
    asyncio.run(main())